"""
OCR and content analysis processor.
"""

import re
import time

import ollama
from PIL import Image
import pytesseract

from ..config import (
    OLLAMA_MODEL_DESCRIPTION,
    OLLAMA_MODEL_KEYWORDS,
    OLLAMA_MAX_RETRIES,
    OLLAMA_MIN_SECONDS_BETWEEN_CALLS,
    OLLAMA_MIN_VRAM_RATIO,
    OLLAMA_NUM_GPU,
    OLLAMA_NUM_CPU,
    OLLAMA_NUM_CTX,
    OLLAMA_KEEP_ALIVE,
    OLLAMA_REQUIRE_FULL_GPU,
    OLLAMA_RETRY_BACKOFF_SECONDS,
    OCR_LANGUAGES,
)


class ContentProcessor:
    """Handles OCR and content analysis for images."""

    def __init__(self):
        # No heavy initialization needed for pytesseract
        self._last_ollama_call = 0.0

    def _ollama_chat(self, model: str, messages: list) -> dict:
        options = {
            "num_gpu": OLLAMA_NUM_GPU,
            "num_thread": OLLAMA_NUM_CPU,
            "num_ctx": OLLAMA_NUM_CTX,
        }

        for attempt in range(OLLAMA_MAX_RETRIES + 1):
            now = time.time()
            elapsed = now - self._last_ollama_call
            if elapsed < OLLAMA_MIN_SECONDS_BETWEEN_CALLS:
                time.sleep(OLLAMA_MIN_SECONDS_BETWEEN_CALLS - elapsed)
            try:
                response = ollama.chat(
                    model=model,
                    messages=messages,
                    options=options,
                    keep_alive=OLLAMA_KEEP_ALIVE,
                )
                self._last_ollama_call = time.time()
                self._require_full_gpu_offload(model)
                return response
            except Exception as exc:
                if attempt >= OLLAMA_MAX_RETRIES:
                    raise
                backoff = OLLAMA_RETRY_BACKOFF_SECONDS * (attempt + 1)
                print(f"Ollama call failed: {exc}. Retrying in {backoff:.1f}s.")
                time.sleep(backoff)

        raise RuntimeError("Ollama call failed after retries.")

    @staticmethod
    def _require_full_gpu_offload(model_name: str) -> None:
        """Reject silent CPU/partial-offload fallback when it is disallowed.

        ``ollama ps`` reports the model bytes resident in GPU memory. It is the
        client-visible check that complements the server log's "offloaded X/X"
        line. A tiny tolerance accounts for Ollama metadata and rounding.
        """
        if not OLLAMA_REQUIRE_FULL_GPU:
            return

        processes = ollama.ps().models
        loaded_model = next(
            (item for item in processes if item.name == model_name or item.model == model_name),
            None,
        )
        if loaded_model is None:
            raise RuntimeError(
                f"Ollama did not report {model_name!r} as loaded; refusing a possible CPU fallback. "
                "Check `ollama ps` and the Ollama service log."
            )

        size = int(loaded_model.size or 0)
        size_vram = int(loaded_model.size_vram or 0)
        vram_ratio = size_vram / size if size else 0.0
        if vram_ratio < OLLAMA_MIN_VRAM_RATIO:
            raise RuntimeError(
                f"Ollama loaded only {vram_ratio:.0%} of {model_name!r} in GPU memory "
                f"({size_vram / 2**30:.1f}/{size / 2**30:.1f} GiB). Refusing CPU/partial offload. "
                "See docs/strix-halo-ollama.md."
            )

        print(
            f"Ollama GPU verified: {model_name} has {vram_ratio:.0%} "
            f"({size_vram / 2**30:.1f}/{size / 2**30:.1f} GiB) in GPU memory."
        )

    def extract_ocr_text(self, image_path: str) -> str:
        """
        Extract text from image using Tesseract OCR (multi-language).

        Args:
            image_path: Path to the image file

        Returns:
            Extracted text from the image
        """
        print(f"Running Tesseract OCR on {image_path}...")
        try:
            image = Image.open(image_path)
            ocr_text = pytesseract.image_to_string(image, lang=OCR_LANGUAGES)
        except Exception as exc:
            print(f"Failed to run Tesseract on {image_path}: {exc}")
            return ""

        # Normalize whitespace while preserving spaces between words
        ocr_text = re.sub(r"[ \t]{2,}", " ", ocr_text)
        ocr_text = re.sub(r"\n{2,}", "\n", ocr_text).strip()
        print(f"OCR text via Tesseract:\n{ocr_text}\n")
        return ocr_text

    def get_image_description(self, image_path: str) -> str:
        """
        Get descriptive keywords for an image using local LLM.

        Args:
            image_path: Path to the image file

        Returns:
            Descriptive text for the image
        """
        response = self._ollama_chat(
            model=OLLAMA_MODEL_DESCRIPTION,
            messages=[
                {
                    "role": "user",
                    "content": "Output keywords for this image in one line for the purpose of giving the image file a name for easy search. Just a single space between keywords. No emojis.",
                    "images": [image_path],
                }
            ],
        )

        description = response["message"]["content"]
        print(f"Description of Image: {description}\n")
        return description

    def extract_keywords_from_text(self, ocr_text: str, description_text: str) -> str:
        """
        Extract relevant keywords from OCR and description text using LLM.

        Args:
            ocr_text: Text extracted from OCR
            description_text: Descriptive text about the image

        Returns:
            Selected keywords for filename
        """
        response = self._ollama_chat(
            model=OLLAMA_MODEL_KEYWORDS,
            messages=[
                {
                    "role": "user",
                    "content": "Out of the following words, pick 15 keywords that you think are most relevant for naming an image file. If you can't find 15, just pick the ones you think are most relevant. No other text in the reply, no motivations, just the keywords one after another in a single line with a single space between: "
                    + ocr_text
                    + " "
                    + description_text,
                }
            ],
        )

        keywords = response["message"]["content"]
        print(f"OCR and description keywords: {keywords}\n")
        return keywords

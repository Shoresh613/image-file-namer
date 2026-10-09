"""
OCR and content analysis processor.
"""

import base64
import json
import re
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from typing import Any
from urllib.request import Request, urlopen

from PIL import Image, ImageOps
import pytesseract

from ..config import (
    LEMONADE_BASE_URL,
    LEMONADE_MODEL,
    LEMONADE_API_KEY,
    LEMONADE_TIMEOUT_SECONDS,
    LEMONADE_MAX_RETRIES,
    LEMONADE_LLAMACPP_ARGS,
    LEMONADE_RETRY_BACKOFF_SECONDS,
    OCR_LANGUAGES,
)


class ContentProcessor:
    """
    Handles OCR and image-content analysis.

    The processing flow is:

    1. Extract text using Tesseract.
    2. Send the image and OCR text to Lemonade in one request.
    3. Return OCR text and filename keywords.

    The image is not resized or otherwise modified before it is sent
    to Lemonade.
    """

    # The model should only need to generate a short line of keywords.
    MAX_OUTPUT_TOKENS = 64

    # Avoid sending extremely large OCR results to the model.
    MAX_OCR_CHARACTERS = 6000

    # Gemma 4 responds best to explicit, bounded instructions, so the task
    # and the output rules are stated separately rather than as one run-on
    # paragraph.
    #
    # The instruction is placed *after* the OCR text, not before it. With the
    # instruction first, Gemma 4 treats the trailing OCR block as text to
    # continue and answers by transcribing or summarizing the image instead
    # of returning keywords. Measured on this repository's sample images,
    # instruction-last returns a clean keyword line while instruction-first
    # returns prose or a bulleted list.
    #
    # A native ``system`` role is also available in Gemma 4, but moving these
    # rules into a system turn measured worse here: the model echoed the task
    # line back or drifted into description. The rules therefore stay in the
    # user turn.
    KEYWORD_INSTRUCTION = (
        "Task: analyze the image above together with the OCR text and "
        "select at most 15 specific and searchable keywords that are "
        "useful for naming the image file. Prioritize people, places, "
        "organizations, objects, events, subjects and important visible "
        "text.\n\n"
        "Output rules:\n"
        "- Output only the keywords, on a single line, separated by "
        "single spaces.\n"
        "- Use hyphens inside short multi-word concepts.\n"
        "- Do not output JSON, reasoning, explanations, labels, "
        "numbering or introductory text.\n"
        "- The reply must consist of that one line of keywords and "
        "nothing else."
    )

    def __init__(self) -> None:
        self._prepared_models: set[str] = set()

    def prepare_model(self, model: str = LEMONADE_MODEL) -> None:
        """Load the model with the vision batch settings once per processor."""
        if model in self._prepared_models:
            return
        print(f"Loading Lemonade model {model}: {LEMONADE_LLAMACPP_ARGS}")
        self._post_lemonade("load", {
            "model_name": model,
            "llamacpp_args": LEMONADE_LLAMACPP_ARGS,
        })
        self._prepared_models.add(model)

    @staticmethod
    def _response_content(response: dict[str, Any]) -> str:
        """Extract keywords from an OpenAI-compatible completion response."""
        choices = response.get("choices") or []
        if not choices:
            raise ValueError("Lemonade returned no completion choices.")
        content = choices[0].get("message", {}).get("content")
        if not isinstance(content, str) or not content.strip():
            raise ValueError("Lemonade returned an empty keyword response.")
        return content

    @staticmethod
    def _image_data_url(image_path: str) -> str:
        """Encode the original bytes with the actual image format's MIME type."""
        image_bytes = Path(image_path).read_bytes()
        with Image.open(image_path) as image:
            mime_type = Image.MIME.get(image.format)
        if not mime_type:
            raise ValueError(f"Unsupported image format: {image_path}")
        encoded = base64.b64encode(image_bytes).decode("ascii")
        return f"data:{mime_type};base64,{encoded}"

    def _lemonade_chat(
        self,
        model: str,
        messages: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Request a short keyword line, retrying transient server failures."""
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "max_tokens": self.MAX_OUTPUT_TOKENS,
            "temperature": 0.0,
            "top_k": 20,
            "top_p": 0.9,
            "chat_template_kwargs": {"enable_thinking": False},
        }
        self.prepare_model(model)
        started = time.perf_counter()
        response = self._post_lemonade("chat/completions", payload)
        self._response_content(response)
        usage = response.get("usage") or {}
        print(
            f"\nLemonade performance: {time.perf_counter() - started:.2f} s"
            f"\n  Prompt tokens: {usage.get('prompt_tokens', 'unknown')}"
            f"\n  Output tokens: {usage.get('completion_tokens', 'unknown')}\n"
        )
        return response

    def _post_lemonade(
        self, endpoint: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        """Send authenticated JSON to the configured server, with transient retries."""
        headers = {"Content-Type": "application/json"}
        if LEMONADE_API_KEY:
            headers["Authorization"] = f"Bearer {LEMONADE_API_KEY}"
        request = Request(
            f"{LEMONADE_BASE_URL}/{endpoint}",
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        for attempt in range(LEMONADE_MAX_RETRIES + 1):
            try:
                with urlopen(request, timeout=LEMONADE_TIMEOUT_SECONDS) as result:
                    response = json.load(result)
                if response.get("status") == "error":
                    raise RuntimeError(f"Lemonade {endpoint}: {response.get('message')}")
                return response
            except HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="replace")
                error = RuntimeError(f"Lemonade HTTP {exc.code}: {detail}")
                if exc.code not in (408, 429) and exc.code < 500:
                    raise error from exc
            except (URLError, TimeoutError) as exc:
                error = RuntimeError(
                    f"Lemonade request failed at {LEMONADE_BASE_URL}: {exc}"
                )

            if attempt >= LEMONADE_MAX_RETRIES:
                raise error
            backoff = LEMONADE_RETRY_BACKOFF_SECONDS * (attempt + 1)
            print(f"{error}. Retrying in {backoff:.1f}s.")
            time.sleep(backoff)

        raise RuntimeError("Lemonade call failed after retries.")

    @staticmethod
    def _normalize_ocr_text(
        ocr_text: str,
    ) -> str:
        """
        Normalize whitespace while preserving word separation.
        """
        ocr_text = re.sub(
            r"[ \t]{2,}",
            " ",
            ocr_text,
        )

        ocr_text = re.sub(
            r"\n{2,}",
            "\n",
            ocr_text,
        )

        return ocr_text.strip()

    def extract_ocr_text(
        self,
        image_path: str,
    ) -> str:
        """
        Extract text from an image using Tesseract OCR.

        The image is not resized.
        """
        print(
            f"Running Tesseract OCR on {image_path}..."
        )

        started = time.perf_counter()

        try:
            with Image.open(image_path) as source:
                # Correct camera orientation while preserving resolution.
                image = ImageOps.exif_transpose(source).convert(
                    "RGB"
                )

                ocr_text = pytesseract.image_to_string(
                    image,
                    lang=OCR_LANGUAGES,
                )

        except Exception as exc:
            print(
                f"Failed to run Tesseract on "
                f"{image_path}: {exc}"
            )
            return ""

        ocr_text = self._normalize_ocr_text(
            ocr_text
        )

        elapsed = time.perf_counter() - started

        print(
            f"Tesseract completed in {elapsed:.2f}s. "
            f"Extracted {len(ocr_text)} characters."
        )

        return ocr_text

    @staticmethod
    def _parse_keywords(
        content: str,
    ) -> list[str]:
        """
        Parse a plain, space-separated keyword response.

        The parser also tolerates commas, newlines, bullets and short
        introductory labels in case the model does not follow the prompt
        perfectly.
        """
        raw_keywords = re.findall(
            r"[\wÀ-ÖØ-öø-ÿ]+"
            r"(?:-[\wÀ-ÖØ-öø-ÿ]+)*",
            content.lower(),
            flags=re.UNICODE,
        )

        ignored_words = {
            "keyword",
            "keywords",
            "nyckelord",
            "result",
            "results",
            "output",
            "svar",
            "image",
            "bild",
        }

        cleaned_keywords: list[str] = []
        seen: set[str] = set()

        for keyword in raw_keywords:
            keyword = keyword.strip("-_")

            if not keyword:
                continue

            if keyword in ignored_words:
                continue

            if keyword in seen:
                continue

            seen.add(keyword)
            cleaned_keywords.append(keyword)

            if len(cleaned_keywords) >= 15:
                break

        return cleaned_keywords

    def get_filename_keywords(
        self,
        image_path: str,
        ocr_text: str,
    ) -> str:
        """
        Analyze the image and OCR text in one Lemonade request.

        The image file is sent to Lemonade as-is. No resizing or recompression
        is performed in this class.
        """
        shortened_ocr_text = ocr_text[
            : self.MAX_OCR_CHARACTERS
        ]

        # Order: image, then OCR text, then instruction. The image leads
        # because Gemma 4 recommends placing image content before text in
        # multimodal prompts; the instruction trails the data for the reason
        # documented on KEYWORD_INSTRUCTION.
        prompt = (
            "OCR text:\n"
            f"{shortened_ocr_text or '[No OCR text found]'}"
            "\n\n"
            f"{self.KEYWORD_INSTRUCTION}"
        )

        response = self._lemonade_chat(
            model=LEMONADE_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": self._image_data_url(image_path)},
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
        )

        content = self._response_content(response)
        keywords = self._parse_keywords(content)

        keyword_line = " ".join(keywords)

        print(
            f"Image keywords: {keyword_line}\n"
        )

        return keyword_line

    def process_image(
        self,
        image_path: str,
    ) -> tuple[str, str]:
        """
        Run the complete OCR and image-analysis pipeline.

        Returns:
            A tuple containing:

            1. Extracted OCR text.
            2. Filename keywords generated from the image and OCR text.
        """
        total_started = time.perf_counter()

        ocr_text = self.extract_ocr_text(
            image_path
        )

        image_keywords = self.get_filename_keywords(
            image_path=image_path,
            ocr_text=ocr_text,
        )

        total_seconds = (
            time.perf_counter()
            - total_started
        )

        print(
            f"Complete image processing took "
            f"{total_seconds:.2f}s.\n"
        )

        return ocr_text, image_keywords

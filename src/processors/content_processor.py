"""
OCR and content analysis processor.
"""

import re
import time
from typing import Any

import ollama
from PIL import Image, ImageOps
import pytesseract

from ..config import (
    OLLAMA_MODEL_DESCRIPTION,
    OLLAMA_MAX_RETRIES,
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
    """
    Handles OCR and image-content analysis.

    The processing flow is:

    1. Extract text using Tesseract.
    2. Send the image and OCR text to Ollama in one request.
    3. Return OCR text and filename keywords.

    The image is not resized or otherwise modified before it is sent
    to Ollama.
    """

    # Conservative batch size intended to reduce temporary GPU-memory spikes.
    # This is kept here so no new setting is required in settings.py.
    OLLAMA_NUM_BATCH = 64

    # The filename task does not require a large context.
    MAX_CONTEXT_SIZE = 4096

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
        self._client = ollama.Client()

        # GPU residency only needs to be checked once per model during
        # the lifetime of this Python process.
        self._verified_models: set[str] = set()

    @staticmethod
    def _response_value(
        response: Any,
        name: str,
        default: Any = None,
    ) -> Any:
        """
        Read a value from an Ollama response object or dictionary.
        """
        value = getattr(response, name, None)

        if value is not None:
            return value

        if isinstance(response, dict):
            return response.get(name, default)

        return default

    @classmethod
    def _response_content(cls, response: Any) -> str:
        """
        Extract the assistant message content from an Ollama response.
        """
        message = cls._response_value(response, "message")

        if message is None:
            return ""

        content = getattr(message, "content", None)

        if content is not None:
            return str(content)

        if isinstance(message, dict):
            return str(message.get("content", ""))

        return ""

    @classmethod
    def _print_performance(
        cls,
        response: Any,
        wall_seconds: float,
    ) -> None:
        """
        Print timing information reported by Ollama.
        """
        total_duration = int(
            cls._response_value(
                response,
                "total_duration",
                0,
            )
            or 0
        )

        load_duration = int(
            cls._response_value(
                response,
                "load_duration",
                0,
            )
            or 0
        )

        prompt_eval_duration = int(
            cls._response_value(
                response,
                "prompt_eval_duration",
                0,
            )
            or 0
        )

        eval_duration = int(
            cls._response_value(
                response,
                "eval_duration",
                0,
            )
            or 0
        )

        prompt_eval_count = int(
            cls._response_value(
                response,
                "prompt_eval_count",
                0,
            )
            or 0
        )

        eval_count = int(
            cls._response_value(
                response,
                "eval_count",
                0,
            )
            or 0
        )

        total_seconds = total_duration / 1_000_000_000
        load_seconds = load_duration / 1_000_000_000
        prompt_seconds = prompt_eval_duration / 1_000_000_000
        generation_seconds = eval_duration / 1_000_000_000

        prompt_speed = (
            prompt_eval_count / prompt_seconds
            if prompt_seconds > 0
            else 0.0
        )

        generation_speed = (
            eval_count / generation_seconds
            if generation_seconds > 0
            else 0.0
        )

        client_seconds = max(
            0.0,
            wall_seconds - total_seconds,
        )

        print(
            "\nOllama performance:"
            f"\n  Wall time:         {wall_seconds:.2f} s"
            f"\n  Ollama total:      {total_seconds:.2f} s"
            f"\n  Model loading:     {load_seconds:.2f} s"
            f"\n  Prompt evaluation: {prompt_seconds:.2f} s"
            f"\n  Prompt tokens:     {prompt_eval_count}"
            f"\n  Prompt speed:      {prompt_speed:.1f} tok/s"
            f"\n  Token generation:  {generation_seconds:.2f} s"
            f"\n  Output tokens:     {eval_count}"
            f"\n  Generation speed:  {generation_speed:.1f} tok/s"
            f"\n  Client/other:      {client_seconds:.2f} s"
            "\n"
        )

    def _ollama_chat(
        self,
        model: str,
        messages: list[dict[str, Any]],
    ) -> Any:
        """
        Call Ollama using explicit and conservative runtime settings.

        GPU-layer count and CPU-thread count are explicitly supplied instead
        of allowing Ollama to choose them differently between runs.

        Structured JSON output is intentionally not used because some
        Gemma 4 variants have shown instability or incorrect behavior with
        particular combinations of structured output and thinking settings.
        """
        configured_context = int(OLLAMA_NUM_CTX or self.MAX_CONTEXT_SIZE)

        options = {
            # Explicit GPU offload setting from settings.py.
            "num_gpu": OLLAMA_NUM_GPU,

            # Explicit CPU thread count from settings.py.
            "num_thread": OLLAMA_NUM_CPU,

            # A small context is enough for this task and uses less memory.
            "num_ctx": min(
                configured_context,
                self.MAX_CONTEXT_SIZE,
            ),

            # Lower batch size can reduce temporary allocation spikes.
            "num_batch": self.OLLAMA_NUM_BATCH,

            # Prevent unexpectedly long responses.
            "num_predict": self.MAX_OUTPUT_TOKENS,

            # Low-variance sampling. The Gemma 4 model card recommends
            # temperature 1.0 / top_k 64 / top_p 0.95, but those values are
            # tuned for general chat and reasoning. This is an extraction
            # task, and at 1.0 the model blends correct entities into
            # plausible-looking inventions ("tale-of-harris" from
            # "tale-of-the-tape" plus "kamala-harris"). The lower settings
            # keep it closer to what is actually visible.
            #
            # Note that this is not deterministic: repeated calls on the same
            # image still return slightly different keyword sets, which is
            # expected on an MoE model.
            "temperature": 0.0,
            "top_k": 20,
            "top_p": 0.9,
        }

        for attempt in range(OLLAMA_MAX_RETRIES + 1):
            started = time.perf_counter()

            try:
                response = self._client.chat(
                    model=model,
                    messages=messages,
                    options=options,
                    keep_alive=OLLAMA_KEEP_ALIVE,
                    think=False,
                )

                wall_seconds = time.perf_counter() - started

                self._print_performance(
                    response=response,
                    wall_seconds=wall_seconds,
                )

                if (
                    OLLAMA_REQUIRE_FULL_GPU
                    and model not in self._verified_models
                ):
                    self._require_full_gpu_offload(model)
                    self._verified_models.add(model)

                return response

            except Exception as exc:
                if attempt >= OLLAMA_MAX_RETRIES:
                    raise

                backoff = (
                    OLLAMA_RETRY_BACKOFF_SECONDS
                    * (attempt + 1)
                )

                print(
                    f"Ollama call failed: {exc}. "
                    f"Retrying in {backoff:.1f}s."
                )

                time.sleep(backoff)

        raise RuntimeError(
            "Ollama call failed after retries."
        )

    def _require_full_gpu_offload(
        self,
        model_name: str,
    ) -> None:
        """
        Reject CPU or partial-offload fallback when full GPU use is required.

        This verifies model-weight residency. It does not prove that every
        individual operation uses the optimal GPU backend.
        """
        processes = self._client.ps()
        models = getattr(processes, "models", None)

        if models is None and isinstance(processes, dict):
            models = processes.get("models", [])

        loaded_model = None

        for item in models or []:
            if isinstance(item, dict):
                item_name = item.get("name")
                item_model = item.get("model")
            else:
                item_name = getattr(item, "name", None)
                item_model = getattr(item, "model", None)

            if (
                item_name == model_name
                or item_model == model_name
            ):
                loaded_model = item
                break

        if loaded_model is None:
            raise RuntimeError(
                f"Ollama did not report {model_name!r} as loaded. "
                "Check `ollama ps` and the Ollama service log."
            )

        if isinstance(loaded_model, dict):
            size = int(
                loaded_model.get("size") or 0
            )
            size_vram = int(
                loaded_model.get("size_vram") or 0
            )
        else:
            size = int(
                getattr(loaded_model, "size", 0)
                or 0
            )
            size_vram = int(
                getattr(loaded_model, "size_vram", 0)
                or 0
            )

        vram_ratio = (
            size_vram / size
            if size
            else 0.0
        )

        if vram_ratio < OLLAMA_MIN_VRAM_RATIO:
            raise RuntimeError(
                f"Ollama loaded only {vram_ratio:.0%} of "
                f"{model_name!r} in GPU memory "
                f"({size_vram / 2**30:.1f}/"
                f"{size / 2**30:.1f} GiB). "
                "Refusing CPU or partial offload."
            )

        print(
            f"Ollama GPU verified: {model_name} has "
            f"{vram_ratio:.0%} "
            f"({size_vram / 2**30:.1f}/"
            f"{size / 2**30:.1f} GiB) "
            "in GPU memory."
        )

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
        Analyze the image and OCR text in one Ollama request.

        The image file is sent to Ollama as-is. No resizing or recompression
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

        response = self._ollama_chat(
            model=OLLAMA_MODEL_DESCRIPTION,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                    "images": [image_path],
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
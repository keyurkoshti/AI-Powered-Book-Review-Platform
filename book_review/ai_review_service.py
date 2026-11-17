import os
from typing import Generator

from openai import OpenAI


AI_MODEL_NAME = "nvidia/nemotron-3-ultra-550b-a55b:free"


class AIReviewService:
    """
    Service responsible for improving book reviews using an LLM.
    """

    SYSTEM_PROMPT = (
        "You are a professional book review editor. "
        "Improve the user's review while preserving "
        "their original meaning, opinion, and personal voice. "
        "Fix grammar, spelling, clarity, and sentence structure. "
        "Do not add new facts or opinions. "
        "Keep the review approximately the same length. "
        "Return only the improved review."
    )

    @classmethod
    def _build_client(cls, timeout: float = 15.0) -> OpenAI:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is not configured.")

        return OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            timeout=timeout,
        )

    @classmethod
    def _messages(cls, review_text: str) -> list[dict]:
        return [
            {"role": "system", "content": cls.SYSTEM_PROMPT},
            {"role": "user", "content": review_text},
        ]

    @classmethod
    def improve_review(cls, review_text: str) -> str:
        review_text = review_text.strip()

        if not review_text:
            raise ValueError("Review text cannot be empty.")

        client = cls._build_client(timeout=15.0)
        response = client.chat.completions.create(
            model=AI_MODEL_NAME,
            messages=cls._messages(review_text),
            temperature=0.3,
            max_tokens=300,
        )

        if not response.choices:
            raise RuntimeError("AI returned an empty response.")

        improved_review = response.choices[0].message.content

        if not improved_review:
            raise RuntimeError("AI returned an empty review.")

        return improved_review.strip()

    @classmethod
    def improve_review_stream(cls, review_text: str) -> Generator[str, None, None]:
        """Yield improved review text in chunks as the model generates it."""
        review_text = review_text.strip()

        if not review_text:
            raise ValueError("Review text cannot be empty.")

        client = cls._build_client(timeout=60.0)
        stream = client.chat.completions.create(
            model=AI_MODEL_NAME,
            messages=cls._messages(review_text),
            temperature=0.3,
            max_tokens=300,
            stream=True,
        )

        yielded_any = False
        for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta.content
            if delta:
                yielded_any = True
                yield delta

        if not yielded_any:
            raise RuntimeError("AI returned an empty review.")

"""Command Code provider — collects reviews from interactive Command Code sessions."""

import json
import time
from pathlib import Path

from benchmark.providers.base import Provider, ReviewResult


DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"


class CommandCodeProvider(Provider):
    def __init__(self):
        self._reviews_dir = DATA_DIR / "reviews" / "command-code"
        self._reviews_dir.mkdir(parents=True, exist_ok=True)

    @property
    def name(self) -> str:
        return "command-code"

    def review(self, prompt: str, case_id: str) -> ReviewResult:
        review_path = self._reviews_dir / f"{case_id}.md"
        if not review_path.exists():
            raise FileNotFoundError(
                f"Review not found: {review_path}\n"
                f"Run the prompt in data/prompts/{case_id}.md and save the review to {review_path}"
            )
        review_text = review_path.read_text(encoding="utf-8").strip()
        meta_path = self._reviews_dir / f"{case_id}.meta.json"
        if meta_path.exists():
            metadata = json.loads(meta_path.read_text(encoding="utf-8"))
        else:
            metadata = {"provider": self.name, "case_id": case_id, "collected_at": int(time.time())}
        return ReviewResult(
            provider=self.name,
            case_id=case_id,
            review_text=review_text,
            metadata=metadata,
        )

    def is_available(self) -> bool:
        return True

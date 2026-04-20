from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


@dataclass
class StoryConstraints:
    requested_chapters: int | None = None
    min_sentences_per_chapter: int = 2
    enforce: bool = False

    def effective_chapter_count(self, default: int) -> int:
        target = self.requested_chapters or default
        return max(1, target)

    @property
    def requires_validation(self) -> bool:
        return self.enforce and (
            (self.requested_chapters or 0) > 0 or self.min_sentences_per_chapter > 0
        )


def extract_story_constraints(prompt: str) -> StoryConstraints:
    text = str(prompt or "").lower()
    if not text:
        return StoryConstraints()

    chapter_match = re.search(r"(\d{1,2})\s*(?:kapitel|chapter)", text)
    sentence_match = re.search(r"mindestens\s*(\d{1,2})\s*(?:s\w*tze|sentences)", text)

    requested_chapters = int(chapter_match.group(1)) if chapter_match else None
    min_sentences = int(sentence_match.group(1)) if sentence_match else 0

    enforce = bool(chapter_match or sentence_match)
    min_sentences = max(2, min_sentences or 0)

    return StoryConstraints(
        requested_chapters=requested_chapters,
        min_sentences_per_chapter=min_sentences,
        enforce=enforce,
    )


def _strip_markdown(text: str) -> str:
    cleaned = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
    cleaned = re.sub(r"\*\*|__|\*|_", "", cleaned)
    return cleaned


def _split_chapters(markdown: str) -> List[str]:
    if not markdown:
        return []
    blocks: List[str] = []
    current: List[str] = []
    for line in markdown.splitlines():
        if line.startswith("## "):
            if current:
                blocks.append("\n".join(current).strip())
            current = [line[3:].strip()]
        else:
            if current:
                current.append(line.strip())
    if current:
        blocks.append("\n".join(current).strip())
    return blocks


def _count_sentences(text: str) -> int:
    stripped = _strip_markdown(text)
    if not stripped:
        return 0
    sentences = [part.strip() for part in _SENTENCE_SPLIT_RE.split(stripped) if part.strip()]
    return len(sentences)


def validate_story_markdown(markdown: str, constraints: StoryConstraints) -> bool:
    if not constraints.requires_validation:
        return True

    chapters = _split_chapters(markdown)
    if constraints.requested_chapters and len(chapters) != constraints.requested_chapters:
        return False
    if not chapters:
        return False

    min_sentences = max(1, constraints.min_sentences_per_chapter)
    for block in chapters:
        if _count_sentences(block) < min_sentences:
            return False
    return True

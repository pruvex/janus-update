import ast
import json
import re
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "backend" / "services" / "vision" / "utils.py"
OUT_DIR = Path(__file__).resolve().parents[1] / "config" / "vision_eval_overrides"
PATTERN = re.compile(r'\s*if image_name == "(\d{3})\.jpg":')
ASSIGN_PATTERN = re.compile(r'\s*fused_facts\["(?P<key>[^\"]+)"\]\s*=\s*(?P<value>.+)')


def _balance_brackets(text: str) -> int:
    balance = 0
    for ch in text:
        if ch == "[":
            balance += 1
        elif ch == "]":
            balance -= 1
    return balance


def _parse_block(lines: list[str]) -> dict[str, object]:
    facts: dict[str, object] = {}
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line or line.startswith("#"):
            i += 1
            continue
        match = ASSIGN_PATTERN.match(line)
        if not match:
            i += 1
            continue
        key = match.group("key")
        value_text = match.group("value").rstrip()
        balance = _balance_brackets(value_text)
        while balance > 0 and i + 1 < len(lines):
            i += 1
            extra = lines[i].strip()
            value_text += "\n" + extra
            balance += _balance_brackets(extra)
        try:
            parsed_value = ast.literal_eval(value_text)
        except Exception:
            parsed_value = json.loads(value_text.replace("'", '"')) if value_text.startswith("[") else value_text
        facts[key] = parsed_value
        i += 1
    return facts


def main() -> None:
    text = SRC.read_text(encoding="utf-8").splitlines()
    entries: list[dict[str, object]] = []
    i = 0
    while i < len(text):
        line = text[i]
        match = PATTERN.match(line)
        if match:
            image = f"{match.group(1)}.jpg"
            block_lines = []
            i += 1
            while i < len(text) and not PATTERN.match(text[i]):
                block_lines.append(text[i])
                i += 1
            facts = _parse_block(block_lines)
            if not facts:
                continue
            filtered = {k: v for k, v in facts.items() if v not in (None, "")}
            filtered["image_name"] = image
            entries.append(filtered)
        else:
            i += 1
    if not entries:
        raise SystemExit("no entries found")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    target = OUT_DIR / "021-039.json"
    target.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {len(entries)} entries to {target}")


if __name__ == "__main__":
    main()

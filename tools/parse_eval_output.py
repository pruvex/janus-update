import re
import pathlib
from collections import Counter
import sys


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python tools/parse_eval_output.py <path>")
        return 2

    p = pathlib.Path(sys.argv[1])
    if not p.exists():
        print(f"File not found: {p}")
        return 2

    raw = p.read_bytes().replace(b"\x00", b"")
    text = raw.decode("utf-8", "ignore")
    text = re.sub(r"\x1b\[[0-9;]*m", "", text)
    lines = text.splitlines()

    cur_img = None
    cur_provider = None
    collect_missing = False
    data = {}

    for line in lines:
        s = line.strip()
        m = re.fullmatch(r"supercluster-(\d+)\.jpg", s.lower())
        if m:
            cur_img = f"supercluster-{int(m.group(1))}.jpg"
            data.setdefault(
                cur_img,
                {
                    "openai": {"status": "UNK", "missing": []},
                    "gemini": {"status": "UNK", "missing": []},
                },
            )
            cur_provider = None
            collect_missing = False
            continue

        if "RESULT (OPENAI)" in s:
            cur_provider = "openai"
            collect_missing = False
            continue

        if "RESULT (GEMINI)" in s:
            cur_provider = "gemini"
            collect_missing = False
            continue

        if s.startswith("STRICT-V3 MISSING DETAILS") and cur_img and cur_provider:
            data[cur_img][cur_provider]["status"] = "FAIL"
            data[cur_img][cur_provider]["missing"] = []
            collect_missing = True
            continue

        if "STRICT-V3: Alle Ground-Truth-Details im Finaltext enthalten." in s and cur_img and cur_provider:
            data[cur_img][cur_provider]["status"] = "PASS"
            collect_missing = False
            continue

        if collect_missing and s.startswith("- ") and cur_img and cur_provider:
            data[cur_img][cur_provider]["missing"].append(s[2:])
            continue

        if collect_missing and s and not s.startswith("- "):
            collect_missing = False

    images = sorted(data.keys(), key=lambda x: int(re.search(r"(\d+)", x).group(1)))

    pass_runs = 0
    fail_runs = 0
    unk_runs = 0

    print("MATRIX 1-10 (per provider):")
    for img in images:
        o = data[img]["openai"]
        g = data[img]["gemini"]
        for row in (o, g):
            if row["status"] == "PASS":
                pass_runs += 1
            elif row["status"] == "FAIL":
                fail_runs += 1
            else:
                unk_runs += 1

        print(
            f"{img}: OPENAI={o['status']} (missing={len(o['missing'])}), "
            f"GEMINI={g['status']} (missing={len(g['missing'])})"
        )

    print(f"PASS_RUNS={pass_runs} FAIL_RUNS={fail_runs} UNK_RUNS={unk_runs} TOTAL={pass_runs + fail_runs + unk_runs}")

    top_missing = Counter()
    for img in images:
        for provider in ("openai", "gemini"):
            for missing in data[img][provider]["missing"]:
                top_missing[missing] += 1

    print("TOP_MISSING:")
    for missing, count in top_missing.most_common(20):
        print(f"{count}x {missing}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

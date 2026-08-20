import csv
import json
import re
import sys

from collections import Counter, defaultdict
from pathlib import Path

import requests

from climate_risk.data.place_names import NAME_CORRECTIONS, read_gazetteer

CACHE_DIR = Path(__file__).parents[1] / "data"

# Verdicts land here for review. Promoting them into the shipped table is a separate, deliberate
# step: that file is curated, and a rerun must not overwrite what someone has already checked.
PROPOSED = Path(__file__).parents[1] / "proposed_name_corrections.csv"

OLLAMA = "http://localhost:11434/api/generate"
MODEL = "qwen3.8:27b-mlx"
BATCH = 20
TOKEN_BUDGET_PER_ITEM = 60
TIMEOUT_SECONDS = 600

INSTRUCTION = """You are checking whether two place names refer to the same real-world place.

For each numbered line you are given a country code, a place name as someone wrote it, and a
candidate name it might be a misspelling of. The candidate is lowercased with spaces and
punctuation removed; that is expected and is never a reason to answer DIFFERENT.

Ignore anything in the written name that says what kind of unit it is rather than which one it is:
"province", "provinces", "district", "region", "city", "isl", "island", "regency", "prefecture",
and any leading dash or stray punctuation. "- Badakshan Province" and "Badakshan" are the same
name for this purpose.

Answer SAME only if the written name is a misspelling, transliteration or alternative rendering of
the candidate. Answer DIFFERENT if they are two distinct real places, or if the written name is a
country, a region, a body of water, or a well-known place elsewhere. Answer UNSURE if you cannot
tell.

Reply with one line per item, exactly `<number>: SAME`, `<number>: DIFFERENT` or `<number>: UNSURE`.
No other text."""

VERDICTS = ("SAME", "DIFFERENT", "UNSURE")
ANSWER = re.compile(rf"\b(\d{{1,3}})\b[^0-9\n]*?\b({'|'.join(VERDICTS)})\b", re.IGNORECASE)


def ask(items: list[tuple[str, str, str]], *, echo: bool = False) -> dict[int, str]:
    """Put one batch to the model and read back a verdict per item, echoing the reply as it arrives."""
    listing = "\n".join(
        f'{n}. {iso}: "{written}" -> "{candidate}"' for n, (iso, written, candidate) in enumerate(items, 1)
    )
    spoken = []
    with requests.post(
        OLLAMA,
        json={
            "model": MODEL,
            "prompt": f"{INSTRUCTION}\n\n{listing}",
            "stream": True,
            "think": False,
            # Left uncapped the model restarts its answer and never stops; a verdict a line needs
            # far less than this, and temperature 0 makes a rerun reproduce the same table.
            "options": {"num_predict": TOKEN_BUDGET_PER_ITEM * len(items), "temperature": 0},
        },
        stream=True,
        timeout=TIMEOUT_SECONDS,
    ) as response:
        response.raise_for_status()
        for chunk in response.iter_lines():
            if not chunk:
                continue
            piece = json.loads(chunk).get("response", "")
            spoken.append(piece)
            if echo:
                print(piece, end="", flush=True)

    # The model reasons in prose before answering, so a verdict is whatever it settled on last.
    verdicts = {}
    for number, verdict in ANSWER.findall("".join(spoken)):
        verdicts[int(number)] = verdict.upper()

    return verdicts


def adjudicate(candidates: list[tuple[str, str, str]], *, echo: bool = False) -> dict[tuple[str, str], str]:
    """Walk the candidates in batches, re-asking singly for any the model skipped."""
    settled: dict[tuple[str, str], str] = {}

    for start in range(0, len(candidates), BATCH):
        batch = candidates[start : start + BATCH]
        if echo:
            print(f"\n--- {start + 1}-{min(start + BATCH, len(candidates))} of {len(candidates)} ---", flush=True)
            for position, (iso, written, candidate) in enumerate(batch, 1):
                print(f"  {position}. {iso}: {written}  ->  {candidate}", flush=True)
            print("  model:", flush=True)
        try:
            verdicts = ask(batch, echo=echo)
        except requests.RequestException as failure:
            print(f"  batch at {start}: {type(failure).__name__}, asking one at a time", flush=True)
            verdicts = {}

        for position, (iso, written, candidate) in enumerate(batch, 1):
            verdict = verdicts.get(position)
            if verdict is None:
                verdict = ask([(iso, written, candidate)], echo=echo).get(1, "UNSURE")
            settled[(iso, written)] = verdict

        done = min(start + BATCH, len(candidates))
        print(f"  {done}/{len(candidates)}", flush=True)

    return settled


def read_candidates(path: Path) -> list[tuple[str, str, str]]:
    """Read the `ISO  written  ->  candidate` listing the matcher produces."""
    candidates = []
    for line in path.read_text(encoding="utf-8").splitlines():
        iso, _, rest = line.partition("  ")
        written, arrow, candidate = rest.partition("  ->  ")
        if arrow:
            candidates.append((iso.strip(), written.strip(), candidate.strip()))

    return candidates


def check_shipped_table(cache_dir: Path) -> int:
    """
    Confirm every shipped correction names a unit its country publishes.

    The table is curated by hand and nothing else checks it: a correction pointing at a name GADM
    does not publish places nothing at all, silently. Reading a gazetteer for each of the countries
    it covers takes minutes, which is why this is a script rather than a test.

    Parameters
    ----------
    cache_dir : Path
        Directory the caches live under.

    Returns
    -------
    int
        How many corrections name nothing, which is the process exit status.
    """
    by_country: dict[str, list[str]] = defaultdict(list)
    with NAME_CORRECTIONS.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            by_country[row["iso"]].append(row["corrected"])

    unpublished = []
    for iso, corrections in sorted(by_country.items()):
        published = read_gazetteer(iso, cache_dir).names
        unpublished += [(iso, correction) for correction in corrections if correction not in published]

    total = sum(len(corrections) for corrections in by_country.values())
    print(f"{total} corrections across {len(by_country)} countries, {len(unpublished)} naming no GADM unit")
    for iso, correction in unpublished:
        print(f"  {iso}  {correction}")

    return len(unpublished)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        raise SystemExit(check_shipped_table(CACHE_DIR))

    listing = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("fuzzy_matches.txt")
    candidates = read_candidates(listing)
    print(f"adjudicating {len(candidates)} candidate corrections with {MODEL}", flush=True)

    settled = adjudicate(candidates, echo=True)
    tally = Counter(settled.values())

    with PROPOSED.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(("iso", "written", "corrected", "verdict"))
        for (iso, written), verdict in sorted(settled.items()):
            candidate = next(c for i, w, c in candidates if (i, w) == (iso, written))
            writer.writerow((iso, written, candidate if verdict == "SAME" else "", verdict.lower()))

    print(f"\n{json.dumps(dict(tally))}")
    print(f"written to {PROPOSED}; promote what survives review into the shipped table")

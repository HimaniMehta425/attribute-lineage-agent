"""
Download loan-level HMDA (Home Mortgage Disclosure Act) data from the public
FFIEC/CFPB Data Browser API.

No API key required -- this is a fully public, unauthenticated government API:
https://ffiec.cfpb.gov/documentation/api/data-browser/

Usage:
    python scripts/download_hmda.py --state IL --county 17031 --year 2024
    python scripts/download_hmda.py --state IL --year 2024   # whole state

Raw downloads land in data/raw/ (gitignored -- this is real data, ~20-80MB per
state/year, so it isn't checked into the repo). A trimmed sample used by the
pipeline's tests and demo lives in data/sample/ and IS checked in.
"""
import argparse
import csv
import json
import urllib.request
from pathlib import Path

API_BASE = "https://ffiec.cfpb.gov/v2/data-browser-api/view/csv"
FILERS_API = "https://ffiec.cfpb.gov/v2/data-browser-api/view/filers"
RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"


def _get(url: str) -> bytes:
    req = urllib.request.Request(url)
    last_err = None
    for _ in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                return resp.read()
        except Exception as e:  # noqa: BLE001
            last_err = e
    raise last_err


def download(state: str, year: int, action_taken: str = "1", county: str | None = None) -> Path:
    """Download HMDA loan-level records (originated loans by default) as CSV."""
    params = f"states={state}&years={year}&actions_taken={action_taken}"
    if county:
        params += f"&counties={county}"
    url = f"{API_BASE}?{params}"

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    suffix = f"_{county}" if county else ""
    out_path = RAW_DIR / f"hmda_{state.lower()}{suffix}_{year}.csv"

    print(f"Fetching: {url}")
    # Note: the FFIEC WAF appears to block some custom/browser-spoofing User-Agent
    # strings but allows plain default clients (curl, bare urllib). Don't set a
    # custom User-Agent here -- it's been empirically flaky.
    data = _get(url)
    out_path.write_bytes(data)

    with open(out_path, newline="") as f:
        row_count = sum(1 for _ in csv.reader(f)) - 1
    print(f"Saved {row_count:,} rows -> {out_path}")
    return out_path


def download_institutions(state: str, year: int) -> Path:
    """Download the lender/institution reference list (LEI -> name) for a state/year.

    This is the reference table that lets the pipeline join a loan record's LEI
    to a human-readable lender name -- the second table in the multi-table join
    story (loan record x lender reference x tract reference).
    """
    url = f"{FILERS_API}?states={state}&years={year}"
    print(f"Fetching: {url}")
    data = _get(url)
    payload = json.loads(data)
    institutions = payload.get("institutions", [])

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RAW_DIR / f"institutions_{state.lower()}_{year}.csv"
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["lei", "name", "count", "period"])
        writer.writeheader()
        writer.writerows(institutions)
    print(f"Saved {len(institutions):,} institutions -> {out_path}")
    return out_path


def make_sample(raw_path: Path, sample_path: Path, n: int = 3000, seed: int = 42) -> None:
    """Deterministically sample n rows from a raw download for the committed fixture."""
    import random

    random.seed(seed)
    with open(raw_path, newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)

    sample = rows if len(rows) <= n else random.sample(rows, n)
    sample_path.parent.mkdir(parents=True, exist_ok=True)
    with open(sample_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(sample)
    print(f"Wrote {len(sample):,} sampled rows -> {sample_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", default="IL", help="Two-letter state code, e.g. IL")
    parser.add_argument("--county", default=None, help="5-digit county FIPS code, e.g. 17031 (Cook County, IL)")
    parser.add_argument("--year", type=int, default=2024)
    parser.add_argument("--action-taken", default="1", help="HMDA action_taken code(s), default 1 = loan originated")
    parser.add_argument("--make-sample", action="store_true", help="Also write a trimmed sample fixture")
    parser.add_argument("--sample-size", type=int, default=3000)
    args = parser.parse_args()

    raw = download(args.state, args.year, args.action_taken, args.county)
    institutions_path = download_institutions(args.state, args.year)

    if args.make_sample:
        sample_dir = Path(__file__).resolve().parent.parent / "data" / "sample"
        sample_out = sample_dir / f"hmda_{args.state.lower()}_sample.csv"
        make_sample(raw, sample_out, n=args.sample_size)

        # Institutions reference table is small already -- copy as-is into the sample dir.
        import shutil

        shutil.copy(institutions_path, sample_dir / institutions_path.name)

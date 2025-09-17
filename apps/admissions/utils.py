
from django.contrib.staticfiles import finders
from functools import lru_cache
import csv, io, logging, re

logger = logging.getLogger(__name__)

def _norm_header(s: str) -> str:
    # lower + non-alnum strip (e.g., "Roll No" -> "rollno")
    return re.sub(r'[^a-z0-9]+', '', (s or '').lower())

@lru_cache(maxsize=1)
def get_allowed_ssc_rolls():
    """
    Read static/csv/roll.csv and return a set of ints from the 'Roll No' column.
    Robust to BOM, quotes, extra spaces, trailing punctuation etc.
    If header not found, falls back to extracting all numbers in file.
    """
    path = finders.find("csv/roll.csv")
    if not path:
        logger.warning("Whitelist CSV not found at static 'csv/roll.csv'; skipping roll check.")
        return set()

    try:
        with open(path, "r", encoding="utf-8-sig", errors="ignore") as f:
            text = f.read()

        # Parse with csv first (handles quoted fields properly)
        reader = csv.reader(io.StringIO(text))
        rows = list(reader)
        if not rows:
            return set()

        headers = rows[0]
        roll_idx = None
        norm_headers = [_norm_header(h) for h in headers]

        # Prefer exact matches
        for i, h in enumerate(norm_headers):
            if h in {"rollno", "rollnumber", "roll", "sscroll", "ssc_roll"}:
                roll_idx = i
                break

        # If still not found, accept any header containing "roll"
        if roll_idx is None:
            for i, h in enumerate(norm_headers):
                if "roll" in h:
                    roll_idx = i
                    break

        allowed = set()
        if roll_idx is not None:
            for r in rows[1:]:
                if roll_idx >= len(r):
                    continue
                raw = (r[roll_idx] or "").strip()
                m = re.search(r"\d+", raw)  # grab the digits only
                if not m:
                    continue
                try:
                    allowed.add(int(m.group(0)))
                except ValueError:
                    continue
        else:
            # Fallback: grab every number in the file (less strict)
            nums = re.findall(r"\b\d+\b", text)
            allowed = {int(n) for n in nums}

        logger.info("Loaded %d SSC rolls from %s", len(allowed), path)
        return allowed

    except Exception as e:
        logger.exception("Error reading whitelist CSV at %s: %s", path, e)
        return set()


@lru_cache(maxsize=1)
def get_allowed_degree_rolls():
    """
    Read static/csv/roll.csv and return a set of ints from the 'Roll No' column.
    Robust to BOM, quotes, extra spaces, trailing punctuation etc.
    If header not found, falls back to extracting all numbers in file.
    """
    path = finders.find("csv/roll_degree.csv")
    if not path:
        logger.warning("Whitelist CSV not found at static 'csv/roll.csv'; skipping roll check.")
        return set()

    try:
        with open(path, "r", encoding="utf-8-sig", errors="ignore") as f:
            text = f.read()

        # Parse with csv first (handles quoted fields properly)
        reader = csv.reader(io.StringIO(text))
        rows = list(reader)
        if not rows:
            return set()

        headers = rows[0]
        roll_idx = None
        norm_headers = [_norm_header(h) for h in headers]

        # Prefer exact matches
        for i, h in enumerate(norm_headers):
            if h in {"rollno", "rollnumber", "roll", "admissionroll", "admission_roll"}:
                roll_idx = i
                break

        # If still not found, accept any header containing "roll"
        if roll_idx is None:
            for i, h in enumerate(norm_headers):
                if "roll" in h:
                    roll_idx = i
                    break

        allowed = set()
        if roll_idx is not None:
            for r in rows[1:]:
                if roll_idx >= len(r):
                    continue
                raw = (r[roll_idx] or "").strip()
                m = re.search(r"\d+", raw)  # grab the digits only
                if not m:
                    continue
                try:
                    allowed.add(int(m.group(0)))
                except ValueError:
                    continue
        else:
            # Fallback: grab every number in the file (less strict)
            nums = re.findall(r"\b\d+\b", text)
            allowed = {int(n) for n in nums}

        logger.info("Loaded %d SSC rolls from %s", len(allowed), path)
        return allowed

    except Exception as e:
        logger.exception("Error reading whitelist CSV at %s: %s", path, e)
        return set()

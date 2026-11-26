"""Compare a new public release check with the archived observation.

Usage: python scripts/compare_public_check.py ARCHIVED.json NEW.json

Compares outcomes, not timings: each cohort reader's status and rows, and the
trial's status, checks, row count and row digest. A difference means the readers
or the host now behave differently from the archived record, so the case study
may need updating. Exits with status 1 when any outcome differs.
"""

import json
import sys


def outcomes(record):
    cohort = {r["reader"]: {"status": r["status"], "rows": r.get("rows")}
              for r in record["cohort_selection"]["results"]}
    trial = record["one_trial"]
    return {
        "packages": record["packages"],
        "cohort": cohort,
        "trial": {key: trial.get(key) for key in ("status", "checks", "rows_returned", "rows_sha256")},
    }


def differences(old, new, path=""):
    if isinstance(old, dict) and isinstance(new, dict):
        for key in sorted(set(old) | set(new)):
            yield from differences(old.get(key), new.get(key), f"{path}.{key}" if path else key)
    elif old != new:
        yield f"{path}: archived {old!r}, now {new!r}"


def main(archived_path, new_path):
    with open(archived_path) as stream:
        archived = json.load(stream)
    with open(new_path) as stream:
        new = json.load(stream)
    changed = list(differences(outcomes(archived), outcomes(new)))
    trial = new["one_trial"]
    print(f"New run {new['started_utc']}: trial {trial['seconds']} s, {trial['http']['requests']} requests, "
          f"{trial['http']['declared_get_body_bytes']:,} declared GET bytes")
    if changed:
        print("Outcomes differ from the archived record:")
        for line in changed:
            print(f"  {line}")
        return 1
    print("Outcomes match the archived record.")
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:3]))

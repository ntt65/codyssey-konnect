"""Check app settings without network calls or printing secret values.

From repository root: python utils/scripts/setup_dev.py [--feature rag|ingest|llm|auth]
Default app profile checks basic startup, or RAG when SUPABASE_DB_URL is set.
Exit 0 = settings present and basic format valid, 1 = missing/invalid settings,
2 = invalid settings types/dependencies. This does not prove live connectivity.
"""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--feature", choices=["app", "basic", "rag", "ingest", "llm", "auth"], default="app")
    args = parser.parse_args(argv)
    try:
        from pydantic import ValidationError
    except ImportError:
        print("ERROR: install project dependencies using the README instructions.")
        return 2
    try:
        # Import inside the boundary so invalid .env types do not print their values.
        from app.config import settings
        report = settings.configuration_report(args.feature)
    except ValidationError as exc:
        fields = sorted({str(error["loc"][0]).upper() for error in exc.errors() if error.get("loc")})
        print("ERROR: invalid setting types: " + ", ".join(fields))
        print("Use .env.example and README; values are intentionally omitted.")
        return 2
    except ImportError:
        print("ERROR: project dependencies are incomplete; follow the README installation steps.")
        return 2
    print(f"profile={report['profile']} configuration_ready={str(report['ready']).lower()}")
    if report["missing"]:
        print("missing: " + ", ".join(key.upper() for key in report["missing"]))
    if report["invalid"]:
        print("invalid: " + ", ".join(key.upper() for key in report["invalid"]))
    print("Checks configuration only. No DB, LLM or Auth requests were sent.")
    return 0 if report["ready"] else 1

if __name__ == "__main__":
    raise SystemExit(main())

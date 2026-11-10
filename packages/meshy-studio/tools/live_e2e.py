"""LIVE end-to-end run: ONE image through the real pipeline against the real Meshy site.

This SPENDS REAL CREDITS (about 30 on one account). It refuses to run without --spend-credits.
Usage: python tools/live_e2e.py --image D:/path/model.png --spend-credits [--account-id N]
"""
import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.runner import build_service, data_root  # noqa: E402

parser = argparse.ArgumentParser()
parser.add_argument("--image", required=True)
parser.add_argument("--spend-credits", action="store_true", help="required: acknowledges that real credits are spent")
parser.add_argument("--account-id", type=int, help="pin the run to one account (otherwise automatic rotation)")
args = parser.parse_args()
if not args.spend_credits:
    sys.exit("Refusing to run: this spends real Meshy credits. Pass --spend-credits to confirm.")

service = build_service(data_root())
if args.account_id:
    service.use_account(args.account_id)
job_id = service.enqueue(args.image, "live e2e")
started = time.time()
service.run_pending()
job = service.database.get_job(job_id)
print(f"job {job_id}: {job.status} in {time.time() - started:.0f}s, submitted={job.submitted}, result={job.result_path}")
print("library:", [(m['name'], m['triangles'], m['formats']) for m in service.database.list_models()[:3]])
service.release_all_browsers()
sys.exit(0 if job.status == "Completed" else 1)

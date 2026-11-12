"""Process whatever is Pending in the queue (live)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.runner import build_service, data_root

service = build_service(data_root())
print("processed", service.run_pending(), flush=True)
for j in service.database.list_jobs():
    print("JOB", j.id, j.status, j.account_id, j.retries, j.error, flush=True)
for a in service.database.list_accounts():
    print("ACC", a.id, a.status, a.authorized, a.cooldown_until, flush=True)

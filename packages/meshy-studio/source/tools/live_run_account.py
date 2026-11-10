"""Live: run one image on one account id, print the WorkerResult."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.runner import build_service, data_root

svc = build_service(data_root())
print('export_dir', svc.worker.export_dir, flush=True)
account = next(a for a in svc.database.list_accounts() if a.id == int(sys.argv[1]))
print(svc.worker.run_one(account.id, sys.argv[2], account_key=account.email), flush=True)

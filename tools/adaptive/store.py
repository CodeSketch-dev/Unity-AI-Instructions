"""Persistent performance memory (SQLite, stdlib). Aggregates only; no prompts, no screenshots, no secrets.

Unknown values are stored as NULL and reported as UNKNOWN; nothing is ever invented.
Soft reset = a `resets` row that makes older runs invisible to the selector (undoable); the DB file is
backed up before every migration, reset and restore.
"""
import glob
import os
import re
import shutil
import sqlite3
import time

SCHEMA_VERSION = 2
MAX_ROWS = 50000
KEEP_ROWS = 40000
KEEP_BACKUPS = 10
MAX_TEXT = 200

M1 = """
CREATE TABLE meta (k TEXT PRIMARY KEY, v TEXT);
CREATE TABLE runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts_start REAL, ts_end REAL NOT NULL,
  category TEXT NOT NULL, env TEXT NOT NULL, method TEXT NOT NULL,
  success INTEGER NOT NULL, verified INTEGER NOT NULL DEFAULT 0,
  latency_ms REAL, tool_ms REAL, wait_ms REAL, model_ms REAL,
  tool_calls INTEGER, in_tok INTEGER, out_tok INTEGER, cache_tok INTEGER,
  retries INTEGER DEFAULT 0, recovery_ms REAL, fail_reason TEXT, predicted_p REAL
);
CREATE INDEX runs_scope ON runs(category, env, method, ts_end);
CREATE TABLE resets (id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL NOT NULL, category TEXT, env TEXT, method TEXT, undone INTEGER NOT NULL DEFAULT 0);
"""
M2 = """
ALTER TABLE runs ADD COLUMN task_fp TEXT;
CREATE INDEX runs_fp ON runs(task_fp);
"""
MIGRATIONS = {1: M1, 2: M2}

SAFE = re.compile(r"[^a-z0-9_.:=|/@-]")
REDACT = [
    (re.compile(r"(?i)\b(?:sk|pk|rk|ghp|gho|ghs|xox[abp]|akia|aiza)[-_A-Za-z0-9]{12,}"), "[KEY]"),
    (re.compile(r"(?i)bearer\s+[a-z0-9._~+/=-]{8,}"), "[KEY]"),
    (re.compile(r"(?i)\b(api[_-]?key|token|secret|password|passwd|pwd|credential)s?\s*[:=]\s*\S+"), r"\1=[REDACTED]"),
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), "[EMAIL]"),
    (re.compile(r"(?i)[a-z]:\\users\\[^\\]+"), "[USERHOME]"),
    (re.compile(r"/(?:home|Users)/[^/\s]+"), "[USERHOME]"),
    (re.compile(r"[A-Za-z0-9+/=_-]{32,}"), "[BLOB]"),
]


def home():
    return os.environ.get("ADAPTIVE_HOME") or os.path.join(os.path.expanduser("~"), ".claude", "adaptive")


def db_path():
    return os.path.join(home(), "perf.db")


def clean_key(s, maxlen=80):
    return SAFE.sub("_", (s or "").strip().lower())[:maxlen] or "unknown"


def redact(text, maxlen=MAX_TEXT):
    if text is None:
        return None
    t = str(text)
    for pat, rep in REDACT:
        t = pat.sub(rep, t)
    return t.replace("\n", " ")[:maxlen]


def _version(conn):
    names = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if "meta" not in names:
        return 0
    row = conn.execute("SELECT v FROM meta WHERE k='schema_version'").fetchone()
    return int(row[0]) if row else 0


def apply_upto(conn, target):
    v = _version(conn)
    for n in range(v + 1, target + 1):
        conn.executescript(MIGRATIONS[n])
        conn.execute("INSERT OR REPLACE INTO meta(k,v) VALUES('schema_version',?)", (str(n),))
    conn.commit()


def backup(path=None, tag="manual"):
    path = path or db_path()
    if not os.path.isfile(path):
        return None
    bdir = os.path.join(os.path.dirname(path), "backups")
    os.makedirs(bdir, exist_ok=True)
    dst = os.path.join(bdir, "perf-%s-%s.db" % (tag, time.strftime("%Y%m%d-%H%M%S")))
    n = 0
    while os.path.exists(dst):
        n += 1
        dst = dst[:-3] + "-%d.db" % n
    src = sqlite3.connect(path)
    out = sqlite3.connect(dst)
    src.backup(out)
    out.close()
    src.close()
    files = sorted(glob.glob(os.path.join(bdir, "perf-*.db")), key=os.path.getmtime)
    for old in files[:-KEEP_BACKUPS]:
        os.remove(old)
    return dst


def connect(path=None):
    path = path or db_path()
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    existed = os.path.isfile(path)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    v = _version(conn)
    if v > SCHEMA_VERSION:
        conn.close()
        raise RuntimeError("perf.db schema %d is newer than this tool (%d); update the tools" % (v, SCHEMA_VERSION))
    if v < SCHEMA_VERSION:
        if existed and v > 0:
            conn.commit()
            backup(path, "premigrate-v%d" % v)
        apply_upto(conn, SCHEMA_VERSION)
    return conn


def _num(x):
    try:
        return None if x is None or float(x) < 0 else float(x)
    except (TypeError, ValueError):
        return None


def _int(x):
    v = _num(x)
    return None if v is None else int(v)


def record_run(conn, category, env, method, success, verified=False, latency_ms=None, tool_ms=None, wait_ms=None,
               model_ms=None, tool_calls=None, in_tok=None, out_tok=None, cache_tok=None, retries=0,
               recovery_ms=None, fail_reason=None, predicted_p=None, ts_start=None, ts_end=None, task_fp=None):
    ts_end = ts_end or time.time()
    if ts_start is None and latency_ms is not None:
        ts_start = ts_end - float(latency_ms) / 1000.0
    cur = conn.execute(
        "INSERT INTO runs(ts_start,ts_end,category,env,method,success,verified,latency_ms,tool_ms,wait_ms,model_ms,"
        "tool_calls,in_tok,out_tok,cache_tok,retries,recovery_ms,fail_reason,predicted_p,task_fp) "
        "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (ts_start, ts_end, clean_key(category), clean_key(env, 160), clean_key(method), int(bool(success)),
         int(bool(verified)), _num(latency_ms), _num(tool_ms), _num(wait_ms), _num(model_ms), _int(tool_calls),
         _int(in_tok), _int(out_tok), _int(cache_tok), _int(retries) or 0, _num(recovery_ms), redact(fail_reason),
         None if predicted_p is None else min(1.0, max(0.0, float(predicted_p))), clean_key(task_fp) if task_fp else None))
    conn.commit()
    prune(conn)
    return cur.lastrowid


def prune(conn, max_rows=MAX_ROWS, keep_rows=KEEP_ROWS):
    n = conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
    if n <= max_rows:
        return 0
    cut = conn.execute("SELECT id FROM runs ORDER BY id DESC LIMIT 1 OFFSET ?", (keep_rows,)).fetchone()
    conn.execute("DELETE FROM runs WHERE id<=?", (cut[0],))
    conn.commit()
    conn.execute("VACUUM")
    return n - keep_rows


def since_ts(conn, category, env, method):
    row = conn.execute(
        "SELECT MAX(ts) FROM resets WHERE undone=0 AND (category IS NULL OR category=?) AND (env IS NULL OR env=?) "
        "AND (method IS NULL OR method=?)", (category, env, method)).fetchone()
    return row[0] or 0.0


def scope_runs(conn, category, env, method):
    category, env, method = clean_key(category), clean_key(env, 160), clean_key(method)
    since = since_ts(conn, category, env, method)
    rows = conn.execute("SELECT * FROM runs WHERE category=? AND env=? AND method=? AND ts_end>? ORDER BY ts_end ASC",
                        (category, env, method, since)).fetchall()
    return [dict(r) for r in rows]


def reset(conn, category=None, env=None, method=None, path=None):
    conn.commit()
    backup(path or db_path_of(conn), "prereset")
    cur = conn.execute("INSERT INTO resets(ts,category,env,method) VALUES(?,?,?,?)",
                       (time.time(), clean_key(category) if category else None, clean_key(env, 160) if env else None,
                        clean_key(method) if method else None))
    conn.commit()
    return cur.lastrowid


def undo_reset(conn, reset_id):
    conn.execute("UPDATE resets SET undone=1 WHERE id=?", (reset_id,))
    conn.commit()


def db_path_of(conn):
    for _, name, f in conn.execute("PRAGMA database_list"):
        if name == "main":
            return f
    return db_path()


def restore(conn_or_none, file, path=None):
    path = path or db_path()
    if conn_or_none is not None:
        conn_or_none.close()
    backup(path, "prerestore")
    shutil.copyfile(file, path)
    return path


def summary(conn, category=None):
    q = "SELECT category, env, method, COUNT(*) n, SUM(success) ok, SUM(verified) ver, AVG(latency_ms) lat, " \
        "SUM(in_tok IS NULL) unk_tok FROM runs"
    args = []
    if category:
        q += " WHERE category=?"
        args.append(clean_key(category))
    q += " GROUP BY category, env, method ORDER BY category, env, method"
    return [dict(r) for r in conn.execute(q, args)]

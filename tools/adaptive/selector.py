"""Method selection from measured history, with priors, confidence, exploration, regression and calibration.

The hierarchy (candidates in order) is only a PRIOR. Data overrides it once a method has enough effective
samples in the exact (category, env) scope. Nothing here is a claim of truth: every decision returns its basis.
Weights: (latency, tokens, success). Token term is dropped (UNKNOWN) when tokens are not measured.
"""
import math
import statistics
import time

from . import store

PROFILES = {"speed": (0.6, 0.1, 0.3), "tokens": (0.1, 0.6, 0.3), "accuracy": (0.1, 0.1, 0.8), "balanced": (0.3, 0.2, 0.5)}
MIN_N = 5.0
HALF_LIFE_DAYS = 30.0
Z90 = 1.2816
MIN_SUCCESS = 0.75
MIN_SUCCESS_CRITICAL = 0.90
EXPLORE_EVERY = 10
EXPLORE_SKIP_LB = 0.95
EXPLORE_SKIP_LAT_MS = 1000.0


def wilson_lb(p, n, z=Z90):
    if n <= 0:
        return 0.0
    d = 1 + z * z / n
    centre = p + z * z / (2 * n)
    margin = z * math.sqrt(max(p * (1 - p) / n + z * z / (4 * n * n), 0.0))
    return max(0.0, (centre - margin) / d)


def method_stats(rows, now=None, half_life_days=HALF_LIFE_DAYS):
    """Age-weighted stats. Success counts only when verified. Tokens None unless >=50% of rows measured them."""
    now = now or time.time()
    if not rows:
        return {"n_raw": 0, "n_eff": 0.0, "p": 0.0, "lb": 0.0, "lat_ms": None, "tok": None, "tok_known": 0.0,
                "rec_ms": None, "unverified_frac": 0.0}
    ws = [0.5 ** (max(0.0, now - r["ts_end"]) / (half_life_days * 86400.0)) for r in rows]
    n_eff = sum(ws)
    good = [(w, r) for w, r in zip(ws, rows) if r["success"] and r["verified"]]
    p = sum(w for w, _ in good) / n_eff if n_eff else 0.0
    lat = [(w, r["latency_ms"]) for w, r in good if r["latency_ms"] is not None]
    lat_ms = sum(w * v for w, v in lat) / sum(w for w, _ in lat) if lat else None
    known = [(w, r) for w, r in zip(ws, rows) if r["in_tok"] is not None and r["out_tok"] is not None]
    tok_known = len(known) / len(rows)
    tg = [(w, r["in_tok"] + r["out_tok"]) for w, r in known if r["success"] and r["verified"]]
    tok = sum(w * v for w, v in tg) / sum(w for w, _ in tg) if (tg and tok_known >= 0.5) else None
    rec = [r["recovery_ms"] for r in rows if r["recovery_ms"] is not None]
    return {"n_raw": len(rows), "n_eff": n_eff, "p": p, "lb": wilson_lb(p, n_eff), "lat_ms": lat_ms, "tok": tok,
            "tok_known": tok_known, "rec_ms": (sum(rec) / len(rec)) if rec else None,
            "unverified_frac": sum(1 for r in rows if not r["verified"]) / len(rows)}


def detect_regression(rows, recent=5, min_base=8):
    if len(rows) < recent + min_base:
        return {"regressed": False, "why": "not enough history"}
    base, rec = rows[:-recent], rows[-recent:]
    sr = lambda xs: sum(1 for r in xs if r["success"] and r["verified"]) / len(xs)  # noqa: E731
    why = []
    if sr(rec) <= sr(base) - 0.25:
        why.append("success %.2f -> %.2f" % (sr(base), sr(rec)))
    bl = [r["latency_ms"] for r in base if r["success"] and r["latency_ms"] is not None]
    rl = [r["latency_ms"] for r in rec if r["success"] and r["latency_ms"] is not None]
    if len(bl) >= 4 and len(rl) >= 3 and statistics.median(rl) >= 2 * statistics.median(bl):
        why.append("median latency %.0f -> %.0f ms" % (statistics.median(bl), statistics.median(rl)))
    return {"regressed": bool(why), "why": "; ".join(why) or "stable"}


def app_prefix(env):
    """Signature up to and including the `app=` segment; later segments (ver=...) may change without it being another app."""
    segs = env.split("|")
    idx = next((i for i, x in enumerate(segs) if x.startswith("app=")), 0)
    return "|".join(segs[:idx + 1])


def detect_env_change(conn, category, env):
    category, env = store.clean_key(category), store.clean_key(env, 160)
    app = app_prefix(env)
    envs = [r[0] for r in conn.execute("SELECT DISTINCT env FROM runs WHERE category=? AND (env=? OR env LIKE ?)",
                                       (category, app, app + "|%"))]
    if envs and env not in envs:
        return {"changed": True, "previous": envs[:5]}
    return {"changed": False, "previous": []}


def calibration(conn, category, env, last=50):
    """Compare predicted vs actual success. Only overconfidence is corrected (offset <= 0)."""
    rows = conn.execute("SELECT predicted_p, success, verified FROM runs WHERE category=? AND env=? AND predicted_p IS NOT NULL "
                        "ORDER BY id DESC LIMIT ?", (store.clean_key(category), store.clean_key(env, 160), last)).fetchall()
    if len(rows) < 10:
        return {"n": len(rows), "offset": 0.0, "brier": None}
    pred = [r[0] for r in rows]
    act = [1.0 if (r[1] and r[2]) else 0.0 for r in rows]
    brier = sum((p - a) ** 2 for p, a in zip(pred, act)) / len(rows)
    off = sum(act) / len(act) - sum(pred) / len(pred)
    return {"n": len(rows), "offset": max(-0.3, min(0.0, off)), "brier": brier}


def select(conn, category, candidates, env, profile="balanced", critical=False, now=None, explore=True):
    now = now or time.time()
    if critical:
        profile = "accuracy"
        explore = False
    wl, wt, ws = PROFILES[profile]
    min_ok = MIN_SUCCESS_CRITICAL if critical else MIN_SUCCESS
    env_chg = detect_env_change(conn, category, env)
    cal = calibration(conn, category, env)
    st, reg = {}, {}
    for m in candidates:
        rows = store.scope_runs(conn, category, env, m)
        st[m] = method_stats(rows, now)
        st[m]["lb_adj"] = max(0.0, st[m]["lb"] + cal["offset"])
        reg[m] = detect_regression(rows)
    backed = [m for m in candidates if st[m]["n_eff"] >= MIN_N]
    out = {"category": category, "env": env, "profile": profile, "critical": critical, "env_changed": env_chg,
           "calibration": cal, "stats": st, "regression": {m: r for m, r in reg.items() if r["regressed"]}, "fallbacks": []}
    if not backed:
        return dict(out, method=candidates[0], source="prior", predicted_p=None, fallbacks=candidates[1:],
                    reason="no method has >=%.0f effective verified-scope samples; using hierarchy order" % MIN_N)
    eligible = [m for m in backed if st[m]["lb_adj"] >= min_ok and not reg[m]["regressed"]]
    if not eligible:
        eligible = [m for m in backed if st[m]["lb_adj"] >= min_ok]
    if not eligible and critical:
        keep = [m for m in backed if st[m]["lb_adj"] >= MIN_SUCCESS and not reg[m]["regressed"]]
        if keep:
            best = max(keep, key=lambda m: st[m]["lb_adj"])
            return dict(out, method=best, source="data", predicted_p=st[best]["lb_adj"], fallbacks=[m for m in candidates if m != best],
                        reason="critical task: confidence below %.2f yet best evidenced method kept; never gamble on an untested method" % min_ok)
    if not eligible:
        untested = [m for m in candidates if m not in backed]
        if untested:
            return dict(out, method=untested[0], source="prior", predicted_p=None, fallbacks=[m for m in candidates if m != untested[0]],
                        reason="data-backed methods are below min success %.2f; trying next untested method" % min_ok)
        best = max(backed, key=lambda m: st[m]["lb_adj"])
        return dict(out, method=best, source="data", predicted_p=st[best]["lb_adj"], fallbacks=[m for m in candidates if m != best],
                    reason="no method meets min success %.2f; best available" % min_ok)

    def exp_cost(m, key):
        s = st[m]
        base = s[key]
        if base is None:
            return None
        fail = s["rec_ms"] if (key == "lat_ms" and s["rec_ms"] is not None) else base
        return base + (1 - s["p"]) * fail

    lats = {m: exp_cost(m, "lat_ms") for m in eligible}
    toks = {m: exp_cost(m, "tok") for m in eligible}
    use_lat = all(v is not None for v in lats.values())
    use_tok = all(v is not None for v in toks.values())
    w_l, w_t, w_s = (wl if use_lat else 0.0), (wt if use_tok else 0.0), ws
    tot = (w_l + w_t + w_s) or 1.0
    scores = {}
    for m in eligible:
        ln = (min(lats.values()) / lats[m]) if use_lat and lats[m] else 1.0
        tn = (min(toks.values()) / toks[m]) if use_tok and toks[m] else 1.0
        scores[m] = (w_l * ln + w_t * tn + w_s * st[m]["lb_adj"]) / tot
    best = max(eligible, key=lambda m: (scores[m], -candidates.index(m)))
    reason = "data-backed best by %s profile%s" % (profile, "" if use_tok else "; tokens UNKNOWN so excluded")
    under = [m for m in candidates if st[m]["n_eff"] < MIN_N and not reg[m]["regressed"]]
    total_runs = sum(s["n_raw"] for s in st.values())
    cheap_enough = st[best]["lb_adj"] >= EXPLORE_SKIP_LB and (st[best]["lat_ms"] or 0) <= EXPLORE_SKIP_LAT_MS
    if explore and under and not cheap_enough and total_runs % EXPLORE_EVERY == EXPLORE_EVERY - 1:
        pick = under[0]
        return dict(out, method=pick, source="explore", predicted_p=None, scores=scores,
                    fallbacks=[best] + [m for m in candidates if m not in (pick, best)],
                    reason="bounded exploration of under-sampled method (every %d runs); safe fallback %s" % (EXPLORE_EVERY, best))
    return dict(out, method=best, source="data", predicted_p=st[best]["lb_adj"], scores=scores,
                fallbacks=[m for m in candidates if m != best], reason=reason)

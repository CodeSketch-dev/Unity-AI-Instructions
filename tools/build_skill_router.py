"""Build skill_router.json (ASCII) from skills/*/SKILL.md so the UserPromptSubmit router can match ANY skill, including future ones.

Usage: python tools/build_skill_router.py [skills-dir] [out-json]
Keyword sources per skill: optional `triggers:` frontmatter (comma separated, weight 3), name tokens (weight 3),
description words (weight 1). Vietnamese prompts are matched through VI_MAP after diacritics are stripped by the hook.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from skill_lint import parse_frontmatter  # noqa: E402

STOP = set("""a an and any are as at be by for from has have how in into is it its of on or per so that the their them then this to use used uses using when where which while with without within your you all each every more most not only also but can may must should will one two new via vs etc such than too out off over under after before during both other another same still just like make makes made get gets set sets add adds adding added build builds building create creates creating need needs needed instead rather work works working
skill skills rule rules template templates recipe recipes system systems basic common generic general project projects game games unity mobile android low end per task tasks step steps file files code asset assets data
""".split())
NAME_STOP = {"game", "skill", "rule", "template", "recipe", "recipes", "system", "basic", "common", "generic", "kit", "and", "the"}

# Vietnamese (diacritics already stripped, lowercase) -> English trigger words
VI_MAP = {
    "nut": "button", "chu": "text label", "can giua": "center align", "can le": "align", "canh": "align", "gia": "price", "bang": "board panel popup",
    "giao dien": "ui", "mua": "purchase buy shop", "ban": "sell shop", "tien": "cash currency money", "thanh": "bar", "dong": "close",
    "bieu tuong": "icon", "hinh": "image sprite", "dep": "polish ui style", "muot": "polish smooth juice", "cam giac": "game feel juice polish",
    "hieu ung": "vfx effect", "am thanh": "audio sfx", "nhac": "music audio", "quang cao": "ads", "luu": "save data", "kinh te": "economy",
    "can bang": "balance economy", "nhan vat": "character", "thu cung": "pet", "trung": "egg", "bot": "bots", "kiem tra": "test qa verify",
    "loi": "bug error", "toi uu": "perf optimize", "dung hinh": "port clone reference", "giong": "clone reference port", "cua hang": "shop",
    "huong dan": "tutorial", "camera": "camera", "bo cuc": "layout", "canh bao": "toast warning", "thong bao": "toast notification",
    "phan thuong": "reward", "nhiem vu": "quest", "cap do": "level progression", "dem nguoc": "timer countdown", "ngon ngu": "localization",
    "xoa": "remove delete", "doi ten": "rename", "tab": "tab", "icon": "icon", "anim": "animation tween", "phong to": "scale pulse animation",
}


def words(text):
    return [w for w in re.findall(r"[a-z][a-z0-9]{2,}", text.lower()) if w not in STOP]


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "skills"
    out = sys.argv[2] if len(sys.argv) > 2 else "skill_router.json"
    skills = []
    for folder in sorted(os.listdir(root)):
        p = os.path.join(root, folder, "SKILL.md")
        if not os.path.isfile(p):
            continue
        with open(p, encoding="utf-8") as f:
            fm, _ = parse_frontmatter(f.read())
        fm = fm or {}
        name = fm.get("name") or folder
        desc = fm.get("description", "")
        explicit = [t.strip().lower() for t in fm.get("triggers", "").split(",") if t.strip()]
        ntok = [t for t in re.split(r"[-_]", name.lower()) if len(t) >= 3 and t not in NAME_STOP]
        use = re.split(r"(?i)\buse (?:when|before|at|after|for|it|this)\b", desc, maxsplit=1)
        dsrc = use[1] if len(use) > 1 else desc
        dwords = sorted(set(words(dsrc)) - set(ntok))[:40]
        skills.append({"n": name, "t": sorted(set(explicit)), "w": ntok, "d": dwords})
    data = {"vi": VI_MAP, "skills": skills}
    with open(out, "w", encoding="ascii", newline="\n") as f:
        json.dump(data, f, ensure_ascii=True, separators=(",", ":"))
    print("skill_router.json: %d skills, %d bytes" % (len(skills), os.path.getsize(out)))


if __name__ == "__main__":
    main()

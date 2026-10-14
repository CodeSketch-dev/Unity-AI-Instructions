"""Print the RectTransform tree of a Unity prefab (names, anchors, sizes, sprite + script names) without opening Unity.

Usage: python -I dump_prefab.py <prefab> <guid-cache.json>
guid-cache.json maps guid -> asset path (reference-index output). Missing guids print as the first 8 characters.
"""
import json
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")


def name_of(cache, guid):
    value = cache.get(guid, guid[:8])
    if isinstance(value, dict):
        value = value.get("path", guid[:8])
    return str(value).split("/")[-1]


def main(prefab, cache_path):
    cache = json.load(open(cache_path, encoding="utf8"))
    text = open(prefab, encoding="utf8").read()
    comps, gos = {}, {}
    for doc in re.split(r"\n--- !u!", text):
        m = re.match(r"(\d+) &(\d+)", doc)
        if not m:
            continue
        comps[m.group(2)] = (m.group(1), doc)
        if m.group(1) == "1":
            gos[m.group(2)] = doc
    rects = {}
    for fid, (cid, doc) in comps.items():
        if cid != "224":
            continue
        go = re.search(r"m_GameObject: \{fileID: (\d+)\}", doc).group(1)
        father = re.search(r"m_Father: \{fileID: (\d+)\}", doc).group(1)
        vec = lambda key: re.search(key + r": \{x: ([-\d.e]+), y: ([-\d.e]+)\}", doc).groups()
        rects[fid] = dict(go=go, father=father, pos=vec("m_AnchoredPosition"), size=vec("m_SizeDelta"), amin=vec("m_AnchorMin"), amax=vec("m_AnchorMax"))
    per_go = {}
    for fid, (cid, doc) in comps.items():
        if cid == "114":
            go = re.search(r"m_GameObject: \{fileID: (\d+)\}", doc).group(1)
            per_go.setdefault(go, []).append(doc)

    def describe(go):
        out = []
        for doc in per_go.get(go, []):
            guid = re.search(r"m_Script: \{fileID: \d+, guid: (\w+)", doc).group(1)
            item = name_of(cache, guid)
            sprite = re.search(r"m_Sprite: \{fileID: (\d+), guid: (\w+)", doc)
            if sprite:
                item += " sprite=" + name_of(cache, sprite.group(2))
                kind = re.search(r"m_Type: (\d)", doc)
                if kind:
                    item += " type=" + kind.group(1)
            out.append(item)
        return ",".join(out)

    children = {}
    for fid, r in rects.items():
        children.setdefault(r["father"], []).append(fid)

    def go_name(go):
        m = re.search(r"m_Name: (.*)", gos[go])
        return m.group(1) if m else "?"

    def walk(fid, depth):
        r = rects[fid]
        print("  " * depth + f"{go_name(r['go'])} pos={r['pos']} size={r['size']} a={r['amin']}-{r['amax']} | {describe(r['go'])}")
        for child in children.get(fid, []):
            walk(child, depth + 1)

    for fid, r in rects.items():
        if r["father"] == "0":
            walk(fid, 0)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])

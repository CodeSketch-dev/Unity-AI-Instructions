"""Turn hooks/hooks.json into a settings.json snippet with absolute paths for a user-level install (no plugin needed).

  py -I tools/install_hooks.py [--root ~/.claude/pipeline-hooks] [--write docs/hooks-settings.snippet.json]

sync.bat copies hooks/ to <root>/hooks. This tool only prints or writes the snippet; merging it into ~/.claude/settings.json
(or a project's .claude/settings.json) is a deliberate human or agent step because settings are shared configuration.
Plugin installs do not need it: ${CLAUDE_PLUGIN_ROOT} is resolved by Claude Code.
"""
import argparse
import json
import os
import sys


def convert(hooks, root):
    root = root.replace("\\", "/")
    text = json.dumps(hooks).replace("${CLAUDE_PLUGIN_ROOT}", root)
    return json.loads(text)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    here = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument("--hooks", default=os.path.join(here, "..", "hooks", "hooks.json"))
    ap.add_argument("--root", default=os.path.join(os.path.expanduser("~"), ".claude", "pipeline-hooks"))
    ap.add_argument("--write")
    a = ap.parse_args(argv)
    with open(a.hooks, encoding="utf-8") as f:
        data = json.load(f)
    out = convert(data, a.root)
    text = json.dumps(out, indent=2)
    if a.write:
        with open(a.write, "w", encoding="utf-8", newline="\n") as f:
            f.write(text + "\n")
        print("wrote " + a.write)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())

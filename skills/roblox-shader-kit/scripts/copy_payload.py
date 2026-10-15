"""Copy the bundled Roblox shader payload into a Unity project, preserving .meta files."""
import argparse
import os
import shutil


def copy_payload(source_root, project_root):
    destination = os.path.join(project_root, "Assets", "_Game", "RobloxShaderKit")
    copied = 0
    for base, _, files in os.walk(source_root):
        for name in files:
            source = os.path.join(base, name)
            relative = os.path.relpath(source, source_root)
            # SourceContract/Scripts is audit/reference material only. Canonical
            # runtime scripts are copied from Runtime/Scripts; copying both into
            # Unity creates duplicate type definitions and breaks compilation.
            if relative.replace(os.sep, "/").startswith("SourceContract/Scripts/"):
                continue
            target = os.path.join(destination, relative)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            shutil.copy2(source, target)
            copied += 1
    return destination, copied


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("project", help="Unity project root")
    parser.add_argument("--source", default=os.path.join(os.path.dirname(__file__), "..", "assets", "roblox-shader-kit"))
    args = parser.parse_args(argv)
    destination, copied = copy_payload(os.path.abspath(args.source), os.path.abspath(args.project))
    print("COPIED %d files to %s" % (copied, destination))
    print("NEXT: stop Play Mode, refresh/import through Unity MCP, compile, and inspect Console")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

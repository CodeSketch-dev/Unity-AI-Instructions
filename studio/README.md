# Studio agent definitions

One file per Paperclip agent (1 Director + 18 specialists). Source of truth for rebuilding the studio on another machine.

- `model`: opus | sonnet | haiku (mapped to claude-*-5-5 at creation).
- Machine paths (Unity, Blender, Android SDK) live in a per-machine config, never in these files.
- Rebuild: create each agent via the Paperclip API/UI and use the file body as its instructions. Log in to Claude separately on each machine.
- `gen.py` regenerates `agents/` from its table; edit the table, not the generated files.
- Changes go through branch + review like any other shared instruction.

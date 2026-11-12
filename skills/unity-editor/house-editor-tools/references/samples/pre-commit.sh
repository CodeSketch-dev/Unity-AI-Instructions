#!/usr/bin/env bash
# tools/githooks/pre-commit  - install once per clone: git config core.hooksPath tools/githooks
# Fast checks only (seconds). The slow Unity batch check runs in CI or with RUN_UNITY_CHECK=1.
set -e
staged=$(git diff --cached --name-only --diff-filter=ACM)

# 1. every staged asset has its .meta (staged or already tracked)
for f in $staged; do
  case "$f" in
    Assets/*.meta) ;;
    Assets/*)
      if ! echo "$staged" | grep -qx "$f.meta" && ! git ls-files --error-unmatch "$f.meta" >/dev/null 2>&1; then
        echo "missing .meta for $f"; exit 1
      fi ;;
  esac
done

# 2. no derived/generated folders under Assets
if echo "$staged" | grep -qiE '^Assets/(graphify-out|.*\.tmp|.*Backup~)/'; then
  echo "derived/backup folder staged under Assets/"; exit 1
fi

# 3. text-serialized scenes and prefabs only (binary scenes are not diffable)
for f in $(echo "$staged" | grep -E '\.(unity|prefab)$' || true); do
  head -c 5 "$f" | grep -q '%YAML' || { echo "binary-serialized: $f (set Asset Serialization = Force Text)"; exit 1; }
done

# 4. missing script markers in text scenes/prefabs (m_Script: {fileID: 0})
if [ -n "$(echo "$staged" | grep -E '\.(unity|prefab)$' || true)" ]; then
  bad=$(git diff --cached -U0 -- '*.unity' '*.prefab' | grep -E '^\+.*m_Script: \{fileID: 0\}' || true)
  [ -z "$bad" ] || { echo "missing script added:"; echo "$bad"; exit 1; }
fi

# 5. optional full Unity check
if [ "${RUN_UNITY_CHECK:-0}" = "1" ]; then
  "${UNITY_EXE:?set UNITY_EXE}" -batchmode -nographics -projectPath . -executeMethod Game.Editor.Check_MissingReferences.RunBatch -logFile - || exit 1
fi
exit 0

"""Project configuration shared by the migration tools.

Create `Tools/migration.json` in the Unity project (next to the tools). Every key is optional; defaults match a project that uses
`Assets/_Game/Scripts/{Logic,Editor,Event}/<Prefix>/...`, a flat namespace and the game prefix `Game`:

{
  "prefix": "MyGame",                       # game prefix: classes become <prefix>_<Feature>_<Part>
  "namespace": "Game",            # namespace used for reflection strings and generated event classes
  "gameRoot": "Assets/_Game",            # mapping paths are relative to this folder
  "searchRoots": ["Assets/_Game"],       # folders scanned for identifiers (add embedded SDK folders if they reference your types)
  "runtimeFolder": "Scripts/Logic/MyGame",  # relative to gameRoot
  "editorFolder": "Scripts/Editor/MyGame",
  "eventFolder": "Scripts/Event/MyGame",
  "testsFolder": "Assets/_Game/Tests"
}
"""
import json
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'migration.json')
_raw = json.load(open(_path, encoding='utf-8')) if os.path.exists(_path) else {}

prefix = _raw.get('prefix', 'Game')
namespace = _raw.get('namespace', 'Game')
game_root = os.path.join(PROJECT_ROOT, *_raw.get('gameRoot', 'Assets/_Game').split('/'))
search_roots = [os.path.join(PROJECT_ROOT, *r.split('/')) for r in _raw.get('searchRoots', [_raw.get('gameRoot', 'Assets/_Game')])]
runtime_folder = _raw.get('runtimeFolder', 'Scripts/Logic/' + prefix)
editor_folder = _raw.get('editorFolder', 'Scripts/Editor/' + prefix)
event_folder = _raw.get('eventFolder', 'Scripts/Event/' + prefix)
tests_folder = os.path.join(PROJECT_ROOT, *_raw.get('testsFolder', 'Assets/_Game/Tests').split('/'))
source_interface = 'I%s_Source' % prefix
test_bus = '%s_TestBus' % prefix
event_prefix = 'Event_%s_' % prefix

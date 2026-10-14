import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "skills", "framework-version-map", "scripts"))

import framework_api_grep as grep_tool  # noqa: E402
import framework_inventory as inv  # noqa: E402


def write(root, rel, text):
    p = os.path.join(root, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(text)


class ApiGrepTests(unittest.TestCase):
    def test_detects_v1_and_v2(self):
        with tempfile.TemporaryDirectory() as r:
            write(r, "Packages/manifest.json", json.dumps({"dependencies": {"com.codesketch": "0.1.1"}}))
            self.assertEqual(grep_tool.detect(r)["framework"], "CodeSketch")
        with tempfile.TemporaryDirectory() as r:
            write(r, "Packages/manifest.json", json.dumps({"dependencies": {"com.sketchengine": "1.0.1"}}))
            self.assertEqual(grep_tool.detect(r)["framework"], "SketchEngine")

    def test_unknown_when_neither(self):
        with tempfile.TemporaryDirectory() as r:
            write(r, "Packages/manifest.json", json.dumps({"dependencies": {}}))
            self.assertIsNone(grep_tool.detect(r)["framework"])

    def test_resolves_package_cache_and_greps_symbol(self):
        with tempfile.TemporaryDirectory() as r:
            write(r, "Packages/manifest.json", json.dumps({"dependencies": {"com.sketchengine": "1.0.1"}}))
            write(r, "Library/PackageCache/com.sketchengine@abc/Runtime/Data/DataBlock.cs",
                  "public abstract class DataBlock<T>\n{\n  public static T INSTANCE;\n}\n")
            d = grep_tool.detect(r)
            self.assertTrue(d["package_dir"].endswith("com.sketchengine@abc"))
            hits = grep_tool.find_symbol(d["package_dir"], "INSTANCE")
            self.assertEqual(len(hits), 1)
            self.assertTrue(hits[0][0].endswith("DataBlock.cs"))
            self.assertEqual(hits[0][1], 3)

    def test_embedded_package_preferred(self):
        with tempfile.TemporaryDirectory() as r:
            write(r, "Packages/manifest.json", json.dumps({"dependencies": {"com.codesketch": "file:../x"}}))
            write(r, "Packages/com.codesketch/Runtime/A.cs", "class A {}\n")
            self.assertTrue(grep_tool.detect(r)["package_dir"].endswith("com.codesketch"))


class InventoryTests(unittest.TestCase):
    def project(self, r):
        write(r, "Assets/_Game/Scripts/Data/Data_Currency.cs",
              "namespace Game {\n public class Data_Currency : DataBlock<Data_Currency> {}\n}\n")
        write(r, "Assets/_Game/Scripts/Factory/Factory_Currency.cs",
              "namespace Game {\n public class Factory_Currency : ScriptableObjectSingleton<Factory_Currency> {}\n}\n")
        write(r, "Assets/_Game/Scripts/Factory/Factory_Audio.cs",
              "namespace Game {\n public class Factory_Audio : SerializedScriptableObjectSingleton<Factory_Audio> {}\n}\n")
        write(r, "Assets/_Game/Resources/CodeSketch/ScriptableObjectSingletons/Game.Factory_Audio.asset", "x")
        write(r, "Assets/_Game/Scripts/Boot.cs",
              "class B {\n [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]\n static void R(){}\n}\n")
        write(r, "Assets/_Game/Scripts/Ai.cs",
              "class Ai {\n void Awake(){ StaticBus<Event_X>.Subscribe(H); StaticBus<Event_Y>.Subscribe(H2); }\n"
              " void OnDestroy(){ StaticBus<Event_Y>.Unsubscribe(H2); }\n}\n")

    def test_inventory(self):
        with tempfile.TemporaryDirectory() as r:
            self.project(r)
            res = inv.scan(r)
            self.assertEqual([d["name"] for d in res["data_blocks"]], ["Game.Data_Currency"])
            names = {f["name"]: f for f in res["factories"]}
            self.assertFalse(names["Game.Factory_Currency"]["asset_exists"])
            self.assertTrue(names["Game.Factory_Audio"]["asset_exists"])
            self.assertEqual(res["init_hooks"][0]["stage"], "SubsystemRegistration")
            unbalanced = {u["event"] for u in res["unbalanced_bus"]}
            self.assertEqual(unbalanced, {"Event_X"})

    def test_library_and_packages_ignored(self):
        with tempfile.TemporaryDirectory() as r:
            write(r, "Library/PackageCache/p/Foo.cs", "class F : DataBlock<F> {}\n")
            write(r, "Packages/p/Bar.cs", "class F : DataBlock<F> {}\n")
            self.assertEqual(inv.scan(r)["data_blocks"], [])

    def test_main_exit_code_on_missing_asset(self):
        with tempfile.TemporaryDirectory() as r:
            self.project(r)
            self.assertEqual(inv.main([r]), 1)


if __name__ == "__main__":
    unittest.main()

import json
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
sys.path.insert(0, os.path.join(ROOT, "skills", "game-orchestrator", "scripts"))
import miniyaml  # noqa: E402

SKILLS = set(os.listdir(os.path.join(ROOT, "skills")))
ROSTER = {"orchestrator", "game-designer", "tech-lead", "gameplay-dev", "ui-dev", "art-tech", "economy-balancer", "qa-tester",
          "perf-auditor", "release-engineer", "reviewer"}
KNOWN_KEYS = {"name", "description", "tools", "disallowedTools", "model", "maxTurns", "skills", "memory", "isolation", "color", "effort"}
LEAVES = ROSTER - {"orchestrator"}


def frontmatter(path):
    with open(path, encoding="utf-8") as f:
        return miniyaml.split_front_matter(f.read())


class AgentTests(unittest.TestCase):
    def test_roster_complete(self):
        files = {f[:-3] for f in os.listdir(os.path.join(ROOT, "agents")) if f.endswith(".md")}
        self.assertEqual(files, ROSTER)

    def test_frontmatter_valid(self):
        for name in sorted(ROSTER):
            fm, body = frontmatter(os.path.join(ROOT, "agents", name + ".md"))
            self.assertEqual(fm["name"], name)
            self.assertTrue(set(fm) <= KNOWN_KEYS, (name, set(fm) - KNOWN_KEYS))
            self.assertGreater(len(fm["description"]), 40, name)
            self.assertLessEqual(len(fm["description"]), 600, name)
            self.assertIn(fm["model"], ("opus", "sonnet", "haiku", "fable", "inherit"), name)
            self.assertGreater(len(body.strip()), 100, name)

    def test_preloaded_skills_exist_and_are_few(self):
        for name in sorted(ROSTER):
            fm, _ = frontmatter(os.path.join(ROOT, "agents", name + ".md"))
            skills = fm.get("skills") or []
            self.assertLessEqual(len(skills), 4, "%s preloads too many skills" % name)
            for s in skills:
                self.assertIn(s, SKILLS, "%s preloads unknown skill %s" % (name, s))

    def test_leaves_cannot_spawn_agents(self):
        for name in sorted(LEAVES):
            fm, _ = frontmatter(os.path.join(ROOT, "agents", name + ".md"))
            self.assertNotIn("Agent", fm["tools"].replace("Agent(", "X("), name)
            self.assertIn("Agent", fm.get("disallowedTools", ""), name)

    def test_read_only_agents_have_no_write_tools(self):
        for name in ("qa-tester", "perf-auditor", "reviewer"):
            fm, _ = frontmatter(os.path.join(ROOT, "agents", name + ".md"))
            self.assertIn("Edit", fm["disallowedTools"], name)
            self.assertNotIn("Edit,", fm["tools"] + ",", name)

    def test_orchestrator_can_spawn_exactly_the_leaves(self):
        fm, _ = frontmatter(os.path.join(ROOT, "agents", "orchestrator.md"))
        m = re.search(r"Agent\(([^)]*)\)", fm["tools"])
        self.assertEqual({x.strip() for x in m.group(1).split(",")}, LEAVES)

    def test_every_agent_states_the_report_limit(self):
        for name in ROSTER:
            with open(os.path.join(ROOT, "agents", name + ".md"), encoding="utf-8") as f:
                self.assertIn("200 words", f.read(), name)


class CommandAndManifestTests(unittest.TestCase):
    def test_commands_have_description(self):
        names = [f for f in os.listdir(os.path.join(ROOT, "commands")) if f.endswith(".md")]
        self.assertGreaterEqual(len(names), 5)
        for n in names:
            fm, body = frontmatter(os.path.join(ROOT, "commands", n))
            self.assertTrue(fm.get("description"), n)
            self.assertGreater(len(body.strip()), 80, n)

    def test_command_skill_references_exist(self):
        for n in os.listdir(os.path.join(ROOT, "commands")):
            with open(os.path.join(ROOT, "commands", n), encoding="utf-8") as f:
                for s in re.findall(r"`([a-z][a-z0-9-]+)` skill", f.read()):
                    self.assertIn(s, SKILLS, "%s -> %s" % (n, s))

    def test_plugin_manifest(self):
        with open(os.path.join(ROOT, ".claude-plugin", "plugin.json"), encoding="utf-8") as f:
            m = json.load(f)
        self.assertEqual(m["name"], "unity-game-pipeline")
        self.assertRegex(m["version"], r"^\d+\.\d+\.\d+$")
        self.assertTrue(m["description"])
        # components live at the plugin root, never inside .claude-plugin/
        self.assertEqual(sorted(os.listdir(os.path.join(ROOT, ".claude-plugin"))), ["plugin.json"])
        for d in ("skills", "agents", "commands", "hooks"):
            self.assertTrue(os.path.isdir(os.path.join(ROOT, d)), d)


class InstallTests(unittest.TestCase):
    def test_hooks_snippet_has_no_plugin_variable_left(self):
        sys.path.insert(0, os.path.join(ROOT, "tools"))
        import install_hooks
        with open(os.path.join(ROOT, "hooks", "hooks.json"), encoding="utf-8") as f:
            data = json.load(f)
        out = json.dumps(install_hooks.convert(data, r"C:\Users\x\.claude\pipeline-hooks"))
        self.assertNotIn("CLAUDE_PLUGIN_ROOT", out)
        self.assertIn("C:/Users/x/.claude/pipeline-hooks/hooks/scripts/stop_gate.py", out)


class ListingBudgetTests(unittest.TestCase):
    def test_hubs_fit_a_200k_context_and_keep_clone_entrypoints(self):
        sys.path.insert(0, os.path.join(ROOT, "tools"))
        import skill_budget
        skills = skill_budget.read_skills(os.path.join(ROOT, "skills"))
        hubs = skill_budget.read_hubs(os.path.join(ROOT, "tools", "hubs.txt"))
        hub_chars, rest_names, _ = skill_budget.cost(skills, hubs)
        budget_200k = 200000 * skill_budget.CHARS_PER_TOKEN * 0.01

        self.assertLessEqual(hub_chars + rest_names, budget_200k)
        self.assertTrue({"game-orchestrator", "gdd-intake", "clone-pipeline", "unity-mcp-workflow",
                         "qa-fix-retest-loop", "new-game-bootstrap"}.issubset(hubs))

    def test_hubs_exist_and_fit_a_large_context(self):
        sys.path.insert(0, os.path.join(ROOT, "tools"))
        import skill_budget
        skills = skill_budget.read_skills(os.path.join(ROOT, "skills"))
        hubs = skill_budget.read_hubs(os.path.join(ROOT, "tools", "hubs.txt"))
        self.assertEqual([h for h in hubs if h not in skills], [])
        self.assertLessEqual(len(hubs), 45)
        hub_chars, rest_names, _ = skill_budget.cost(skills, hubs)
        budget_1m = 1000000 * skill_budget.CHARS_PER_TOKEN * 0.01
        self.assertLess(hub_chars + rest_names, budget_1m * 0.5)


class LocalBatchTerminologyTests(unittest.TestCase):
    def test_qa_and_build_entrypoints_use_local_batch_names(self):
        self.assertTrue(os.path.isdir(os.path.join(ROOT, "skills", "qa-batch-and-fallbacks")))
        legacy_qa = "qa" + "-ci-and-fallbacks"
        legacy_workflow = "ci" + ".yml.template"
        self.assertFalse(os.path.exists(os.path.join(ROOT, "skills", legacy_qa)))
        self.assertFalse(os.path.exists(os.path.join(ROOT, "skills", "unity-batch-build", "assets", legacy_workflow)))
        self.assertTrue(os.path.isfile(os.path.join(ROOT, "skills", "unity-batch-build", "assets", "local-build.ps1.template")))
        self.assertFalse(os.path.exists(os.path.join(ROOT, "skills", "unity-batch-build", "assets", "here sync installed the skills; scripts are stdlib Python#")))


if __name__ == "__main__":
    unittest.main()

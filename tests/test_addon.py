from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class Hook(list):
    pass


class AddonManager:
    def __init__(self) -> None:
        self.config = {}
        self.exports = None
        self.config_action = None
        self.updated_action = None
        self.get_config_calls = 0

    def getConfig(self, _module):
        self.get_config_calls += 1
        return self.config

    def addonFromModule(self, _module):
        return "961932796"

    def setWebExports(self, module, pattern):
        self.exports = (module, pattern)

    def setConfigAction(self, module, action):
        self.config_action = (module, action)

    def setConfigUpdatedAction(self, module, action):
        self.updated_action = (module, action)


class Timer:
    calls = []

    @classmethod
    def singleShot(cls, delay, callback):
        cls.calls.append(delay)
        callback()


class WebContent:
    def __init__(self):
        self.js = []


class WebView:
    def __init__(self):
        self.scripts = []

    def eval(self, script):
        self.scripts.append(script)


def load_addon():
    manager = AddonManager()
    hooks = types.SimpleNamespace(
        webview_will_set_content=Hook(),
        reviewer_did_answer_card=Hook(),
    )
    aqt = types.ModuleType("aqt")
    aqt.gui_hooks = hooks
    aqt.mw = types.SimpleNamespace(addonManager=manager)
    qt = types.ModuleType("aqt.qt")
    qt.QTimer = Timer
    webview = types.ModuleType("aqt.webview")
    webview.WebContent = WebContent
    sys.modules.update({"aqt": aqt, "aqt.qt": qt, "aqt.webview": webview})

    spec = importlib.util.spec_from_file_location("confetti_addon", ROOT / "__init__.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module, manager, hooks


addon, manager, hooks = load_addon()


class SettingsTests(unittest.TestCase):
    def test_defaults_are_safe(self):
        settings = addon.Settings.from_mapping({})
        self.assertTrue(settings.matches(addon.AGAIN))
        self.assertTrue(settings.matches(addon.GOOD))
        self.assertFalse(settings.matches(addon.HARD))
        self.assertEqual(settings.preset, "button_cannon")
        self.assertEqual(settings.intensity, 100)
        self.assertEqual(settings.origin_mode, "center")
        self.assertEqual(settings.shape, "squares")
        self.assertEqual(settings.emoji, "🎉")
        self.assertEqual(settings.again_emoji, "👎")
        self.assertEqual(settings.spread, 100)
        self.assertFalse(settings.respect_reduced_motion)

    def test_invalid_values_are_normalized_and_bounded(self):
        settings = addon.Settings.from_mapping(
            {
                "enabled": "false",
                "preset": "unknown",
                "colors": ["bad", "#ABCDEF"],
                "intensity": 999,
                "duration_ms": -1,
                "delay_ms": "bad",
                "origin_mode": "unknown",
                "shape": "triangles",
                "emoji": "",
                "again_emoji": 42,
                "spread": 999,
            }
        )
        self.assertFalse(settings.enabled)
        self.assertEqual(settings.preset, "button_cannon")
        self.assertEqual(settings.colors, ("#abcdef",))
        self.assertEqual(settings.intensity, 200)
        self.assertEqual(settings.duration_ms, 400)
        self.assertEqual(settings.delay_ms, 80)
        self.assertEqual(settings.origin_mode, "center")
        self.assertEqual(settings.shape, "squares")
        self.assertEqual(settings.emoji, "🎉")
        self.assertEqual(settings.again_emoji, "👎")
        self.assertEqual(settings.spread, 360)

    def test_legacy_palette_and_option_names_are_migrated(self):
        settings = addon.Settings.from_mapping(
            {
                "palette": "pastel",
                "colors": ["#000000"],
                "particle_multiplier": 141,
                "intensity": 25,
                "trigger_delay_ms": 0,
                "delay_ms": 500,
                "origin_mode": "center",
                "shape": "squares",
                "spread": 146,
            }
        )
        self.assertEqual(settings.colors, addon.PALETTES["pastel"])
        self.assertEqual(settings.intensity, 141)
        self.assertEqual(settings.delay_ms, 0)
        self.assertEqual(settings.origin_mode, "center")
        self.assertEqual(settings.shape, "squares")
        self.assertEqual(settings.spread, 146)

    def test_payload_contains_rendering_choices(self):
        settings = addon.Settings.from_mapping(
            {
                "origin_mode": "custom",
                "custom_origin_x": 25,
                "custom_origin_y": 75,
                "shape": "circles",
                "emoji": "✨",
                "again_emoji": "😭",
                "spread": 180,
            }
        )
        payload = settings.payload(addon.GOOD)
        self.assertEqual(payload["originMode"], "custom")
        self.assertEqual(payload["customOrigin"], {"x": 0.25, "y": 0.75})
        self.assertEqual(payload["shape"], "circles")
        self.assertEqual(payload["emoji"], "✨")
        self.assertEqual(payload["againEmoji"], "😭")
        self.assertEqual(payload["spread"], 180)

    def test_canonical_config_drops_legacy_bloat(self):
        settings = addon.Settings.from_mapping(
            {
                "palette": "pastel",
                "particle_multiplier": 141,
                "trigger_delay_ms": 0,
                "emoji": "✨",
                "again_emoji": "😭",
                "spread": 180,
            }
        )
        config = settings.to_mapping()
        self.assertEqual(config["colors"], list(addon.PALETTES["pastel"]))
        self.assertEqual(config["intensity"], 141)
        self.assertEqual(config["delay_ms"], 0)
        self.assertEqual(config["spread"], 180)
        self.assertEqual(config["emoji"], "✨")
        self.assertEqual(config["again_emoji"], "😭")
        self.assertNotIn("palette", config)
        self.assertNotIn("particle_multiplier", config)


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        manager.config = {}
        addon._update_settings(manager.config)
        Timer.calls.clear()

    def test_only_reviewer_receives_assets(self):
        Reviewer = type("Reviewer", (), {})
        Reviewer.__module__ = "aqt.reviewer"
        content = WebContent()
        addon._add_assets(content, Reviewer())
        self.assertEqual(
            content.js,
            [
                "/_addons/961932796/web/canvas-confetti.browser.min.js",
                "/_addons/961932796/web/confetti.js",
            ],
        )

        other = WebContent()
        addon._add_assets(other, object())
        self.assertEqual(other.js, [])

    def test_good_answer_schedules_compact_payload(self):
        web = WebView()
        addon._answered(types.SimpleNamespace(web=web), object(), addon.GOOD)
        self.assertEqual(Timer.calls, [80])
        self.assertEqual(len(web.scripts), 1)
        self.assertIn("window.ankiConfetti?.fire(", web.scripts[0])
        self.assertNotIn(" ", web.scripts[0])

    def test_again_answer_triggers_by_default(self):
        web = WebView()
        addon._answered(types.SimpleNamespace(web=web), object(), addon.AGAIN)
        self.assertEqual(Timer.calls, [80])
        self.assertEqual(len(web.scripts), 1)

    def test_hard_answer_does_nothing_by_default(self):
        web = WebView()
        addon._answered(types.SimpleNamespace(web=web), object(), addon.HARD)
        self.assertEqual(Timer.calls, [])
        self.assertEqual(web.scripts, [])

    def test_saved_config_refreshes_cached_settings(self):
        manager.updated_action[1]({"trigger_good": False})
        web = WebView()
        addon._answered(types.SimpleNamespace(web=web), object(), addon.GOOD)
        self.assertEqual(web.scripts, [])

    def test_answering_does_not_reread_config_files(self):
        calls = manager.get_config_calls
        web = WebView()
        addon._answered(types.SimpleNamespace(web=web), object(), addon.GOOD)
        addon._answered(types.SimpleNamespace(web=web), object(), addon.AGAIN)
        self.assertEqual(manager.get_config_calls, calls)

    def test_hooks_and_exports_are_registered(self):
        self.assertIn(addon._add_assets, hooks.webview_will_set_content)
        self.assertIn(addon._answered, hooks.reviewer_did_answer_card)
        self.assertEqual(manager.exports[1], r"web/.*\.js")
        self.assertIs(manager.config_action[1], addon._open_settings)
        self.assertIs(manager.updated_action[1], addon._update_settings)


if __name__ == "__main__":
    unittest.main()

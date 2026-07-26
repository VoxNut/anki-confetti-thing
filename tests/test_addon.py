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

    def getConfig(self, _module):
        return self.config

    def addonFromModule(self, _module):
        return "961932796"

    def setWebExports(self, module, pattern):
        self.exports = (module, pattern)


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
        self.assertTrue(settings.matches(addon.GOOD))
        self.assertEqual(settings.preset, "button_cannon")
        self.assertEqual(settings.intensity, 100)

    def test_invalid_values_are_normalized_and_bounded(self):
        settings = addon.Settings.from_mapping(
            {
                "enabled": "false",
                "preset": "unknown",
                "colors": ["bad", "#ABCDEF"],
                "intensity": 999,
                "duration_ms": -1,
                "delay_ms": "bad",
            }
        )
        self.assertFalse(settings.enabled)
        self.assertEqual(settings.preset, "button_cannon")
        self.assertEqual(settings.colors, ("#abcdef",))
        self.assertEqual(settings.intensity, 200)
        self.assertEqual(settings.duration_ms, 400)
        self.assertEqual(settings.delay_ms, 80)

    def test_legacy_palette_and_option_names_are_migrated(self):
        settings = addon.Settings.from_mapping(
            {
                "palette": "pastel",
                "particle_multiplier": 141,
                "trigger_delay_ms": 0,
            }
        )
        self.assertEqual(settings.colors, addon.PALETTES["pastel"])
        self.assertEqual(settings.intensity, 141)
        self.assertEqual(settings.delay_ms, 0)


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        manager.config = {}
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

    def test_again_answer_does_nothing(self):
        web = WebView()
        addon._answered(types.SimpleNamespace(web=web), object(), 1)
        self.assertEqual(Timer.calls, [])
        self.assertEqual(web.scripts, [])

    def test_hooks_and_exports_are_registered(self):
        self.assertIn(addon._add_assets, hooks.webview_will_set_content)
        self.assertIn(addon._answered, hooks.reviewer_did_answer_card)
        self.assertEqual(manager.exports[1], r"web/.*\.js")


if __name__ == "__main__":
    unittest.main()

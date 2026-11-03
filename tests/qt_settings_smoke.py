"""Manual smoke test for the native settings dialog using Anki's Qt runtime."""

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication, QDialogButtonBox, QWidget
from qt_support import load_addon


ROOT = Path(__file__).parents[1]


class AddonManager:
    def __init__(self) -> None:
        self.written = None

    def getConfig(self, _module):
        return {
            "preset": "stars",
            "origin_mode": "center",
            "shape": "squares",
            "spread": 146,
        }

    def addonFromModule(self, module):
        return module.split(".")[0]

    def setWebExports(self, _module, _pattern):
        pass

    def setConfigAction(self, _module, _action):
        pass

    def setConfigUpdatedAction(self, _module, _action):
        pass

    def writeConfig(self, module, config):
        self.written = (module, config)


app = QApplication.instance() or QApplication(sys.argv)
manager = AddonManager()
addon = load_addon(manager)
settings_module = importlib.import_module(f"{ROOT.name}.settings")
settings_module.tooltip = lambda *_args, **_kwargs: None

host = QWidget()
dialog = settings_module.ConfettiSettingsDialog(host)
assert dialog.spread.value() == 146
assert dialog.preview_good.isEnabled()
assert not dialog.emoji.isEnabled()
dialog.spread.setValue(220)
dialog.again_emoji.setText("😭")
dialog.emoji_size.setValue(230)
dialog.shape.setCurrentIndex(dialog.shape.findData("emoji"))
dialog.emoji.setText("✨")
assert dialog.emoji.isEnabled()
dialog.preview_good.click()
overlay = dialog.preview._confetti_overlay
assert overlay.timer.isActive()
assert all(p.shape == "emoji" for p in overlay.particles)
assert overlay._emoji_key[0] == "✨"
dialog.preview_again.click()
assert dialog.preview._confetti_overlay is overlay
assert overlay._emoji_key[0] == "😭"
assert abs(overlay.particles[0].size - 41.4) < .01

button_box = dialog.findChild(QDialogButtonBox)
button_box.button(QDialogButtonBox.StandardButton.Save).click()
assert manager.written is not None
assert manager.written[1]["spread"] == 220
assert manager.written[1]["again_emoji"] == "😭"
assert manager.written[1]["emoji_size"] == 230
assert manager.written[1]["shape"] == "emoji"
assert manager.written[1]["emoji"] == "✨"
assert manager.written[1]["origin_mode"] == "center"

dialog.close()
app.processEvents()
assert not overlay.timer.isActive()
print("settings dialog smoke test passed")

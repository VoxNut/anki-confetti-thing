"""Compact, lazily loaded settings UI."""

from __future__ import annotations

from typing import Any

from aqt import mw
from aqt.qt import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)
from aqt.utils import qconnect, tooltip
from aqt.webview import AnkiWebView

from . import AGAIN, GOOD, Settings, _asset_urls, _fire, _update_settings

PRESET_LABELS = {
    "button_cannon": "Button cannon",
    "simple_burst": "Simple burst",
    "realistic_burst": "Realistic burst",
    "fireworks": "Fireworks",
    "stars": "Stars",
    "side_cannons": "Side cannons",
}
ORIGIN_LABELS = {
    "center": "Center",
    "answer_button": "Answer button",
    "top": "Top",
    "bottom": "Bottom",
    "left": "Left",
    "right": "Right",
    "custom": "Custom",
}
SHAPE_LABELS = {
    "squares": "Squares",
    "circles": "Circles",
    "mixed": "Mixed",
    "stars": "Stars",
    "preset": "Preset default",
}


def _select(combo: QComboBox, value: str) -> None:
    index = combo.findData(value)
    if index >= 0:
        combo.setCurrentIndex(index)


def _spin(
    parent: QWidget,
    minimum: int,
    maximum: int,
    value: int,
    suffix: str = "",
) -> QSpinBox:
    spin = QSpinBox(parent)
    spin.setRange(minimum, maximum)
    spin.setValue(value)
    if suffix:
        spin.setSuffix(suffix)
    return spin


class ConfettiSettingsDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent or mw)
        self.setWindowTitle("Tiramisu's Confetti Thing")
        self.resize(760, 760)
        current = Settings.load()

        root = QVBoxLayout(self)
        intro = QLabel(
            "Adjust the controls, then preview immediately. Preview does not "
            "require saving.",
            self,
        )
        intro.setWordWrap(True)
        root.addWidget(intro)

        self.preview = AnkiWebView(self)
        self.preview.setMinimumHeight(280)
        self.preview.requiresCol = False
        root.addWidget(self.preview, 1)

        form = QFormLayout()
        root.addLayout(form)

        self.enabled = QCheckBox("Enable confetti", self)
        self.enabled.setChecked(current.enabled)
        form.addRow("", self.enabled)

        triggers = QHBoxLayout()
        self.trigger_again = QCheckBox("Again", self)
        self.trigger_hard = QCheckBox("Hard", self)
        self.trigger_good = QCheckBox("Good", self)
        self.trigger_easy = QCheckBox("Easy", self)
        for box, checked in (
            (self.trigger_again, current.trigger_again),
            (self.trigger_hard, current.trigger_hard),
            (self.trigger_good, current.trigger_good),
            (self.trigger_easy, current.trigger_easy),
        ):
            box.setChecked(checked)
            triggers.addWidget(box)
        triggers.addStretch(1)
        form.addRow("Triggers", triggers)

        self.preset = QComboBox(self)
        for key, label in PRESET_LABELS.items():
            self.preset.addItem(label, key)
        _select(self.preset, current.preset)
        form.addRow("Preset", self.preset)

        self.origin = QComboBox(self)
        for key, label in ORIGIN_LABELS.items():
            self.origin.addItem(label, key)
        _select(self.origin, current.origin_mode)
        form.addRow("Origin", self.origin)

        custom_origin = QHBoxLayout()
        self.origin_x = _spin(self, 0, 100, current.custom_origin_x, "% X")
        self.origin_y = _spin(self, 0, 100, current.custom_origin_y, "% Y")
        custom_origin.addWidget(self.origin_x)
        custom_origin.addWidget(self.origin_y)
        form.addRow("Custom origin", custom_origin)
        qconnect(self.origin.currentIndexChanged, self._refresh_origin_controls)

        self.shape = QComboBox(self)
        for key, label in SHAPE_LABELS.items():
            self.shape.addItem(label, key)
        _select(self.shape, current.shape)
        form.addRow("Shape", self.shape)

        self.colors = QLineEdit(", ".join(current.colors), self)
        self.colors.setPlaceholderText("#ff0000, #00ff00, #0000ff")
        form.addRow("Colors", self.colors)

        self.intensity = _spin(self, 25, 200, current.intensity, "%")
        form.addRow("Intensity", self.intensity)

        self.spread = _spin(self, 10, 360, current.spread, "°")
        self.spread.setSingleStep(10)
        self.spread.setToolTip(
            "Launch width in degrees: 10 is narrow, 180 is wide, "
            "and 360 is a full circle."
        )
        form.addRow("Spread", self.spread)

        self.duration = _spin(self, 400, 4000, current.duration_ms, " ms")
        self.duration.setSingleStep(100)
        form.addRow("Fireworks duration", self.duration)

        self.delay = _spin(self, 0, 500, current.delay_ms, " ms")
        self.delay.setSingleStep(10)
        form.addRow("Review delay", self.delay)

        runtime = QHBoxLayout()
        self.reduced_motion = QCheckBox("Respect reduced motion", self)
        self.reduced_motion.setChecked(current.respect_reduced_motion)
        self.worker = QCheckBox("Use rendering worker", self)
        self.worker.setChecked(current.use_worker)
        runtime.addWidget(self.reduced_motion)
        runtime.addWidget(self.worker)
        runtime.addStretch(1)
        form.addRow("Runtime", runtime)

        preview_buttons = QHBoxLayout()
        self.preview_again = QPushButton("Preview Again 👎", self)
        self.preview_good = QPushButton("Preview Good", self)
        self.preview_again.setEnabled(False)
        self.preview_good.setEnabled(False)
        qconnect(self.preview_again.clicked, lambda: self._preview(AGAIN))
        qconnect(self.preview_good.clicked, lambda: self._preview(GOOD))
        preview_buttons.addStretch(1)
        preview_buttons.addWidget(self.preview_again)
        preview_buttons.addWidget(self.preview_good)
        root.addLayout(preview_buttons)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Close,
            parent=self,
        )
        qconnect(buttons.accepted, self._save)
        qconnect(buttons.rejected, self.close)
        root.addWidget(buttons)

        qconnect(self.preview.loadFinished, self._preview_loaded)
        self.preview.stdHtml(
            """
            <main>
              <div>Live preview</div>
              <small>Adjust settings below, then choose a preview button.</small>
            </main>
            """,
            js=list(_asset_urls()),
            head="""
            <style>
              html, body { height: 100%; margin: 0; overflow: hidden; }
              body {
                display: grid; place-items: center;
                background: #11151b; color: #e8eaed;
                font-family: system-ui, sans-serif;
              }
              main { text-align: center; font-size: 24px; }
              small { color: #9aa0a6; font-size: 13px; }
            </style>
            """,
            context=None,
            default_css=False,
        )
        self._refresh_origin_controls()

    def _preview_loaded(self, ok: bool) -> None:
        self.preview_again.setEnabled(ok)
        self.preview_good.setEnabled(ok)

    def _refresh_origin_controls(self, *_args: Any) -> None:
        enabled = self.origin.currentData() == "custom"
        self.origin_x.setEnabled(enabled)
        self.origin_y.setEnabled(enabled)

    def _current(self) -> Settings:
        colors = self.colors.text().replace(";", ",").split(",")
        return Settings.from_mapping(
            {
                "enabled": self.enabled.isChecked(),
                "trigger_again": self.trigger_again.isChecked(),
                "trigger_hard": self.trigger_hard.isChecked(),
                "trigger_good": self.trigger_good.isChecked(),
                "trigger_easy": self.trigger_easy.isChecked(),
                "preset": self.preset.currentData(),
                "origin_mode": self.origin.currentData(),
                "custom_origin_x": self.origin_x.value(),
                "custom_origin_y": self.origin_y.value(),
                "shape": self.shape.currentData(),
                "colors": [color.strip() for color in colors],
                "intensity": self.intensity.value(),
                "spread": self.spread.value(),
                "duration_ms": self.duration.value(),
                "delay_ms": self.delay.value(),
                "respect_reduced_motion": self.reduced_motion.isChecked(),
                "use_worker": self.worker.isChecked(),
            }
        )

    def _preview(self, ease: int) -> None:
        _fire(self.preview, self._current().payload(ease))

    def _save(self) -> None:
        settings = self._current()
        config = settings.to_mapping()
        mw.addonManager.writeConfig(__package__, config)
        _update_settings(config)
        tooltip("Confetti settings saved.", parent=self)

    def closeEvent(self, event: Any) -> None:
        self.preview.cleanup()
        super().closeEvent(event)

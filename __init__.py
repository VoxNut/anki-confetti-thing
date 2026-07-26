"""Fast, low-overhead confetti for Anki reviews."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Mapping

from aqt import gui_hooks, mw
from aqt.qt import QTimer
from aqt.webview import WebContent

GOOD = 3
EASY = 4
PRESETS = frozenset(
    {
        "button_cannon",
        "simple_burst",
        "realistic_burst",
        "fireworks",
        "stars",
        "side_cannons",
    }
)
PALETTES = {
    "tiramisu": ("#f6bd60", "#f7ede2", "#f5cac3", "#84a59d", "#8d5524"),
    "anki": ("#2f7de1", "#45b7d1", "#ffffff", "#ffcd56", "#4bc0c0"),
    "rainbow": ("#f94144", "#f3722c", "#f9c74f", "#90be6d", "#43aa8b", "#577590"),
    "pastel": ("#ffadad", "#ffd6a5", "#fdffb6", "#caffbf", "#9bf6ff", "#bdb2ff"),
    "mochi": ("#ef476f", "#ffd166", "#06d6a0", "#118ab2", "#f8f9fa"),
}
DEFAULT_COLORS = PALETTES["tiramisu"]
HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$").fullmatch


def _boolean(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        if value.lower() in {"true", "yes", "on", "1"}:
            return True
        if value.lower() in {"false", "no", "off", "0"}:
            return False
    return default


def _integer(value: Any, default: int, minimum: int, maximum: int) -> int:
    try:
        return max(minimum, min(maximum, int(value)))
    except (TypeError, ValueError):
        return default


def _colors(config: Mapping[str, Any]) -> tuple[str, ...]:
    value = config.get("colors")
    if value is None:
        palette = str(config.get("palette", "tiramisu"))
        value = (
            config.get("custom_colors")
            if palette == "custom"
            else PALETTES.get(palette, DEFAULT_COLORS)
        )
    if not isinstance(value, (list, tuple)):
        return DEFAULT_COLORS
    valid = tuple(str(color).lower() for color in value if HEX_COLOR(str(color)))
    return valid[:12] or DEFAULT_COLORS


@dataclass(frozen=True, slots=True)
class Settings:
    enabled: bool
    trigger_good: bool
    trigger_easy: bool
    preset: str
    colors: tuple[str, ...]
    intensity: int
    duration_ms: int
    delay_ms: int
    respect_reduced_motion: bool
    use_worker: bool

    @classmethod
    def load(cls) -> "Settings":
        return cls.from_mapping(mw.addonManager.getConfig(__name__) or {})

    @classmethod
    def from_mapping(cls, config: Mapping[str, Any]) -> "Settings":
        preset = str(config.get("preset", "button_cannon"))
        if preset not in PRESETS:
            preset = "button_cannon"
        return cls(
            enabled=_boolean(config.get("enabled"), True),
            trigger_good=_boolean(config.get("trigger_good"), True),
            trigger_easy=_boolean(config.get("trigger_easy"), True),
            preset=preset,
            colors=_colors(config),
            intensity=_integer(
                config.get("intensity", config.get("particle_multiplier")),
                100,
                25,
                200,
            ),
            duration_ms=_integer(config.get("duration_ms"), 1600, 400, 4000),
            delay_ms=_integer(
                config.get("delay_ms", config.get("trigger_delay_ms")),
                80,
                0,
                500,
            ),
            respect_reduced_motion=_boolean(
                config.get("respect_reduced_motion"), True
            ),
            use_worker=_boolean(config.get("use_worker"), True),
        )

    def matches(self, ease: int) -> bool:
        return self.enabled and (
            (ease == GOOD and self.trigger_good)
            or (ease == EASY and self.trigger_easy)
        )

    def payload(self, ease: int) -> dict[str, Any]:
        return {
            "ease": ease,
            "preset": self.preset,
            "colors": self.colors,
            "intensity": self.intensity,
            "duration": self.duration_ms,
            "reducedMotion": self.respect_reduced_motion,
            "worker": self.use_worker,
        }


def _is_reviewer(context: object | None) -> bool:
    if context is None:
        return False
    kind = type(context)
    return kind.__module__ == "aqt.reviewer" and kind.__name__ == "Reviewer"


def _add_assets(web_content: WebContent, context: object | None) -> None:
    if not _is_reviewer(context):
        return
    package = mw.addonManager.addonFromModule(__name__)
    root = f"/_addons/{package}/web"
    web_content.js.extend(
        (f"{root}/canvas-confetti.browser.min.js", f"{root}/confetti.js")
    )


def _fire(webview: Any, payload: Mapping[str, Any]) -> None:
    try:
        encoded = json.dumps(payload, separators=(",", ":"))
        webview.eval(f"window.ankiConfetti?.fire({encoded})")
    except RuntimeError:
        # The reviewer can be destroyed while a delayed callback is pending.
        pass


def _answered(reviewer: Any, _card: Any, ease: int) -> None:
    settings = Settings.load()
    if not settings.matches(ease):
        return
    webview = getattr(reviewer, "web", None)
    if webview is None:
        return
    payload = settings.payload(ease)
    if settings.delay_ms:
        QTimer.singleShot(
            settings.delay_ms,
            lambda view=webview, data=payload: _fire(view, data),
        )
    else:
        _fire(webview, payload)


mw.addonManager.setWebExports(__name__, r"web/.*\.js")
gui_hooks.webview_will_set_content.append(_add_assets)
gui_hooks.reviewer_did_answer_card.append(_answered)

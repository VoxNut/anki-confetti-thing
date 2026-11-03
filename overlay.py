"""Native, click-through confetti; no work runs in the card's web renderer."""

from __future__ import annotations

import math
import sys
import time
from typing import Any, Mapping

from aqt.qt import (
    QApplication, QColor, QEvent, QFont, QPainter, QPixmap, QPointF,
    QPolygonF, QRectF, Qt, QTimer, QWidget,
)

from .particles import make_particles


def reduced_motion() -> bool:
    if sys.platform == "win32":
        import ctypes
        enabled = ctypes.c_int(1)
        if ctypes.windll.user32.SystemParametersInfoW(0x1042, 0, ctypes.byref(enabled), 0):
            return not enabled.value
    return not QApplication.isEffectEnabled(Qt.UIEffect.UI_AnimateCombo)


class ConfettiOverlay(QWidget):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAutoFillBackground(False)
        self.setStyleSheet("background: transparent; border: none;")
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setGeometry(parent.rect())
        parent.installEventFilter(self)
        self.timer = QTimer(self)
        self.timer.setTimerType(Qt.TimerType.PreciseTimer)
        self.timer.timeout.connect(self._tick)
        self.particles = []
        self.started = 0.0
        self.colors: dict[str, QColor] = {}
        self.emoji: QPixmap | None = None
        self._emoji_key = None
        self._star = QPolygonF([
            QPointF(math.cos(-math.pi / 2 + index * math.pi / 5) * (1 if index % 2 == 0 else .45),
                    math.sin(-math.pi / 2 + index * math.pi / 5) * (1 if index % 2 == 0 else .45))
            for index in range(10)
        ])
        self.hide()

    def start(self, payload: Mapping[str, Any], delay_ms: int = 0) -> None:
        self.stop()
        if payload.get("reducedMotion") and reduced_motion():
            return
        self.particles = make_particles(payload)
        self.colors = {particle.color: QColor(particle.color) for particle in self.particles}
        if any(particle.shape == "emoji" for particle in self.particles):
            text = payload.get("againEmoji", "👎") if payload.get("ease") == 1 else payload.get("emoji", "🎉")
            size = self.particles[0].size
            dpr = self.devicePixelRatioF()
            key = (text, size, dpr)
            if key != self._emoji_key:
                self.emoji = QPixmap(math.ceil(size * dpr * 1.4), math.ceil(size * dpr * 1.4))
                self.emoji.setDevicePixelRatio(dpr)
                self.emoji.fill(Qt.GlobalColor.transparent)
                painter = QPainter(self.emoji)
                font = QFont("Segoe UI Emoji")
                font.setPixelSize(round(size))
                painter.setFont(font)
                painter.drawText(QRectF(0, 0, size * 1.4, size * 1.4), Qt.AlignmentFlag.AlignCenter, text)
                painter.end()
                self._emoji_key = key
        self.started = time.perf_counter() + max(0, min(500, delay_ms)) / 1000
        refresh = self.screen().refreshRate() if self.screen() else 60
        self.timer.start(round(1000 / max(60, min(120, refresh))))

    def stop(self) -> None:
        self.timer.stop()
        self.particles = []
        self.hide()

    def eventFilter(self, watched: Any, event: Any) -> bool:
        if watched is self.parentWidget():
            if event.type() == QEvent.Type.Resize:
                self.setGeometry(watched.rect())
            elif event.type() == QEvent.Type.Hide:
                self.stop()
        return False

    def _tick(self) -> None:
        elapsed = time.perf_counter() - self.started
        if elapsed < 0:
            return
        self.particles = [particle for particle in self.particles if elapsed < particle.born + particle.life]
        if not self.particles:
            self.stop()
            return
        if not self.isVisible():
            self.setGeometry(self.parentWidget().rect())
            self.show()
            self.raise_()
        self.update()

    def paintEvent(self, event: Any) -> None:
        elapsed = time.perf_counter() - self.started
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.setPen(Qt.PenStyle.NoPen)
        width, height = self.width(), self.height()
        for particle in self.particles:
            age = elapsed - particle.born
            if not 0 <= age < particle.life:
                continue
            x, y = particle.position(age, width, height)
            if x < -100 or x > width + 100 or y > height + 100:
                continue
            painter.save()
            painter.setOpacity(min(1, (particle.life - age) / .7))
            painter.translate(x, y)
            painter.rotate(math.degrees(particle.phase) + age * particle.spin)
            size = particle.size
            if particle.shape == "emoji" and self.emoji is not None:
                side = self.emoji.width() / self.emoji.devicePixelRatioF()
                painter.drawPixmap(QPointF(-side / 2, -side / 2), self.emoji)
            else:
                painter.setBrush(self.colors[particle.color])
                painter.scale(size / 2, size / 2 * max(.15, abs(math.cos(particle.phase + age * 7))))
                if particle.shape == "circle":
                    painter.drawEllipse(QRectF(-1, -1, 2, 2))
                elif particle.shape == "star":
                    painter.drawPolygon(self._star)
                else:
                    painter.drawRect(QRectF(-1, -1, 2, 2))
            painter.restore()
        painter.end()


def show_confetti(parent: QWidget, payload: Mapping[str, Any], delay_ms: int = 0) -> None:
    overlay = getattr(parent, "_confetti_overlay", None)
    if overlay is None:
        overlay = ConfettiOverlay(parent)
        parent._confetti_overlay = overlay
    overlay.start(payload, delay_ms)


def stop_confetti(parent: QWidget) -> None:
    overlay = getattr(parent, "_confetti_overlay", None)
    if overlay is not None:
        overlay.stop()

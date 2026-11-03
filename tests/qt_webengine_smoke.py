"""Manual smoke test using the same Qt WebEngine bundled with Anki."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from PyQt6.QtCore import QTimer, QUrl
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QApplication


ROOT = Path(__file__).parents[1]
app = QApplication(sys.argv)
view = QWebEngineView()
view.resize(800, 600)
view.show()

html = """
<!doctype html>
<html>
<head>
  <style>html, body { margin: 0; background: #202124; }</style>
  <script>
    window.workerCount = 0;
    window.Worker = new Proxy(Worker, {
      construct(target, args) { workerCount++; return new target(...args); }
    });
    window._queueAction = action => setTimeout(() => {
      document.body.dataset.cardReady = "true";
      action();
    }, 120);
  </script>
  <script src="web/canvas-confetti.browser.min.js"></script>
  <script src="web/confetti.js"></script>
</head>
<body></body>
</html>
"""
early_canvas_count = None


def finish() -> None:
    script = """({
      confetti: typeof window.confetti,
      controller: typeof window.ankiConfetti?.fire,
      canvases: document.querySelectorAll("canvas").length,
      workerCount,
      cardReady: document.body.dataset.cardReady === "true",
      reducedMotion: matchMedia("(prefers-reduced-motion: reduce)").matches,
      size: [
        document.querySelector("canvas")?.width || 0,
        document.querySelector("canvas")?.height || 0
      ]
    })"""

    def report(result: object) -> None:
        image = view.grab().toImage()
        changed_pixels = 0
        for y in range(0, image.height(), 2):
            for x in range(0, image.width(), 2):
                color = image.pixelColor(x, y)
                if (color.red(), color.green(), color.blue()) != (32, 33, 36):
                    changed_pixels += 1
        result["changedPixels"] = changed_pixels
        result["canvasesBeforeCardReady"] = early_canvas_count
        print(json.dumps(result, sort_keys=True))
        valid = (
            result["confetti"] == "function"
            and result["controller"] == "function"
            and result["canvases"] == 1
            and result["size"] == [800, 600]
            and result["changedPixels"] > 0
            and result["workerCount"] == 1
            and result["cardReady"]
            and early_canvas_count == 0
        )
        app.exit(0 if valid else 1)

    view.page().runJavaScript(script, report)


def loaded(ok: bool) -> None:
    if not ok:
        print("page failed to load", file=sys.stderr)
        app.exit(1)
        return
    view.page().runJavaScript(
        """window.ankiConfetti.afterCard({
          ease: 1,
          preset: "stars",
          colors: ["#ffffff", "#ff0000"],
          intensity: 100,
          duration: 800,
          originMode: "center",
          shape: "squares",
          emoji: "✨",
          againEmoji: "😭",
          emojiSize: 180,
          spread: 180,
          reducedMotion: false,
          worker: true
        })"""
    )
    def record_early(result: object) -> None:
        global early_canvas_count
        early_canvas_count = result

    QTimer.singleShot(40, lambda: view.page().runJavaScript(
        'document.querySelectorAll("canvas").length', record_early
    ))
    QTimer.singleShot(400, finish)


view.loadFinished.connect(loaded)
view.setHtml(html, QUrl.fromLocalFile(str(ROOT) + "/"))
QTimer.singleShot(5000, lambda: app.exit(2))
raise SystemExit(app.exec())

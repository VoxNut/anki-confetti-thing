"""Verify native animation keeps painting during a one-second web-renderer stall.

Use --senren to load a real Senren card through local AnkiConnect instead.
No review is graded and no collection data is modified.
"""

import hashlib
import importlib
import json
import os
import sys
import time
import urllib.request
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QTimer, QUrl, Qt
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QApplication
from qt_support import load_addon


def anki(action, **params):
    request = urllib.request.Request("http://127.0.0.1:8765", json.dumps(
        dict(action=action, version=6, params=params)).encode(), {"Content-Type":"application/json"})
    result = json.load(urllib.request.urlopen(request))
    if result["error"]:
        raise RuntimeError(result["error"])
    return result["result"]


app = QApplication(sys.argv)
manager = SimpleNamespace(getConfig=lambda module: {},
    setConfigAction=lambda *args: None, setConfigUpdatedAction=lambda *args: None)
addon = load_addon(manager)
renderer = importlib.import_module(f"{addon.__name__}.overlay")
view = QWebEngineView()
view.resize(960, 720)
view.show()
samples = []
started = 0
timer = QTimer()


def sample():
    image = view.grab().toImage()
    digest = hashlib.sha256(image.constBits().asstring(image.sizeInBytes())).hexdigest()
    samples.append((time.perf_counter() - started, digest))


def finish():
    timer.stop()
    blocked = [digest for at, digest in samples if .35 < at < 1.05]
    overlay = view._confetti_overlay
    assert len(blocked) >= 6, "Qt event loop stalled"
    assert len(set(blocked)) >= 6, "animation froze with the card's JavaScript"
    assert overlay.testAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
    assert overlay.geometry() == view.rect(), "overlay did not follow the resize"
    renderer.stop_confetti(view)
    assert not overlay.timer.isActive() and not overlay.isVisible()
    renderer.show_confetti(view, addon.Settings.from_mapping({}).payload(1))
    assert view._confetti_overlay is overlay, "a new overlay was allocated for each answer"
    assert overlay.emoji is not None, "Again emoji not cached"
    renderer.stop_confetti(view)
    for shape in ["squares", "circles", "stars", "mixed", "emoji", "preset"]:
        for preset in ["button_cannon", "simple_burst", "realistic_burst", "fireworks", "stars", "side_cannons"]:
            renderer.show_confetti(view, addon.Settings.from_mapping({"shape":shape,"preset":preset}).payload(3))
            overlay._tick()
            assert not view.grab().isNull()
    overlay.started -= 10
    overlay._tick()
    assert not overlay.timer.isActive(), "late frames prolonged the effect"
    renderer.show_confetti(view, addon.Settings.from_mapping({}).payload(3), 500)
    overlay._tick()
    assert not overlay.isVisible(), "configured delay was ignored"
    renderer.stop_confetti(view)
    renderer.reduced_motion = lambda: True
    renderer.show_confetti(view, {"reducedMotion":True})
    assert not overlay.timer.isActive(), "reduced motion preference ignored"
    print(json.dumps({"samplesWhilePageBlocked": len(blocked),
        "uniqueFramesWhilePageBlocked": len(set(blocked)),
        "clickThrough": True, "resizes": True, "reusesOverlay": True,
        "allPresetsAndShapes": True, "elapsedTimeExpiry": True}), flush=True)
    app.exit(0)


def loaded(ok):
    global started
    if not ok:
        app.exit(1)
        return
    started = time.perf_counter()
    payload = addon.Settings.from_mapping({"preset":"realistic_burst", "delay_ms":0}).payload(3)
    renderer.show_confetti(view, payload)
    timer.timeout.connect(sample)
    timer.start(40)
    QTimer.singleShot(200, lambda: view.page().runJavaScript(
        "window.busyUntil=performance.now()+1000;while(performance.now()<busyUntil){}"))
    QTimer.singleShot(1250, lambda: view.resize(700, 500))
    QTimer.singleShot(1500, finish)


html = '<html><body style="margin:0;background:#202124"></body></html>'
base = QUrl("about:blank")
if "--senren" in sys.argv:
    card_ids = anki("findCards", query="note:Senren+")
    card = anki("cardsInfo", cards=card_ids[:1])[0]
    html = '<html class="win"><head><script>window.pycmd=()=>{};</script></head><body class="card nightMode">' + card["answer"] + '</body></html>'
    from pathlib import Path
    base = QUrl.fromLocalFile(str(Path(anki("getMediaDirPath"))) + "/")
view.loadFinished.connect(loaded)
view.setHtml(html, base)
QTimer.singleShot(8000, lambda: app.exit(2))
raise SystemExit(app.exec())

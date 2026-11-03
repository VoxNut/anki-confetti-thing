"""Load the add-on with real Qt and a minimal Anki host for standalone checks."""

import importlib
import sys
import types
from pathlib import Path

from PyQt6 import QtCore, QtGui, QtWidgets


def load_addon(manager):
    root = Path(__file__).parents[1]
    aqt = types.ModuleType("aqt")
    aqt.mw = types.SimpleNamespace(addonManager=manager)
    aqt.gui_hooks = types.SimpleNamespace(reviewer_did_answer_card=[], reviewer_will_end=[])
    qt = types.ModuleType("aqt.qt")
    for source in [QtCore, QtGui, QtWidgets]:
        for name in dir(source):
            if not name.startswith("_"):
                setattr(qt, name, getattr(source, name))
    utils = types.ModuleType("aqt.utils")
    utils.qconnect = lambda signal, slot: signal.connect(slot)
    utils.tooltip = lambda *args, **kwargs: None
    sys.modules.update({"aqt": aqt, "aqt.qt": qt, "aqt.utils": utils})
    sys.path.insert(0, str(root.parent))
    return importlib.import_module(root.name)

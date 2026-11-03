# Tiramisu's Confetti Thing

A small, offline Anki add-on that celebrates `Again`, `Good`, and `Easy`
answers with confetti. Each answer can be enabled or disabled independently.

## Rendering

- Confetti is painted in a native Qt overlay, outside the card's web renderer.
  Card scripts, CSS, page replacement, and browser animation queues do not drive it.
- One click-through overlay is reused. It follows the review surface when resized
  and stops when reviewing ends or the surface is hidden.
- Particle positions use elapsed time rather than frame counts. A missed timer
  tick does not extend the animation or resume it from an outdated position.
- A new answer cancels unfinished effects, preventing stacked animations.
- Particle counts and animation duration are bounded.
- Every answer uses the same selected preset and launch controls. Normal
  confetti and Again can each use a configurable, resizable emoji.
- There are no JavaScript assets, workers, browser canvases, background polls,
  or cross-webview messages. The settings UI is loaded only when opened.
- Windows reduced-motion preferences can optionally be respected.

The runtime uses Anki's bundled Qt and Python's standard library. No additional
dependencies or network access are required. The settings preview uses the same
native renderer as reviews. Version 1's `use_worker` setting is ignored on import
and removed the next time settings are saved.

## Install

Copy this directory into Anki's `addons21` folder, or package it as an
`.ankiaddon` archive.

Restart Anki after installing or updating the Python code.

## Configure

In Anki, open **Tools → Add-ons**, select **Tiramisu's Confetti Thing**, and
choose **Config**. A compact settings window provides:

- Live embedded previews for Good and Again.
- Trigger, preset, origin, shape, emoji, emoji-size, color, intensity, and
  spread controls.
- Fireworks duration, review delay, and reduced-motion options.

Preview buttons use the current controls immediately, without saving first.
Choose **Save** once the effect looks right.

Available presets are `button_cannon`, `simple_burst`, `realistic_burst`,
`fireworks`, `stars`, and `side_cannons`.

## Development

Run the checks from this directory:

```powershell
python -m unittest discover -s tests -v
```

An optional Windows integration check uses Anki's bundled Qt WebEngine:

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
$env:QTWEBENGINE_CHROMIUM_FLAGS = "--disable-gpu"
& "$env:LOCALAPPDATA\AnkiProgramFiles\.venv\Scripts\python.exe" tests/qt_overlay_smoke.py
& "$env:LOCALAPPDATA\AnkiProgramFiles\.venv\Scripts\python.exe" tests/qt_settings_smoke.py
```

Set `PYTHONPATH` to Anki's `app_packages` directory if the bundled interpreter
does not find PyQt6 automatically. `qt_overlay_smoke.py --senren` additionally
loads a real Senren card through local AnkiConnect without changing review data.
The test checks native animation during a one-second browser-script stall,
resizing, every preset and shape, delay, reduced motion, and timer cleanup.

The previous renderer's license is retained in
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) for the repository history.

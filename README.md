# Tiramisu's Confetti Thing

A small, offline Anki add-on that celebrates `Again`, `Good`, and `Easy`
answers with confetti. Each answer can be enabled or disabled independently.

## Why this rewrite is lean

- Only the reviewer receives the JavaScript assets.
- One canvas is reused instead of allocating a canvas for every answer.
- Rendering uses a web worker when Qt WebEngine supports it.
- A new answer cancels unfinished effects, preventing stacked animations.
- Particle counts and animation duration are bounded.
- Origin and shape choices apply consistently across single-origin celebration
  presets; Again has its own centered thumbs-down effect.
- There are no background polls, event listeners, cross-webview messages, or
  custom settings windows.
- Windows/browser reduced-motion preferences can optionally be respected.

The runtime is one small Python integration module, one small JavaScript
controller, and the vendored
[`canvas-confetti`](https://github.com/catdad/canvas-confetti) library. Nothing
is loaded from the network.

## Install

Copy this directory into Anki's `addons21` folder, or package it as an
`.ankiaddon` archive.

Restart Anki after installing or updating the Python code.

## Configure

In Anki, open **Tools → Add-ons**, select **Tiramisu's Confetti Thing**, and
choose **Config**. A compact settings window provides:

- Live embedded previews for Good and Again.
- Trigger, preset, origin, shape, color, intensity, and spread controls.
- Fireworks duration, review delay, reduced-motion, and worker options.

Preview buttons use the current controls immediately, without saving first.
Choose **Save** once the effect looks right.

Available presets are `button_cannon`, `simple_burst`, `realistic_burst`,
`fireworks`, `stars`, and `side_cannons`.

## Development

Run the checks from this directory:

```powershell
python -m unittest discover -s tests -v
node --check web/confetti.js
node tests/test_confetti.js
```

An optional Windows integration check uses Anki's bundled Qt WebEngine:

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
$env:QTWEBENGINE_CHROMIUM_FLAGS = "--disable-gpu"
& "$env:LOCALAPPDATA\AnkiProgramFiles\.venv\Scripts\python.exe" tests/qt_webengine_smoke.py
& "$env:LOCALAPPDATA\AnkiProgramFiles\.venv\Scripts\python.exe" tests/qt_settings_smoke.py
```

Third-party licensing is recorded in
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

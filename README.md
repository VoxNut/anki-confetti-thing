# Tiramisu's Confetti Thing

A small, offline Anki add-on that celebrates `Good` and `Easy` answers with
confetti.

## Why this rewrite is lean

- Only the reviewer receives the JavaScript assets.
- One canvas is reused instead of allocating a canvas for every answer.
- Rendering uses a web worker when Qt WebEngine supports it.
- A new answer cancels unfinished effects, preventing stacked animations.
- Particle counts and animation duration are bounded.
- There are no background polls, event listeners, cross-webview messages, or
  custom settings windows.
- Windows/browser reduced-motion preferences are respected by default.

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
choose **Config**. See the inline configuration help for every option.

Available presets are `button_cannon`, `simple_burst`, `realistic_burst`,
`fireworks`, `stars`, and `side_cannons`.

## Development

Run the checks from this directory:

```powershell
python -m unittest discover -s tests -v
node --check web/confetti.js
node tests/test_confetti.js
```

Third-party licensing is recorded in
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

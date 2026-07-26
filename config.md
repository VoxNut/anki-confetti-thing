## Tiramisu's Confetti Thing

Edit these values in Anki's add-on Config window.

- `enabled`: master switch.
- `trigger_good` / `trigger_easy`: answers that launch confetti.
- `preset`: `button_cannon`, `simple_burst`, `realistic_burst`, `fireworks`,
  `stars`, or `side_cannons`.
- `colors`: up to 12 CSS hex colors in `#rrggbb` form.
- `intensity`: particle percentage from 25 to 200.
- `duration_ms`: fireworks duration from 400 to 4000 milliseconds.
- `delay_ms`: delay after answering, from 0 to 500 milliseconds. A short delay
  lets Anki finish drawing the next card first.
- `respect_reduced_motion`: disable effects when Windows or the browser asks
  for reduced motion.
- `use_worker`: render through a web worker when supported.

Invalid values safely fall back to defaults. Changes take effect on the next
answer without restarting Anki.

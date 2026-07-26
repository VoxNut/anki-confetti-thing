## Tiramisu's Confetti Thing

Use Anki's add-on Config window for a live UI. Its underlying fields are:

- `enabled`: master switch.
- `trigger_again`, `trigger_hard`, `trigger_good`, and `trigger_easy`: answers
  that launch confetti. Again, Good, and Easy are enabled by default.
- `preset`: `button_cannon`, `simple_burst`, `realistic_burst`, `fireworks`,
  `stars`, or `side_cannons`.
- `colors`: up to 12 CSS hex colors in `#rrggbb` form.
- `intensity`: particle percentage from 25 to 200.
- `duration_ms`: fireworks duration from 400 to 4000 milliseconds.
- `delay_ms`: delay after answering, from 0 to 500 milliseconds. A short delay
  lets Anki finish drawing the next card first.
- `origin_mode`: `center`, `answer_button`, `top`, `bottom`, `left`, `right`,
  or `custom`. Single-origin presets launch from this point.
- `custom_origin_x` / `custom_origin_y`: percentages used by the `custom`
  origin.
- `shape`: `squares`, `circles`, `mixed`, `stars`, `emoji`, or `preset`.
- `emoji`: character used when `shape` is `emoji`.
- `again_emoji`: character used by the special Again burst, such as `😭`.
- `emoji_size`: emoji particle size from 50% to 300%.
- `spread`: launch width in degrees, from 10 to 360. Try 180 for a wide burst.
- `respect_reduced_motion`: honor Windows' reduced-motion preference. This is
  off by default because Windows may report reduced motion even when you
  explicitly want this effect.
- `use_worker`: render through a web worker when supported.

Invalid values safely fall back to defaults. Changes take effect on the next
answer without restarting Anki. Settings are cached between changes, so
answering a card does not read configuration files from disk.

`Again` uses its configured emoji with the same selected preset, origin,
spread, and launch style as the other answers.

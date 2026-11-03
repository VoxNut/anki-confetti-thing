"""Time-based confetti motion, independent of browser and timer frame rates."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class Particle:
    born: float
    life: float
    origin: tuple[float, float]
    vx: float
    vy: float
    drag: float
    fall: float
    size: float
    phase: float
    spin: float
    color: str
    shape: str

    def position(self, age: float, width: int, height: int) -> tuple[float, float]:
        distance = -math.expm1(-self.drag * age) / self.drag
        return (
            self.origin[0] * width + self.vx * distance + 6 * math.sin(self.phase + age * 8),
            self.origin[1] * height + self.vy * distance + self.fall * age,
        )


def make_particles(payload: Mapping[str, Any], rng: random.Random | None = None) -> list[Particle]:
    rng = rng or random.Random()
    intensity = max(25, min(200, payload.get("intensity", 100))) / 100
    spread = max(10, min(360, payload.get("spread", 100)))
    mode = payload.get("originMode", "center")
    ease = payload.get("ease", 3)
    points = {
        "center": (.5, .5), "top": (.5, .12), "bottom": (.5, .88),
        "left": (.08, .5), "right": (.92, .5),
        "answer_button": ({1: .18, 2: .38, 3: .62, 4: .82}.get(ease, .5), .88),
    }
    custom = payload.get("customOrigin", {})
    origin = (max(0, min(1, custom.get("x", .5))), max(0, min(1, custom.get("y", .5)))) \
        if mode == "custom" else points.get(mode, (.5, .5))
    angle = {1: 58, 2: 72, 3: 108, 4: 122}.get(ease, 90) if mode == "answer_button" else 90
    selected_shape = "emoji" if ease == 1 else payload.get("shape", "squares")
    shapes = {"squares": ("square",), "circles": ("circle",),
              "stars": ("star",), "mixed": ("square", "circle"), "emoji": ("emoji",)}
    colors = payload.get("colors") or ("#f6bd60", "#f5cac3", "#84a59d")
    emoji_size = max(50, min(300, payload.get("emojiSize", 160))) / 100
    particles: list[Particle] = []

    def burst(count: int, velocity: float = 45, scalar: float = 1,
              decay: float = .9, gravity: float = 1, born: float = 0,
              life: float = 200 / 60, point: tuple[float, float] = origin,
              direction: float = angle, preset_shape: tuple[str, ...] = ("square", "circle")) -> None:
        choices = shapes.get(selected_shape, preset_shape)
        for _ in range(max(1, round(count * intensity))):
            theta = math.radians(direction + rng.uniform(-spread / 2, spread / 2))
            speed = velocity * 60 * rng.uniform(.5, 1.5)
            shape = rng.choice(choices)
            particles.append(Particle(
                born, life, point, math.cos(theta) * speed, -math.sin(theta) * speed,
                -60 * math.log(decay), 180 * gravity,
                18 * emoji_size if shape == "emoji" else rng.uniform(6, 10) * scalar,
                rng.uniform(0, math.tau), rng.uniform(-240, 240), rng.choice(colors), shape,
            ))

    preset = payload.get("preset", "button_cannon")
    if preset == "simple_burst":
        burst(48, velocity=30, scalar=.8)
    elif preset == "realistic_burst":
        burst(38, velocity=52)
        burst(30)
        burst(52, decay=.91, scalar=.8)
        burst(30, velocity=28, scalar=1.1)
    elif preset == "fireworks":
        duration = max(.4, min(4, payload.get("duration", 1600) / 1000))
        for index in range(math.ceil(duration / .22)):
            burst(32, velocity=28, born=index * .22, life=55 / 60,
                  point=(rng.random(), rng.uniform(.08, .5)))
    elif preset == "stars":
        burst(38, velocity=40, scalar=1.15, preset_shape=("star",))
        burst(24, velocity=24, scalar=.65, preset_shape=("circle",))
    elif preset == "side_cannons":
        burst(58, velocity=42, point=(0, .86), direction=60)
        burst(58, velocity=42, point=(1, .86), direction=120)
    else:
        burst(72, velocity=46, gravity=.9, scalar=.95)
    return particles

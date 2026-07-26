(() => {
  "use strict";

  if (window.ankiConfetti?.version === 2) return;

  const state = {
    cannon: null,
    canvas: null,
    timer: 0,
    worker: null,
    thumbsDown: null,
  };
  const clamp = (value, low, high) => Math.max(low, Math.min(high, Number(value)));
  const count = (base, intensity) =>
    Math.max(1, Math.round(base * clamp(intensity || 100, 25, 200) / 100));
  const spread = (payload, fallback) =>
    Number.isFinite(Number(payload.spread))
      ? clamp(payload.spread, 10, 360)
      : fallback;

  function stop() {
    clearInterval(state.timer);
    state.timer = 0;
    state.cannon?.reset();
  }

  function cannon(useWorker) {
    if (state.cannon && state.worker === useWorker) return state.cannon;
    stop();
    state.canvas?.remove();
    const canvas = document.createElement("canvas");
    canvas.setAttribute("aria-hidden", "true");
    Object.assign(canvas.style, {
      position: "fixed",
      inset: "0",
      width: "100%",
      height: "100%",
      pointerEvents: "none",
      zIndex: "2147483647",
    });
    document.body.append(canvas);
    state.canvas = canvas;
    state.worker = useWorker;
    state.cannon = window.confetti.create(canvas, {
      resize: true,
      useWorker,
    });
    return state.cannon;
  }

  function configuredShapes(payload, presetShapes) {
    switch (payload.shape) {
      case "mixed":
        return ["square", "circle"];
      case "circles":
        return ["circle"];
      case "stars":
        return ["star"];
      case "preset":
        return presetShapes;
      case "squares":
      default:
        return ["square"];
    }
  }

  function defaults(payload, presetShapes) {
    const options = {
      colors: payload.colors,
      disableForReducedMotion: payload.reducedMotion !== false,
    };
    const shapes = configuredShapes(payload, presetShapes);
    if (shapes?.length) options.shapes = shapes;
    return options;
  }

  function origin(payload) {
    switch (payload.originMode) {
      case "answer_button":
        return {
          x: [0, 0.18, 0.38, 0.62, 0.82][payload.ease] || 0.5,
          y: 0.88,
        };
      case "top":
        return { x: 0.5, y: 0.12 };
      case "bottom":
        return { x: 0.5, y: 0.88 };
      case "left":
        return { x: 0.08, y: 0.5 };
      case "right":
        return { x: 0.92, y: 0.5 };
      case "custom":
        return {
          x: clamp(payload.customOrigin?.x ?? 0.5, 0, 1),
          y: clamp(payload.customOrigin?.y ?? 0.5, 0, 1),
        };
      case "center":
      default:
        return { x: 0.5, y: 0.5 };
    }
  }

  function angle(ease) {
    return [90, 58, 72, 108, 122][ease] || 90;
  }

  function burst(fire, payload, pieces, options = {}, presetShapes) {
    fire({
      ...defaults(payload, presetShapes),
      ...options,
      particleCount: count(pieces, payload.intensity),
    });
  }

  const presets = {
    button_cannon(fire, payload) {
      burst(fire, payload, 72, {
        angle: angle(payload.ease),
        spread: spread(payload, 58),
        startVelocity: 46,
        gravity: 0.9,
        scalar: 0.95,
        origin: origin(payload),
      });
    },

    simple_burst(fire, payload) {
      burst(fire, payload, 48, {
        spread: spread(payload, 64),
        startVelocity: 30,
        scalar: 0.8,
        origin: origin(payload),
      });
    },

    realistic_burst(fire, payload) {
      const shared = { ...defaults(payload), origin: origin(payload) };
      const total = count(150, payload.intensity);
      const configuredSpread = spread(payload, 100);
      [
        [0.25, { spread: configuredSpread, startVelocity: 52 }],
        [0.2, { spread: configuredSpread }],
        [0.35, { spread: configuredSpread, decay: 0.91, scalar: 0.8 }],
        [0.2, { spread: configuredSpread, startVelocity: 28, scalar: 1.1 }],
      ].forEach(([ratio, options]) =>
        fire({ ...shared, ...options, particleCount: Math.round(total * ratio) })
      );
    },

    fireworks(fire, payload) {
      const end = performance.now() + clamp(payload.duration || 1600, 400, 4000);
      const launch = () => {
        if (performance.now() >= end) {
          clearInterval(state.timer);
          state.timer = 0;
          return;
        }
        burst(fire, payload, 32, {
          startVelocity: 28,
          spread: spread(payload, 360),
          ticks: 55,
          origin: { x: Math.random(), y: Math.random() * 0.42 + 0.08 },
        });
      };
      launch();
      state.timer = setInterval(launch, 220);
    },

    stars(fire, payload) {
      const point = origin(payload);
      burst(fire, payload, 38, {
        spread: spread(payload, 70),
        startVelocity: 40,
        scalar: 1.15,
        origin: point,
      }, ["star"]);
      burst(fire, payload, 24, {
        spread: spread(payload, 90),
        startVelocity: 24,
        scalar: 0.65,
        origin: point,
      }, ["circle"]);
    },

    side_cannons(fire, payload) {
      const pieces = count(58, payload.intensity);
      const shared = {
        ...defaults(payload),
        particleCount: pieces,
        spread: spread(payload, 55),
        startVelocity: 42,
      };
      fire({ ...shared, angle: 60, origin: { x: 0, y: 0.86 } });
      fire({ ...shared, angle: 120, origin: { x: 1, y: 0.86 } });
    },
  };

  function launchAgain(fire, payload) {
    if (!state.thumbsDown && typeof window.confetti.shapeFromText === "function") {
      try {
        state.thumbsDown = window.confetti.shapeFromText({
          text: "👎",
          scalar: 2,
        });
      } catch (_error) {
        // Older web engines fall back to ordinary square particles.
      }
    }
    burst(fire, payload, 28, {
      spread: spread(payload, 100),
      startVelocity: 24,
      gravity: 1.05,
      scalar: 1.6,
      shapes: state.thumbsDown ? [state.thumbsDown] : ["square"],
      origin: { x: 0.5, y: 0.5 },
    });
  }

  function fire(payload = {}) {
    if (typeof window.confetti?.create !== "function") return;
    stop();
    const launch = cannon(payload.worker !== false);
    if (payload.ease === 1) {
      launchAgain(launch, payload);
    } else {
      (presets[payload.preset] || presets.button_cannon)(launch, payload);
    }
  }

  window.ankiConfetti = { version: 2, fire, stop };
})();

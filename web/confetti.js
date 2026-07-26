(() => {
  "use strict";

  if (window.ankiConfetti?.version === 2) return;

  const state = { cannon: null, canvas: null, timer: 0, worker: null };
  const clamp = (value, low, high) => Math.max(low, Math.min(high, Number(value)));
  const count = (base, intensity) =>
    Math.max(1, Math.round(base * clamp(intensity || 100, 25, 200) / 100));

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

  function defaults(payload) {
    return {
      colors: payload.colors,
      disableForReducedMotion: payload.reducedMotion !== false,
    };
  }

  function origin(ease) {
    return ease === 4 ? { x: 0.82, y: 0.88 } : { x: 0.62, y: 0.88 };
  }

  function burst(fire, payload, pieces, options = {}) {
    fire({
      ...defaults(payload),
      ...options,
      particleCount: count(pieces, payload.intensity),
    });
  }

  const presets = {
    button_cannon(fire, payload) {
      burst(fire, payload, 72, {
        angle: payload.ease === 4 ? 122 : 82,
        spread: 58,
        startVelocity: 46,
        gravity: 0.9,
        scalar: 0.95,
        origin: origin(payload.ease),
      });
    },

    simple_burst(fire, payload) {
      burst(fire, payload, 48, {
        spread: 64,
        startVelocity: 30,
        scalar: 0.8,
        origin: { x: 0.5, y: 0.52 },
      });
    },

    realistic_burst(fire, payload) {
      const shared = { ...defaults(payload), origin: origin(payload.ease) };
      const total = count(150, payload.intensity);
      [
        [0.25, { spread: 26, startVelocity: 52 }],
        [0.2, { spread: 60 }],
        [0.35, { spread: 100, decay: 0.91, scalar: 0.8 }],
        [0.2, { spread: 120, startVelocity: 28, scalar: 1.1 }],
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
          spread: 360,
          ticks: 55,
          origin: { x: Math.random(), y: Math.random() * 0.42 + 0.08 },
        });
      };
      launch();
      state.timer = setInterval(launch, 220);
    },

    stars(fire, payload) {
      const point = origin(payload.ease);
      burst(fire, payload, 38, {
        spread: 70,
        startVelocity: 40,
        scalar: 1.15,
        shapes: ["star"],
        origin: point,
      });
      burst(fire, payload, 24, {
        spread: 90,
        startVelocity: 24,
        scalar: 0.65,
        shapes: ["circle"],
        origin: point,
      });
    },

    side_cannons(fire, payload) {
      const pieces = count(58, payload.intensity);
      const shared = {
        ...defaults(payload),
        particleCount: pieces,
        spread: 55,
        startVelocity: 42,
      };
      fire({ ...shared, angle: 60, origin: { x: 0, y: 0.86 } });
      fire({ ...shared, angle: 120, origin: { x: 1, y: 0.86 } });
    },
  };

  function fire(payload = {}) {
    if (typeof window.confetti?.create !== "function") return;
    stop();
    const launch = cannon(payload.worker !== false);
    (presets[payload.preset] || presets.button_cannon)(launch, payload);
  }

  window.ankiConfetti = { version: 2, fire, stop };
})();

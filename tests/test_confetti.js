"use strict";

const assert = require("node:assert/strict");
const path = require("node:path");

let canvasCount = 0;
let resetCount = 0;
const launches = [];

global.window = global;
global.document = {
  body: {
    append() {},
  },
  createElement() {
    canvasCount += 1;
    return {
      setAttribute() {},
      style: {},
      remove() {},
    };
  },
};
global.confetti = function () {};
global.confetti.create = () => {
  const fire = (options) => launches.push(options);
  fire.reset = () => {
    resetCount += 1;
  };
  return fire;
};

require(path.join(__dirname, "..", "web", "confetti.js"));

const base = {
  ease: 3,
  colors: ["#ffffff"],
  intensity: 100,
  reducedMotion: true,
  worker: true,
};

window.ankiConfetti.fire({ ...base, preset: "button_cannon" });
window.ankiConfetti.fire({ ...base, preset: "stars" });
window.ankiConfetti.fire({ ...base, ease: 1, preset: "button_cannon" });

assert.equal(canvasCount, 1, "the same canvas should be reused");
assert.equal(resetCount, 2, "the previous animation should be cancelled");
assert.equal(launches.length, 4, "two cannons and two star layers should launch");
assert.equal(launches[0].disableForReducedMotion, true);
assert.equal(launches[0].particleCount, 72);
assert.equal(launches[1].shapes[0], "star");
assert.deepEqual(launches[3].origin, { x: 0.18, y: 0.88 });
assert.equal(launches[3].angle, 58);

window.ankiConfetti.stop();
assert.equal(resetCount, 3);

console.log("confetti runtime smoke test passed");

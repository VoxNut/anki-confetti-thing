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
global.confetti.shapeFromText = (options) => ({
  type: "emoji",
  text: options.text,
  scalar: options.scalar,
});
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
  originMode: "center",
  shape: "squares",
  emoji: "✨",
  againEmoji: "😭",
  emojiSize: 180,
  spread: 180,
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
assert.equal(launches[0].spread, 180);
assert.equal(launches[0].angle, 90);
assert.deepEqual(launches[0].origin, { x: 0.5, y: 0.5 });
assert.deepEqual(launches[0].shapes, ["square"]);
assert.deepEqual(launches[1].shapes, ["square"]);
assert.deepEqual(launches[2].shapes, ["square"]);
assert.deepEqual(launches[3].origin, { x: 0.5, y: 0.5 });
assert.equal(launches[3].shapes[0].text, "😭");
assert.equal(launches[3].spread, 180);
assert.equal(launches[3].particleCount, launches[0].particleCount);
assert.equal(launches[3].angle, launches[0].angle);
assert.equal(launches[3].scalar, 1.8);
assert.equal(launches[3].shapes[0].scalar, 1.8);

window.ankiConfetti.fire({
  ...base,
  ease: 3,
  preset: "simple_burst",
  shape: "emoji",
});
assert.equal(launches[4].shapes[0].text, "✨");
assert.equal(launches[4].scalar, 1.8);

window.ankiConfetti.stop();
assert.equal(resetCount, 4);

const actions = [];
const frames = new Map();
const timers = new Map();
let handle = 0;
global._queueAction = (action) => actions.push(action);
global.requestAnimationFrame = (callback) => {
  frames.set(++handle, callback);
  return handle;
};
global.cancelAnimationFrame = (id) => frames.delete(id);
global.setTimeout = (callback, delay) => {
  timers.set(++handle, { callback, delay });
  return handle;
};
global.clearTimeout = (id) => timers.delete(id);
function paint() {
  const pending = [...frames.values()];
  frames.clear();
  pending.forEach(callback => callback());
}

const before = launches.length;
window.ankiConfetti.afterCard({ ...base, delay: 80 });
assert.equal(launches.length, before, "wait for Anki's card-script queue");
assert.equal(frames.size, 0, "do not start before queued card scripts finish");
actions.shift()();
paint();
assert.equal(launches.length, before, "give the next card its first paint");
paint();
assert.equal(launches.length, before, "honor the extra configured delay");
assert.equal([...timers.values()][0].delay, 80);
const launch = [...timers.values()][0].callback;
timers.clear();
launch();
assert.equal(launches.length, before + 1);

window.ankiConfetti.afterCard(base);
window.ankiConfetti.stop();
actions.shift()();
assert.equal(frames.size, 0, "cancel stale queued celebrations");
window.ankiConfetti.afterCard(base);
actions.shift()();
paint();
window.ankiConfetti.stop();
paint();
assert.equal(timers.size, 0, "cancel celebrations waiting for paint");
window.ankiConfetti.afterCard(base);
actions.shift()();
paint();
paint();
window.ankiConfetti.stop();
assert.equal(timers.size, 0, "cancel delayed launches");
assert.equal(launches.length, before + 1);

console.log("confetti runtime smoke test passed");

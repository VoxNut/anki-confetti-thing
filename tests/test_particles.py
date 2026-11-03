import importlib.util
import math
import random
import sys
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location("confetti_particles", Path(__file__).parents[1] / "particles.py")
particles = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = particles
spec.loader.exec_module(particles)


class ParticleTests(unittest.TestCase):
    def scene(self, **payload):
        return particles.make_particles(payload, random.Random(42))

    def test_elapsed_time_does_not_depend_on_number_of_frames(self):
        particle = self.scene()[0]
        expected = particle.position(1.2, 1920, 1080)
        for time in [0, .016, .032, .048, 1.2]:
            result = particle.position(time, 1920, 1080)
        self.assertEqual(result, expected)
        self.assertNotEqual(particle.position(.2, 1920, 1080), expected)

    def test_all_presets_and_shapes_are_finite_and_bounded(self):
        for preset in ["button_cannon", "simple_burst", "realistic_burst", "fireworks", "stars", "side_cannons"]:
            for shape in ["squares", "circles", "mixed", "stars", "emoji", "preset"]:
                scene = self.scene(preset=preset, shape=shape, intensity=200, duration=4000)
                self.assertLessEqual(len(scene), 1280)
                self.assertTrue(scene)
                for particle in scene:
                    self.assertTrue(all(math.isfinite(value) for value in particle.position(.5, 1920, 1080)))
                    self.assertLessEqual(particle.born + particle.life, 5)

    def test_again_uses_emoji_with_selected_preset(self):
        normal = self.scene(preset="side_cannons", ease=3)
        again = self.scene(preset="side_cannons", ease=1, emojiSize=300)
        self.assertEqual(len(normal), len(again))
        self.assertTrue(all(p.shape == "emoji" and p.size == 54 for p in again))
        self.assertEqual({p.origin for p in again}, {(0, .86), (1, .86)})

    def test_origins_and_spread_are_preserved(self):
        scene = self.scene(originMode="custom", customOrigin={"x":.2,"y":.8}, spread=10)
        self.assertTrue(all(p.origin == (.2, .8) for p in scene))
        self.assertTrue(all(abs(p.vx) < abs(p.vy) * .1 for p in scene))

    def test_fireworks_are_scheduled_in_advance(self):
        scene = self.scene(preset="fireworks", duration=1000)
        births = sorted({p.born for p in scene})
        self.assertEqual(len(births), 5)
        self.assertAlmostEqual(births[-1], .88)

    def test_palette_and_intensity(self):
        scene = self.scene(intensity=200, colors=["#123456"])
        self.assertEqual(len(scene), 144)
        self.assertEqual({p.color for p in scene}, {"#123456"})


if __name__ == "__main__":
    unittest.main()

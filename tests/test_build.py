import importlib.util
from pathlib import Path
import re
import unittest
spec=importlib.util.spec_from_file_location('builder',Path(__file__).resolve().parents[1]/'scripts/build.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
class BuildTest(unittest.TestCase):
 def test_all_guides_and_assets(self):
  recipes=b.load_recipes(); self.assertEqual(len(recipes),10)
  ids={r['id'] for r in recipes}
  for r in recipes:
   self.assertNotRegex(r['html'],r':{3,}\{')
   for path in re.findall(r'<img[^>]+src="([^"]+)"',r['html']):self.assertTrue((b.ROOT/path).is_file(),path)
   for target in re.findall(r'href="#/course/([a-z0-9-]+)"',r['html']):self.assertIn(target,ids)
 def test_preserves_safety_notes_and_nested_images(self):
  recipes={r['id']:r for r in b.load_recipes()}
  self.assertIn('5V',recipes['02-setup']['html'])
  self.assertIn('calibration_pose.jpg',recipes['03-calibration']['html'])
  self.assertIn('wrist_center.jpg',recipes['03-calibration']['html'])
  self.assertIn('尚未完整跑通',recipes['05-sim-teleop']['html'])
if __name__=='__main__': unittest.main()

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

spec=importlib.util.spec_from_file_location('generate',Path(__file__).resolve().parents[1]/'src/generate.py')
g=importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)

class GeneratorTests(unittest.TestCase):
    def fixture(self):
        return dict(username='test',updated='2026-11-10T12:00:00+00:00',repositories=3,stars=0,followers=0,commits=None,languages={'Java & XML':100},popular=[],contributions=None,days=[])
    def test_themes_escape_and_match(self):
        config=dict(name='A < B',username='test',role='Student',location='Brazil',stack='Java')
        texts=[]
        for theme in ('dark','light'):
            svg=g.render(config,self.fixture(),theme)
            root=ET.fromstring(svg)
            texts.append([node.text for node in root.iter('{http://www.w3.org/2000/svg}text')])
            self.assertIn('A &lt; B',svg)
            self.assertIn('N/A',svg)
        self.assertEqual(texts[0],texts[1])
    def test_outage_preserves_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            (root/'cache').mkdir()
            (root/'profile.toml').write_text('username="test"\n')
            snapshot=json.dumps(self.fixture())
            (root/'cache/stats.json').write_text(snapshot)
            with patch.object(g,'ROOT',root),patch.object(g,'collect',side_effect=RuntimeError('outage')),patch.object(g,'render',return_value='<svg/>'),patch('sys.argv',['generate']):
                g.main()
            self.assertEqual((root/'cache/stats.json').read_text(),snapshot)
            self.assertTrue((root/'dark_mode.svg').exists())
    def test_pagination(self):
        api=g.API()
        with patch.object(api,'request',side_effect=[[{}]*100,[{}]]) as request:
            self.assertEqual(len(api.pages('users/test/repos')),101)
            self.assertIn('page=2',request.call_args.args[0])

if __name__=='__main__':
    unittest.main()

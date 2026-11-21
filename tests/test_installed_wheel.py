"""Opt-in installed-distribution check, never imports the checkout's CLI.

Build with pip wheel --no-deps ., install that wheel --no-deps in an isolated
runtime with the project's ordinary core dependencies, then run:
CODEFIXER_WHEEL_PYTHON=/absolute/runtime/bin/python python -m unittest discover \
    -s tests -p test_installed_wheel.py -v
No model, linter or repository command is invoked by these tests.
"""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


@unittest.skipUnless(os.environ.get('CODEFIXER_WHEEL_PYTHON'),
                     'Requires an explicitly supplied installed-wheel runtime')
class InstalledWheelTests(unittest.TestCase):
    def setUp(self):
        self.python = os.environ['CODEFIXER_WHEEL_PYTHON']
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.outside = Path(self.temp.name)
        self.home = self.outside / 'home'
        self.home.mkdir()
        self.env = {**os.environ, 'HOME': str(self.home), 'PYTHONPATH': '',
                    'TMPDIR': str(self.outside), 'PYTHONDONTWRITEBYTECODE': '1'}

    def run_cli(self, *args):
        return self.run_process([str(Path(self.python).with_name('codefixer')), *args])

    def run_python(self, *args):
        return self.run_process([self.python, *args])

    def run_process(self, command):
        result = subprocess.run(command, cwd=self.outside,
                                env=self.env, text=True, capture_output=True,
                                timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_help_and_config_display(self):
        self.assertIn('--config-reset', self.run_cli('--help'))
        config = json.loads(self.run_cli('--config'))
        self.assertIn('llm', config)
        stored = json.loads((self.home / '.codefixer/config.json').read_text())
        self.assertEqual(config, stored)

    def test_reset_persists_defaults(self):
        defaults = json.loads(self.run_cli('--config'))
        path = self.home / '.codefixer/config.json'
        modified = json.loads(path.read_text())
        modified['llm']['timeout'] = 1234
        path.write_text(json.dumps(modified))
        self.run_cli('--config-reset')
        self.assertEqual(json.loads(path.read_text()), defaults)
        self.assertEqual(json.loads(self.run_cli('--config')), defaults)

    def test_local_module_and_template_closure(self):
        program = (
            'import json, pathlib, cli, config_manager, issue_deduplicator, llm; '
            'root=pathlib.Path(cli.__file__).parent; '
            'print(json.dumps({"origins": [str(pathlib.Path(m.__file__).resolve()) '
            'for m in (cli,config_manager,issue_deduplicator)], '
            '"template": llm.load_prompt_template(), '
            '"template_file": (root/"templates/fix_prompt.txt").is_file()}))'
        )
        result = json.loads(self.run_python('-c', program))
        source = Path(__file__).resolve().parent.parent
        for origin in result['origins']:
            self.assertNotIn(source, Path(origin).parents)
            self.assertIn('site-packages', origin)
        self.assertTrue(result['template_file'])
        expected = (source / 'templates/fix_prompt.txt').read_text()
        self.assertEqual(result['template'], expected)


if __name__ == '__main__':
    unittest.main()

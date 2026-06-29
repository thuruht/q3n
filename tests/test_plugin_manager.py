import sys
import types
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.src.core.plugin_manager import PluginManager


class _FakeWidget:
    def __init__(self, parent=None): pass
    def set_entries(self, entries): self._entries = entries


def _fake_standalone(entries, args):
    _fake_standalone.called_with = (entries, args)


PLUGIN_META = {
    'name': 'test_plugin',
    'title': 'Test Plugin',
    'description': 'A test plugin',
    'version': '0.1.0',
}


def test_register_panel():
    pm = PluginManager(plugin_dirs=[])
    pm.register_panel('testpanel', _FakeWidget)
    assert pm.panels['testpanel'] is _FakeWidget


def test_register_standalone():
    pm = PluginManager(plugin_dirs=[])
    pm.register_standalone('teststd', _fake_standalone)
    assert pm._standalones['teststd'] is _fake_standalone


def test_run_standalone():
    pm = PluginManager(plugin_dirs=[])
    pm.register_standalone('teststd', _fake_standalone)
    pm.run_standalone('teststd', ['e1'], ['--flag'])
    assert _fake_standalone.called_with == (['e1'], ['--flag'])


def test_run_standalone_not_found():
    pm = PluginManager(plugin_dirs=[])
    try:
        pm.run_standalone('missing', [], [])
        assert False, 'should raise'
    except KeyError:
        pass


def test_list_plugins_empty():
    pm = PluginManager(plugin_dirs=[])
    assert pm.list_plugins() == []


def test_list_plugins_with_fake_module():
    pm = PluginManager(plugin_dirs=[])
    mod = types.SimpleNamespace(PLUGIN_META=PLUGIN_META)
    pm._plugins.append(('test_plugin', mod))
    result = pm.list_plugins()
    assert result == [('test_plugin', PLUGIN_META)]

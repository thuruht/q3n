"""Plugin discovery and loading for the Q3N meta-application framework.

Plugins are Python modules or packages placed in app/plugins/ (or a
configurable directory). Each plugin must expose a `register()` function
that accepts a `PluginManager` instance.

Example plugin (app/plugins/my_plugin/__init__.py):
    def register(manager):
        manager.register_action('my_action', my_handler)
        manager.register_widget('my_widget', MyWidgetClass)
"""

from pathlib import Path
import importlib
import inspect
import sys


class PluginManager:
    """Discovers and loads plugins from a directory."""

    def __init__(self, plugin_dirs=None):
        self._actions = {}
        self._widgets = {}
        self._hooks = {}
        self._panels = {}
        self._standalones = {}
        self._plugins = []
        self._plugin_dirs = plugin_dirs or self._default_dirs()

    @staticmethod
    def _default_dirs():
        root = Path(__file__).resolve().parent.parent.parent
        return [
            root / 'plugins',
            Path.cwd() / 'plugins',
            Path.cwd() / 'app' / 'plugins',
        ]

    def discover(self):
        """Scan plugin directories and load all found plugins."""
        for plugin_dir in self._plugin_dirs:
            if not plugin_dir.exists():
                continue
            sys.path.insert(0, str(plugin_dir.parent))
            for entry in sorted(plugin_dir.iterdir()):
                if entry.name.startswith('_') or entry.name.startswith('.'):
                    continue
                self._load(entry)
        return self._plugins

    def _load(self, path):
        """Load a single plugin from a file or package path."""
        name = path.stem if path.is_file() else path.name
        try:
            if path.is_file() and path.suffix == '.py':
                spec = importlib.util.spec_from_file_location(name, path)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
            elif path.is_dir() and (path / '__init__.py').exists():
                module = importlib.import_module(f'plugins.{name}')
            else:
                return
            if hasattr(module, 'register'):
                module.register(self)
                self._plugins.append((name, module))
        except Exception as e:
            print(f'[plugin] Failed to load {name}: {e}')

    def register_action(self, name, func):
        """Register a callable action."""
        self._actions[name] = func

    def register_widget(self, name, widget_class):
        """Register a widget class."""
        self._widgets[name] = widget_class

    def register_hook(self, hook_name, func):
        """Register a hook callback."""
        self._hooks.setdefault(hook_name, []).append(func)

    def register_panel(self, name: str, widget_class: type) -> None:
        self._panels[name] = widget_class

    def register_standalone(self, name: str, func) -> None:
        self._standalones[name] = func

    def list_plugins(self) -> list:
        return [(name, getattr(mod, 'PLUGIN_META', {})) for name, mod in self._plugins]

    def run_standalone(self, name: str, entries, args) -> None:
        func = self._standalones.get(name)
        if func is None:
            raise KeyError(f"No standalone plugin '{name}'")
        func(entries, args)

    def get_action(self, name):
        return self._actions.get(name)

    def get_widget(self, name):
        return self._widgets.get(name)

    def trigger_hook(self, hook_name, *args, **kwargs):
        results = []
        for func in self._hooks.get(hook_name, []):
            try:
                results.append(func(*args, **kwargs))
            except Exception as e:
                print(f'[hook] {hook_name}: {e}')
        return results

    @property
    def actions(self):
        return dict(self._actions)

    @property
    def widget_classes(self):
        return dict(self._widgets)

    @property
    def panels(self):
        return dict(self._panels)

    @property
    def hooks(self):
        return dict(self._hooks)

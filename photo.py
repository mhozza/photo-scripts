
import argparse
import importlib
import os
import pkgutil

def main():
    parser = argparse.ArgumentParser(description="Photo management tool.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Discover and load plugins
    plugins_dir = os.path.join(os.path.dirname(__file__), "plugins")
    for _, name, _ in pkgutil.iter_modules([plugins_dir]):
        plugin = importlib.import_module(f"plugins.{name}")
        if hasattr(plugin, "register_subcommand"):
            plugin.register_subcommand(subparsers)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()

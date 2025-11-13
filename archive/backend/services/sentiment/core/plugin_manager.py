# backend/core/plugin_manager.py
# Loads and manages plugins

class PluginManager:
    def __init__(self):
        self.factor_plugins = []
        self.executor_plugins = []

    def load_plugins(self):
        # Discover and load plugins
        pass

    def get_factors(self):
        # Call all factor plugins
        pass

    def execute_trade(self, trade):
        # Call appropriate executor plugin
        pass

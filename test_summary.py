from shared.smart_model_manager import SmartModelManager
try:
    manager = SmartModelManager()
    print(f'Environment: {manager.environment.value}')
    print(f'Config: {manager.config}')
except Exception as e:
    print(f'Model manager test: {e}')

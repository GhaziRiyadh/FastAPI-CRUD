from src.core.utils.utils import convert_path_to_model, get_app_paths
import importlib

for path in get_app_paths("models").values():
    for p in path.values():
        importlib.import_module(convert_path_to_model(p))
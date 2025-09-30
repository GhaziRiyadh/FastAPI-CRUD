import mimetypes
from datetime import datetime, timezone
from pathlib import Path
import os,time
import importlib
import importlib.util
from typing import Dict

def get_apps() -> Dict[str, str]:
    apps_dir = os.path.join("src", "apps")
    return {name: os.path.join(apps_dir, name) for name in os.listdir(apps_dir)}


_cache: dict[str, tuple[float, dict[str, dict[str, str]]]] = {}
_CACHE_TTL = 60*60  # ثانية

def get_app_paths(child_name: str) -> dict[str, dict[str, str]]:
    """Return all <child_name> paths inside every app with TTL cache."""
    now = time.time()
    if child_name in _cache:
        ts, data = _cache[child_name]
        if now - ts < _CACHE_TTL:
            return data

    result: dict[str, dict[str, str]] = {}

    for app_name, app_path in get_apps().items():
        if not os.path.isdir(app_path) or app_name.startswith("__"):
            continue

        for root, dirs, files in os.walk(app_path):
            if os.path.basename(root) == child_name:
                file_paths = {
                    file.replace(".py", ""): os.path.join(root, file)
                    for file in files if "__init__" not in file
                }
                result[app_name] = file_paths
                break

    _cache[child_name] = (now, result)
    return result

def convert_path_to_model(path:str):
    return path.replace("\\",'.').removesuffix(".py")

def calc_average_rate(reviews):
    return float(sum(r.rating for r in reviews) / len(reviews)) if reviews else 0

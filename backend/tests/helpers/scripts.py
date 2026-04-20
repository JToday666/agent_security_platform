from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def load_module_from_path(name: str, path: Path):
    """按文件路径加载脚本模块，供 CLI 和入口测试复用。"""
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载模块: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module

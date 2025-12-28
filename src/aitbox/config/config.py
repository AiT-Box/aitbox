#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File        : config.py
Project     : aitbox
Author      : gdd
Created     : 2025-12-27
Description :
"""

from functools import lru_cache
from typing import Any

import yaml
from hydra.utils import instantiate

GLOBAL_YAML_PATH: str | None = None
GLOBAL_CONFIG: Any = None


@lru_cache
def load_yaml(path: str) -> dict:
    """ """
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def set_yaml_path(path: str) -> dict:
    """ """
    global GLOBAL_YAML_PATH
    GLOBAL_YAML_PATH = path
    load_yaml.cache_clear()
    config = get_cfg()
    global GLOBAL_CONFIG
    GLOBAL_CONFIG = config
    return config


def get_cfg(path: str | None = None) -> Any:
    """ """
    global GLOBAL_YAML_PATH

    yaml_path = path or GLOBAL_YAML_PATH
    if yaml_path is None:
        raise RuntimeError(
            "YAML path not set. Provide path or call set_yaml_path(path) first."
        )

    cfg = load_yaml(yaml_path)
    cfg = instantiate_cfg(cfg)
    return cfg


def instantiate_cfg(cfg: Any) -> Any:
    """ """
    if isinstance(cfg, dict):
        if "_target_" in cfg:
            return instantiate(cfg, _convert_="object")
        return {k: instantiate_cfg(v) for k, v in cfg.items()}

    if isinstance(cfg, list):
        return [instantiate_cfg(v) for v in cfg]

    return cfg

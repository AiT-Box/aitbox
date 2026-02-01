#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File        : base.py
Project     : aitbox
Author      : gdd
Created     : 2025-12-27
Description :
"""

from dataclasses import fields


class ConfigBase:
    """"""

    def __new__(cls, *args, **kwargs):
        """ """
        obj = super().__new__(cls)
        cls_fields = list(fields(cls))

        arg_kwargs = {}
        if args:
            if len(args) > len(cls_fields):
                raise TypeError(
                    f"{cls.__name__} takes at most {len(cls_fields)} positional arguments "
                    f"but {len(args)} were given"
                )
            for value, field in zip(args, cls_fields):
                arg_kwargs[field.name] = value
        explicit_kwargs = {**arg_kwargs, **kwargs}
        
        from aitbox.config.config import GLOBAL_CONFIG

        yaml_obj = None
        if GLOBAL_CONFIG is not None:
            yaml_obj = find_instance(GLOBAL_CONFIG, cls)

        for f in cls_fields:
            name = f.name
            if name in explicit_kwargs:
                value = explicit_kwargs[name]
            elif yaml_obj is not None and hasattr(yaml_obj, name):
                value = getattr(yaml_obj, name)
            else:
                value = getattr(cls, name)
            setattr(obj, name, value)
        return obj


def find_instance(root: object, cls: type) -> object | None:
    """"""
    if isinstance(root, cls):
        return root

    if hasattr(root, "__dict__"):
        for v in root.__dict__.values():
            res = find_instance(v, cls)
            if res is not None:
                return res

    if isinstance(root, (list, tuple)):
        for v in root:
            res = find_instance(v, cls)
            if res is not None:
                return res

    return None

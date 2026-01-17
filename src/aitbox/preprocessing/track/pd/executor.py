#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File        : executor
Project     : aitbox
Author      : gdd
Created     : 2026/1/17
Description :
"""
from functools import wraps

import pandas as pd


USE_PANDARALLEL = False


def set_pandarallel():
    """ """
    global USE_PANDARALLEL
    USE_PANDARALLEL = True


def init_pandarallel(nb_workers=None):
    """ """
    from pandarallel import pandarallel

    pandarallel.initialize(
        nb_workers=nb_workers,
        progress_bar=True
    )


def groupby_apply_wrapper(key: str):
    """ """

    def decorator(func):
        """ """
        @wraps(func)
        def wrapper(df: pd.DataFrame, *args, **kwargs) -> pd.DataFrame:
            df_groupy = df.groupby(key, group_keys=False,)
            global USE_PANDARALLEL
            if USE_PANDARALLEL:
                return df_groupy.parallel_apply(
                    lambda g: func(g, *args, **kwargs)
                )
            else:
                return df_groupy.apply(
                    lambda g: func(g, *args, **kwargs)
                )
        return wrapper
    return decorator

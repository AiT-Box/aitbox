#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File        : downsample
Project     : aitbox
Author      : gdd
Created     : 2026/1/17
Description :
"""
import pandas as pd

from aitbox.preprocessing.track.pd.executor import groupby_apply_wrapper


@groupby_apply_wrapper
def sample_by_distance(track: pd.DataFrame, distance_th: float, *args, **kwargs):
    """ """
    pass

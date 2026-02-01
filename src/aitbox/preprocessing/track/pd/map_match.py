#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File        : map_match
Project     : aitbox
Author      : gdd
Created     : 2026/1/18
Description :
"""

from __future__ import annotations

import numpy as np
from typing import Any

_NATIVE_MODULE_NAME = "aitbox.preprocessing.track.map_match"


def map_match(
    road_network: dict[str, Any],
    tracks: list[np.ndarray],
    *,
    track_ids: list[str] | None = None,
    gps_sigma: float = 50.0,
    beta: float = 5.0,
    search_radius: float = 100.0,
    num_threads: int = 0,
) -> list[dict[str, Any] | None]:
    import importlib

    native = importlib.import_module(_NATIVE_MODULE_NAME)
    return native.map_match(
        road_network=road_network,
        tracks=tracks,
        track_ids=track_ids,
        gps_sigma=gps_sigma,
        beta=beta,
        search_radius=search_radius,
        num_threads=num_threads,
    )

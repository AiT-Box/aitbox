#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File        : indicator
Project     : aitbox
Author      : gdd, run
Created     : 2026/1/17
Description :
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

import pandas as pd

from aitbox.schemas.road_network import Lane, Branch, Cross


class IndicatorType(str, Enum):
    """"""
    # Flow / demand
    VOLUME = "volume"  # 流量
    THROUGHPUT = "throughput"  # 实际通行流量

    # Queue
    QUEUE_LENGTH = "queue_length"  # 实时排队长度

    QUEUE_TIME = "queue_time"  # 排队时间
    GREEN_END_QUEUE_LENGTH = "green_end_queue_length"  # 绿灯时间结束时刻的排队长度
    RED_START_QUEUE_LENGTH = "red_start_queue_length"  # 红灯启亮时刻的排队长度


    # State
    SPEED = "speed"  # 速度
    DENSITY = "density"  # 密度
    OCCUPANCY = "occupancy"  # 占有率

    # Capacity / saturation
    CAPACITY = "capacity"  # 通行能力
    SATURATION = "saturation"  # 饱和度（v/c）
    DEGREE_OF_SATURATION = "dos"  # HCM 常用缩写

    # Efficiency / delay
    DELAY = "delay"  # 平均延误
    STOP_DELAY = "stop_delay"  # 停车延误
    TRAVEL_TIME = "travel_time"  # 行程时间

    # Stability / spillback
    QUEUE_SPILLBACK = "queue_spillback"  # 排队溢出
    BLOCKING = "blocking"  # 阻塞

    # Others
    STOP_COUNT = "stop_count"  # 停车次数


@dataclass
class Indicator:
    """ """
    type: IndicatorType
    freq: str
    entity: None | Lane | Branch | Cross
    value: Any
    timestamp: None | str | int = None
    unit: None | str = None

    def __post_init__(self):
        """ """
        try:
            pd.tseries.frequencies.to_offset(self.freq)
        except Exception:
            pass

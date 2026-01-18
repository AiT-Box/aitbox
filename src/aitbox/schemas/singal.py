#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File        : singal
Project     : aitbox
Author      : gdd, run
Created     : 2026/1/17
Description :
"""
from dataclasses import dataclass
from enum import Enum
from typing import List


class PhaseType(str, Enum):
    NORMAL = "normal"
    EMPTY = "empty"


class SignalSchemaType(str, Enum):
    CYCLER = "cycler"  # 周期式
    ACTUATED = "actuated"  # 感应式
    ADAPTIVE = "adaptive"  # 自适应


@dataclass
class SignalSchema:
    """signalschema """
    rings: List["Ring"]  # 环的id
    running_phase: List[int]  # 每个环上正在运行的相位
    running_time: List[int]  # 每个环上每个相位运行的时间（s）
    type: SignalSchemaType

@dataclass
class Ring:
    phases: List["Phase"]


class Phase:
    id: str | int
    type: PhaseType  # 相位类型
    green: int  # 绿灯时间
    min_green: int  # 最小绿
    max_green: int  # 最大绿
    counting_down: int  # 绿闪烁
    yellow: int  # 黄灯时间
    all_red: int  # 全红时间
    start_up_loss: int  # 启动损失时间
    barrier_id: int  # 屏障区编号

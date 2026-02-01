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
    type: SignalSchemaType
    rings: List["Ring"]  # 相位结构：决定了交叉口相位的结构以多环的形式组织。
    running_phase: List[int]  # 每个环上正在运行的相位
    running_time: List[int]  # 每个环上每个相位运行的时间（s）


@dataclass
class ActuatedSignalSchema(SignalSchema):
    """Actuatedsignalschema """

    def __init__(self):
        super().__init__()

    max_break_gap: float  # 最大切断间隔
    start_green: int  # 相位初始绿灯时间


@dataclass
class AdaptiveSignalSchema(SignalSchema):
    """Actuatedsignalschema """

    def __init__(self):
        super().__init__()


@dataclass
class CyclerSignalSchema(SignalSchema):
    """Cyclersignalschema """

    def __init__(self):
        super().__init__()

    cycle: int  # 信号周期
    min_cycle: int  # 方案的最小周期
    max_cycle: int  # 方案的最大周期
    phase_offset: int  # 相位差


@dataclass
class Ring:
    phases: List["Phase"]

@dataclass
class Phase:
    id: str | int
    type: PhaseType  # 相位类型

@dataclass
class CyclerPhase(Phase):
    green: int  # 绿灯时间
    min_green: int  # 最小绿
    max_green: int  # 最大绿
    green_flash: int  # 绿闪烁
    yellow: int  # 黄灯时间
    all_red: int  # 全红时间
    start_up_loss: int  # 启动损失时间
    barrier_id: int  # 屏障区编号


@dataclass
class ActuatedPhase(Phase):
    min_green: int  # 初始绿灯时间
    green_extend_unit: int  # 绿灯单位延长时间
    max_green: int  # 绿灯极限延长时间

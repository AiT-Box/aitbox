#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project : aitbox
# @File : ippo_solver.py
# @Author : run
# @Date : 2026/1/19 20:54
# Description: 基于IPPO的强化学习信号控制模式求解器

from typing import List

from aitbox.models.signal.isolated.base import IsolatedSolver
from aitbox.schemas.indicator import Indicator
from aitbox.schemas.road_network import Cross
from aitbox.schemas.singal import SignalSchema


class IPPOSolver(IsolatedSolver):
    def __init__(self, *args):
        pass

    def solve(self, cross: Cross, indicators: Indicator | List[Indicator], schema: SignalSchema | None = None, *args,
              **kwargs) -> SignalSchema:
        # todo 确认指标所在位置
        return schema

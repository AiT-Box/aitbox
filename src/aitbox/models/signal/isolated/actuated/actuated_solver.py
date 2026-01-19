#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project : aitbox
# @File : actuated_solver.py
# @Author : run
# @Date : 2026/1/19 20:51
from typing import List

from aitbox.models.signal.isolated.base import IsolatedSolver
from aitbox.schemas.indicator import Indicator
from aitbox.schemas.road_network import Cross
from aitbox.schemas.singal import SignalSchema


class ActuatedSolver(IsolatedSolver):
    def __init__(self, *args):
        pass

    def solve(self, cross: Cross, indicators: Indicator | List[Indicator], schema: SignalSchema | None = None, *args,
              **kwargs) -> SignalSchema:
        # todo 确认指标所在位置

        return schema

#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project : aitbox
# @File : simple_solver.py
# @Author : run
# @Date : 2026/1/18 20:43
from typing import List

from aitbox.models.signal.isolated.base import IsolatedSolver
from aitbox.schemas.indicator import Indicator
from aitbox.schemas.road_network import Cross
from aitbox.schemas.singal import SignalSchema


class SimpleSolver(IsolatedSolver):
    def __init__(self, *args):
        pass


    def solve(self, cross: Cross, indicators: Indicator | List[Indicator], schema: SignalSchema | None = None, *args,
              **kwargs) -> SignalSchema:
        pass


    def calc_cycle(self):
        #step1: calc cycle for intersection

        pass

    def allocate_green_split(self):
        # step2: allocate green split for every phase
        pass

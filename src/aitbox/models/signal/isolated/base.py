#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File        : base
Project     : aitbox
Author      : gdd
Created     : 2026/1/17
Description :
"""

import abc
from typing import List

from aitbox.schemas.indicator import Indicator
from aitbox.schemas.road_network import Cross
from aitbox.schemas.singal import SingalSchema


class IsolatedSolver(abc.ABC):
    """ """

    @abc.abstractmethod
    def solve(
        self,
        cross: Cross,
        indicators: Indicator | List[Indicator],
        schema: SingalSchema | None = None,
        *args,
        **kwargs,
    ) -> SingalSchema:
        """ """
        ...

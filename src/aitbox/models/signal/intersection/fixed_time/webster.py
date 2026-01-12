#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File        : webster.py
Project     : aitbox
Author      : wukunrun
Created     : 2026-01-12
Description : 获得webster模型的信号配时
"""
import logging

import numpy as np


class Webster:
    def __init__(self, min_cycle=50, max_cycle=180):
        """初始化Webster计算器

        Args:
            min_cycle: 最小信号周期（秒）
            max_cycle: 最大信号周期（秒）
        """
        if min_cycle <= 0 or max_cycle <= 0:
            raise ValueError("周期值必须大于0")
        if min_cycle >= max_cycle:
            raise ValueError("最小周期必须小于最大周期")
        self.min_cycle = min_cycle
        self.max_cycle = max_cycle
        self.logger = logging.getLogger(__name__)

    def set_min_cycle(self, min_cycle: int) -> None:
        self.min_cycle = min_cycle

    def set_max_cycle(self, max_cycle: int) -> None:
        """设置最大周期"""
        if max_cycle <= 0:
            raise ValueError("最大周期必须大于0")
        if max_cycle <= self.min_cycle:
            raise ValueError("最大周期必须大于当前最小周期")
        self.max_cycle = max_cycle

    def get_cycle_by_webster(self, l: np.array, y: np.array) -> int:
        """使用Webster公式计算最优信号周期

        公式: C = 1.5 * ΣL / (1 - ΣY)

        Args:
            l: 各相位损失时间列表（秒）
            y: 各相位饱和度列表（0-1之间）

        Returns:
            int: 计算出的信号周期（秒），在[min_cycle, max_cycle]范围内

        Raises:
            ValueError: 输入参数无效时
        """

        if l is None or len(l) == 0:
            raise Exception("相位损失时间列表为空，无法计算！")
        if y is None or len(y) == 0:
            raise Exception("相位饱和度列表为空，无法计算！")

        if np.sum(y) >= 1.00:
            raise Exception("相位的饱和度之和大于1.0，无法计算！")
        elif np.sum(y) > 0.85:
            logging.warning("相位的饱和度之和大于0.90，处于过饱和状态，信控周期将会偏大！")

        # 防止除零
        if np.sum(y) >= 0.90:
            self.logger.warning("饱和度之和接近1.0，使用最大周期")
            return self.max_cycle

        webster_cycle = int(np.round(1.5 * np.sum(l) / (1 - np.sum(y))))
        webster_cycle = max(webster_cycle, self.min_cycle)
        webster_cycle = min(webster_cycle, self.max_cycle)

        return webster_cycle


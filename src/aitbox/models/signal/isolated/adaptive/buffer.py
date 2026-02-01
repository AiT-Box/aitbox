#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project : aitbox
# @File : buffer.py
# @Author : run
# @Date : 2026/1/22 20:51
from dataclasses import dataclass

from typing import Deque, Tuple
from collections import deque

import numpy as np
import random


@dataclass
class Sample:
    state: np.ndarray
    action: np.ndarray
    reward: np.ndarray
    next_state: np.ndarray
    done: False


@dataclass
class Buffer:
    capacity: int
    samples: Deque[Sample] = None

    def __post_init__(self):
        if self.samples is None:
            self.samples = deque(maxlen=self.capacity)

    def add(self, state: np.ndarray, action: np.ndarray,
            reward: np.ndarray, next_state: np.ndarray, done: bool = False) -> None:
        """添加单个样本到缓冲区"""
        sample = Sample(
            state=state,
            action=action,
            reward=reward,
            next_state=next_state,
            done=done
        )
        self.samples.append(sample)

    def add_batch(self, states: np.ndarray, actions: np.ndarray,
                  rewards: np.ndarray, next_states: np.ndarray, dones: np.ndarray) -> None:
        """批量添加样本"""
        for i in range(len(states)):
            self.add(states[i], actions[i], rewards[i], next_states[i], bool(dones[i]))

    def sample(self, batch_size: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """随机采样一批数据"""
        batch_size = min(batch_size, len(self.samples))
        batch_samples = random.sample(list(self.samples), batch_size)

        states = np.array([s.state for s in batch_samples])
        actions = np.array([s.action for s in batch_samples])
        rewards = np.array([s.reward for s in batch_samples]).flatten()
        next_states = np.array([s.next_state for s in batch_samples])
        dones = np.array([s.done for s in batch_samples]).flatten()

        return states, actions, rewards, next_states, dones

    def size(self) -> int:
        """返回当前缓冲区大小"""
        return len(self.samples)

    def is_full(self) -> bool:
        """检查缓冲区是否已满"""
        return len(self.samples) == self.capacity

    def clear(self) -> None:
        """清空缓冲区"""
        self.samples.clear()

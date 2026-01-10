#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File        : base.py
Project     : aitbox
Author      : gdd
Created     : 2025-12-28
Description :
"""

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import torch
import torch.nn as nn


@dataclass
class StepOutput:
    """ """

    loss: Any
    prediction: Any


class TestModelBase(ABC, nn.Module):
    """ """

    def __init__(self, model: nn.Module):
        """ """
        super().__init__()
        self.model = model

    @torch.no_grad()
    @abstractmethod
    def test_step(self, batch: Any) -> StepOutput:
        """ """
        ...


class TrainModelBase(TestModelBase):
    """ """

    def __init__(self, model: nn.Module):
        """ """
        super().__init__(model)
        self.criterion = self.configure_criterion()

    @abstractmethod
    def train_step(self, batch: Any) -> StepOutput:
        """"""
        ...

    @torch.no_grad()
    @abstractmethod
    def validate_step(self, batch: Any) -> StepOutput:
        """ """
        ...
    
    def test_step(self, batch: Any) -> StepOutput:
        """ """
        return self.validate_step(batch)

    @abstractmethod
    def configure_criterion(self) -> nn.Module:
        """ """
        ...

    @abstractmethod
    def configure_optimizer(self) -> nn.Module:
        """ """
        ...

    @abstractmethod
    def compute_loss(self, prediction: Any, ground_truth: Any, *args, **kwargs):
        """"""
        ...
        
    def save_model(self, save_path):
        """ """
        os.makedirs(save_path, exist_ok=True)
        torch.save(self.model.state_dict(), save_path)

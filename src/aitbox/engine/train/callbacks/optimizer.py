#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File        : optimizer.py
Project     : aitbox
Author      : gdd
Created     : 2026-01-10
Description :
"""

from typing import TYPE_CHECKING

import torch.distributed as dist

from aitbox.engine.train.callbacks.base import Callback

if TYPE_CHECKING:
    from aitbox.engine.train.trainer import Trainer


class BaseOptimzerCallback(Callback):
    """ """

    caller: "Trainer"


class OptimizerCallback(BaseOptimzerCallback):
    """ """

    def __init__(self):
        """ """
        super().__init__()
        self.ctx = None

    def configure_optimizer(self):
        """ """
        self.caller.optimizer = self.caller.model.configure_optimizer()

    def before_batch_train(self):
        """ """
        if dist.is_available() and dist.is_initialized():
            if not self.caller.batch_result_data.batch_idx % self.caller.grad_accumulate_step == 0:
                self.ctx = self.caller.model.no_sync()
                self.ctx.__enter__()

    def after_batch_train_backward(self):
        """ """
        if dist.is_available() and dist.is_initialized():
            if not self.caller.batch_result_data.batch_idx % self.caller.grad_accumulate_step == 0:
                self.ctx.__exit__(None, None, None)

    def optimizer(self):
        """ """
        if self.caller.batch_result_data.batch_idx % self.caller.grad_accumulate_step == 0:
            self.caller.optimizer.step()
            self.caller.optimizer.zero_grad()

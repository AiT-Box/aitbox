#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File        : loss.py
Project     : aitbox
Author      : gdd
Created     : 2026-01-10
Description :
"""

from typing import TYPE_CHECKING

from aitbox.engine.train.callbacks.base import Callback

if TYPE_CHECKING:
    from aitbox.engine.train.trainer import Trainer


class BaseLossCallback(Callback):
    """ """

    caller: "Trainer"


class LossCallback(BaseLossCallback):
    """ """

    def backward(self):
        """ """
        loss = self.caller.batch_result_data.batch_loss / self.caller.grad_accumulate_step
        loss.backward()

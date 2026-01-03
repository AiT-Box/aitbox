#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File        : wrapper.py
Project     : aitbox
Author      : gdd
Created     : 2026-01-02
Description :
"""

import functools

import torch.distributed as dist
from torch.utils.data import DataLoader, DistributedSampler


class InfiniteLoader:
    """ """

    def __init__(self, loader: DataLoader):
        """ """
        self.loader = loader
        self.iterator = iter(loader)
        self.num_iter = 1

    def __iter__(self):
        """ """
        return self

    def __next__(self):
        """ """
        try:
            return next(self.iterator)
        except StopIteration:
            self.num_iter += 1
            self.set_epoch()
            self.iterator = iter(self.loader)
            return next(self.iterator)

    def __len__(self):
        """ """
        return len(self.loader)

    def __getattr__(self, name):
        """ """
        if name in self.__dict__:
            return self.__dict__[name]
        elif hasattr(self.loader, name):
            return getattr(self.loader, name)
        else:
            raise AttributeError(f"'InfiniteLoader' has no attribute '{name}'")

    def set_epoch(self):
        """ """
        if isinstance(self.loader.sampler, DistributedSampler):
            self.loader.sampler.set_epoch(self.num_iter)


def ddp_master_only(func):
    """ """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        """ """
        if not dist.is_available() or not dist.is_initialized():
            return func(*args, **kwargs)
        if dist.get_rank() == 0:
            return func(*args, **kwargs)
        return None

    return wrapper

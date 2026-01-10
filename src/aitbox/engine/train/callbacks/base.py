#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File        : base.py
Project     : aitbox
Author      : gdd
Created     : 2026-01-02
Description :
"""

from abc import ABC, abstractmethod
from bisect import bisect_right
from typing import List


class Callback(ABC):
    """ """

    caller: "CallbackMixin" = None
    weight: float = 0

    @classmethod
    def set_caller(cls, caller: "CallbackMixin"):
        """ """
        cls.caller = caller

    @classmethod
    def set_weight(cls, weight: float):
        """ """
        cls.weight = weight

    @property
    def name(self):
        """ """
        return self.__class__.name


class CallbacksContainer(ABC):
    """ """

    @abstractmethod
    def add(self, callback: Callback):
        """ """
        ...

    @abstractmethod
    def remove(self, callback_cls_str):
        """ """
        ...

    @abstractmethod
    def get(self, callback_cls_str):
        """ """
        ...
        
    @abstractmethod
    def replace(self, callback_cls_str, new_callback):
        """ """
        ...


class CallbacksList(CallbacksContainer):
    """ """

    def __init__(self):
        """ """
        super().__init__()
        self._callbacks: List[Callback] = []

    def add(self, callback: Callback) -> None:
        """ """
        weight = getattr(callback, "weight", 0)
        weights = [-getattr(cb, "weight", 0) for cb in self._callbacks]
        index = bisect_right(weights, -weight)
        self._callbacks.insert(index, callback)

    def remove(self, callback_cls_str) -> None:
        """ """
        for i, callback in enumerate(self._callbacks):
            if callback.name == callback_cls_str:
                self._callbacks.pop(i)
                break

    def get(self, callback_cls_str) -> Callback | None:
        """ """
        for callback in self._callbacks:
            if callback.name == callback_cls_str:
                return callback
        return None
    
    def replace(self, callback_cls_str, new_callback: Callback) -> None:
        """ """
        for index, callback in enumerate(self._callbacks):
            if callback.name == callback_cls_str:
                new_callback.set_caller(callback.caller)
                self._callbacks[index] = new_callback

    def __iter__(self):
        """ """
        return iter(self._callbacks)

    def __len__(self):
        """ """
        return len(self._callbacks)


class CallbackMixin:
    """ """

    def __init__(self, *args, **kwargs):
        """ """
        super().__init__(*args, **kwargs)
        self.callbacks = CallbacksList()

    def init_callbacks(self, callbacks: Callback | List[Callback]):
        """ """
        if isinstance(callbacks, Callback):
            callbacks = [callbacks]
        for callback in callbacks:
            callback.set_caller(self)
            self.callbacks.add(callback)

    def remove_callback(self, callback_cls_str):
        """ """
        self.callbacks.remove(callback_cls_str)

    def add_callback(self, callback: Callback):
        """ """
        callback.set_caller(self)
        self.callbacks.add(callback)

    def get_callback(self, callback_cls_str):
        """ """
        return self.callbacks.get(callback_cls_str)
    
    def replace_callback(self, callback_cls_str, new_callback):
        """ """
        return self.callbacks.replace(callback_cls_str, new_callback)

    def __call__(self, name: str, *args, **kwargs):
        """ """
        for cb in self.callbacks:
            attr = getattr(cb, name, None)
            if attr is not None:
                attr(*args, **kwargs)

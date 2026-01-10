#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File        : road_network.py
Project     : aitbox
Author      : gdd
Created     : 2026-01-10
Description :
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import List

from shapely.geometry import Point


@dataclass
class RoadNetwork:
    """ """
    cross: List["Cross"]
    road_segment: List["RoadSegment"]


class CrossType(Enum):
    """ """
    pass


@dataclass
class Cross:
    """ """
    id: str | int
    name: str
    type: CrossType
    location: Point
    branch: List["Branch"]


class BranchType(Enum):
    """ """
    IN = auto()
    OUT = auto()


class DirectionType(Enum):
    """ """
    EAST = auto()
    SOUTH = auto()
    WEST = auto()
    NORTH = auto()
    

class Branch:
    """ """
    id: str | int
    name: str
    type: BranchType
    direction: DirectionType


class RoadSegment:
    """ """
    pass

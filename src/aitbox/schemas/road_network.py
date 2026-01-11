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

from shapely import LineString, Point


@dataclass
class RoadNetwork:
    """ """
    cross: List["Cross"]
    road_segment: List["RoadSegment"]


class CrossType(Enum):
    """ """
    NORMAL = auto()
    SIGNAL = auto()


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
    EAST_NORTH = auto()
    WEST_NORTH = auto()
    WEST_SOUTH = auto()
    EAST_SOUTH = auto()


@dataclass
class Branch:
    """ """
    id: str | int
    name: str
    type: BranchType
    direction: DirectionType
    geom: LineString
    lane: List["Lane"]
    

class LaneTurnType(Enum):
    """ """
    pass


@dataclass
class Lane:
    """ """
    id: str | int
    seq_num: int
    group: int
    broaden: bool
    flow_type: BranchType
    turn_type: LaneTurnType


class RoadSegment:
    """ """
    pass

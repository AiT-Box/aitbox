#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File        : road_network.py
Project     : aitbox
Author      : gdd
Created     : 2026-01-10
Description : Road network domain model
"""

from dataclasses import dataclass
from enum import Enum, IntFlag, auto
from typing import List, Union

from shapely.geometry import LineString, Point


# =========================
# Road Network
# =========================

@dataclass
class RoadNetwork:
    """Road network"""
    cross: List["Cross"]
    road_segment: List["RoadSegment"]


# =========================
# Cross / Intersection
# =========================

class CrossType(str, Enum):
    """Intersection type"""
    NORMAL = "normal"
    SIGNAL = "signal"


@dataclass
class Cross:
    """Intersection"""
    id: str | int
    name: str
    type: CrossType
    location: Point
    branch: List["Branch"]


# =========================
# Branch
# =========================

class BranchType(str, Enum):
    """Branch direction relative to intersection"""
    IN = "in"
    OUT = "out"


class DirectionType(str, Enum):
    """Geometric direction"""
    EAST = "east"
    SOUTH = "south"
    WEST = "west"
    NORTH = "north"

    EAST_NORTH = "east_north"
    WEST_NORTH = "west_north"
    WEST_SOUTH = "west_south"
    EAST_SOUTH = "east_south"


@dataclass
class Branch:
    """Intersection branch"""
    id: str | int
    name: str
    type: BranchType
    direction: DirectionType
    geom: LineString
    lane: List["Lane"]


# =========================
# Lane
# =========================

class LaneType(str, Enum):
    """Lane functional type"""
    REGULAR = "regular"
    BUS_ONLY = "bus_only"
    VARIABLE = "variable"


class LaneTurnType(IntFlag):
    """Allowed turning movements of a lane"""

    STRAIGHT = auto()
    LEFT = auto()
    RIGHT = auto()
    UTURN = auto()

    # Common combinations (semantic shortcuts)
    STRAIGHT_LEFT = STRAIGHT | LEFT
    STRAIGHT_RIGHT = STRAIGHT | RIGHT
    STRAIGHT_UTURN = STRAIGHT | UTURN

    LEFT_RIGHT = LEFT | RIGHT
    LEFT_UTURN = LEFT | UTURN
    RIGHT_UTURN = RIGHT | UTURN

    STRAIGHT_LEFT_RIGHT = STRAIGHT | LEFT | RIGHT
    STRAIGHT_LEFT_UTURN = STRAIGHT | LEFT | UTURN
    STRAIGHT_RIGHT_UTURN = STRAIGHT | RIGHT | UTURN

    LEFT_RIGHT_UTURN = LEFT | RIGHT | UTURN
    ALL = STRAIGHT | LEFT | RIGHT | UTURN


@dataclass
class Lane:
    """Lane"""
    id: str | int
    seq_num: int
    group: int
    broaden: bool
    flow_type: BranchType
    turn_type: LaneTurnType
    lane_type: LaneType = LaneType.REGULAR
    width: float = 3.5


# =========================
# Road Segment
# =========================

@dataclass
class RoadSegment:
    """Road segment between two intersections"""
    id: str | int
    name: str
    geom: LineString
    length: float
    start_branch_id: str | int
    end_branch_id: str | int
    start_cross_id: str | int
    end_cross_id: str | int

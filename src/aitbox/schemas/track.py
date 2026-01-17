#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File        : track
Project     : aitbox
Author      : gdd
Created     : 2026/1/5
Description :
"""

from abc import abstractmethod, ABC
from dataclasses import dataclass, replace
from enum import Enum, auto
from typing import Tuple, Type

import pandas as pd
import polars as pl


class CoordinateType(Enum):
    """ """

    EUCLIDEAN = auto()
    WGS84 = auto()
    BD09 = auto()


@dataclass(frozen=True)
class CoordinateSpec:
    columns: Tuple[str, str, str, str]
    unit: str
    description: str
    epsg: int | None = None


COORDINATE_SPECS = {
    CoordinateType.EUCLIDEAN: CoordinateSpec(
        columns=("track_id", "x", "y", "time"),
        unit="meter",
        description="Local 2D Cartesian coordinate",
        epsg=None,
    ),
    CoordinateType.WGS84: CoordinateSpec(
        columns=("track_id", "lon", "lat", "time"),
        unit="degree",
        description="WGS84 geographic coordinate",
        epsg=4326,
    ),
    CoordinateType.BD09: CoordinateSpec(
        columns=("track_id", "lon", "lat", "time"),
        unit="degree",
        description="Baidu BD09 coordinate",
        epsg=None,
    ),
}


@dataclass
class TrackBase:
    """ """

    data: pd.DataFrame | pl.DataFrame
    coord_type: CoordinateType
    time_format: str | None = None

    @abstractmethod
    def __post_init__(self):
        """ """
        ...

    def _inplace(self, data, inplace):
        """ """
        if inplace:
            self.data = data
            return self
        else:
            return replace(self, data=data)

    @property
    def required_columns(self) -> tuple:
        """ """
        return COORDINATE_SPECS[self.coord_type].columns

    @property
    def coordinate_specs(self) -> CoordinateSpec:
        """ """
        return COORDINATE_SPECS[self.coord_type]


@dataclass
class TrackPd(TrackBase):
    """ """

    def __post_init__(self):
        """ """
        self._validate_columns()

    def _validate_columns(self):
        """ """
        required = set(self.required_columns)
        existing = set(self.data.columns)

        missing = required - existing
        if missing:
            raise ValueError(f"Missing required columns: {sorted(missing)}")

    @classmethod
    def from_dataframe(
        cls, data: pd.DataFrame, coord_type: CoordinateType | None = None, **kwargs
    ) -> "TrackPd":
        """ """
        if coord_type is None:
            coord_type = CoordinateType.EUCLIDEAN
        return cls(data=data, coord_type=coord_type, **kwargs)

    @classmethod
    def from_csv(cls, path: str, coord_type: CoordinateType | None = None, **kwargs) -> "TrackPd":
        """ """
        df = pd.read_csv(path, **kwargs)
        return cls.from_dataframe(df, coord_type)

    def sample_by_distance(self, distance_th, inplace=True, *args, **kwargs):
        """ """

        from aitbox.preprocessing.track.pd.downsample import sample_by_distance

        data = sample_by_distance(self.data, distance_th, *args, **kwargs)
        return self._inplace(data, inplace)

@dataclass
class TrackPl(TrackBase):
    """ """

    def __post_init__(self):
        """ """
        self._validate_columns()

    def _validate_columns(self):
        """ """
        required = set(self.required_columns)
        existing = set(self.data.columns)

        missing = required - existing
        if missing:
            raise ValueError(f"Missing required columns: {sorted(missing)}")

    @classmethod
    def from_dataframe(
        cls, data: pl.DataFrame, coord_type: CoordinateType | None = None, **kwargs
    ) -> "TrackPl":
        """ """
        if coord_type is None:
            coord_type = CoordinateType.EUCLIDEAN
        return cls(data=data, coord_type=coord_type, **kwargs)

    @classmethod
    def from_csv(cls, path: str, coord_type: CoordinateType | None = None, **kwargs) -> "TrackPl":
        """ """
        df = pl.read_csv(path, **kwargs)
        return cls.from_dataframe(df, coord_type)


TRACK_BACKEND = {
    "pandas": TrackPd,
    "polars": TrackPl,
}
BACKEND: str = "pandas"


def set_track_backend(backend: str) -> None:
    """ """
    if backend not in TRACK_BACKEND:
        raise ValueError(f"Unknown backend: {backend}")
    global BACKEND
    BACKEND = backend


def get_track_backend() -> Type[TrackBase]:
    """ """
    return TRACK_BACKEND[BACKEND]


class Track(ABC):
    """ """

    def __new__(cls, data=None, coord_type=None, **kwargs):
        """ """
        if cls is not Track:
            return super().__new__(cls)

        backend_cls = get_track_backend()
        if coord_type is None:
            coord_type = CoordinateType.EUCLIDEAN
        return backend_cls(data=data, coord_type=coord_type, ti, **kwargs)

    @classmethod
    def from_dataframe(cls, data, coord_type=None, **kwargs):
        """ """
        backend_cls = get_track_backend()
        return backend_cls.from_dataframe(data, coord_type, **kwargs)

    @classmethod
    def from_csv(cls, path: str, coord_type=None, **kwargs):
        """ """
        backend_cls = get_track_backend()
        return backend_cls.from_csv(path, coord_type, **kwargs)

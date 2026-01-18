#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File        : test_track
Project     : aitbox
Author      : gdd
Created     : 2026/1/5
Description :
"""
import pytest

import pandas as pd
import polars as pl

from aitbox.schemas.track import CoordinateType, TrackPd, Track, TrackPl, set_track_backend


def test_track_pd():
    """ """
    track = Track(
        data=pd.DataFrame(
            {
                "time": [0, 1, 2],
                "x": [0.0, 1.0, 2.0],
                "y": [0.0, 1.0, 2.0],
                "track_id": [0, 0, 0]
            }
        ),
        coord_type=CoordinateType.EUCLIDEAN,
    )

    assert isinstance(track, TrackPd)
    assert track.coord_type == CoordinateType.EUCLIDEAN


def test_track_pl():
    """ """
    set_track_backend("polars")

    track = Track(
        data=pl.DataFrame(
            {
                "time": [0, 1, 2],
                "x": [0.0, 1.0, 2.0],
                "y": [0.0, 1.0, 2.0],
                "track_id": [0, 0, 0]
            }
        ),
        coord_type=CoordinateType.EUCLIDEAN,
    )

    assert isinstance(track, TrackPl)
    assert track.coord_type == CoordinateType.EUCLIDEAN


def test_track_pd_columns():
    """ """
    with pytest.raises(ValueError, match="Missing required columns"):
        Track(
            data=pd.DataFrame(
                {
                    "x": [0.0, 1.0, 2.0],
                    "y": [0.0, 1.0, 2.0],
                }
            ),
            coord_type=CoordinateType.EUCLIDEAN,
        )


def test_track_pl_columns():
    """ """
    set_track_backend("polars")

    with pytest.raises(ValueError, match="Missing required columns"):
        Track(
            data=pl.DataFrame(
                {
                    "x": [0.0, 1.0, 2.0],
                    "y": [0.0, 1.0, 2.0],
                }
            ),
            coord_type=CoordinateType.EUCLIDEAN,
        )


def test_track_pd_from_dataframe():
    """ """
    data = pd.DataFrame(
        {
            "time": [0, 1, 2],
            "x": [0.0, 1.0, 2.0],
            "y": [0.0, 1.0, 2.0],
            "track_id": [0, 0, 0]
        }
    )
    track = Track.from_dataframe(data)
    assert isinstance(track, TrackPd)


def test_track_pl_from_dataframe():
    """ """
    set_track_backend("polars")

    data = pd.DataFrame(
        {
            "time": [0, 1, 2],
            "x": [0.0, 1.0, 2.0],
            "y": [0.0, 1.0, 2.0],
            "track_id": [0, 0, 0]
        }
    )
    track = Track.from_dataframe(data)
    assert isinstance(track, TrackPl)


def test_track_pd_from_csv():
    """ """
    path = r'../../tests/data/track/track_isolated_noise.csv'
    track = Track.from_csv(path, coord_type=CoordinateType.GCJ02)
    assert isinstance(track, TrackPd)


def test_track_pl_from_csv():
    """ """
    set_track_backend("polars")

    path = r'../../tests/data/track/track_isolated_noise.csv'
    track = Track.from_csv(path, coord_type=CoordinateType.GCJ02)
    assert isinstance(track, TrackPl)
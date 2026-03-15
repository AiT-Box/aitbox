import math
import pytest
import polars as pl

# 假设被测试函数位于模块 denoising 中
from src.aitbox.utils.track.track_utils import cal_haversine_dis, cal_haversine_dis_vector_polars, cal_haversine_dis_vector_numpy
from src.aitbox.preprocessing.track.pl.denoising import Denoising


def test_same_point():
    """相同点距离应为 0"""
    assert cal_haversine_dis((0, 0), (0, 0)) == 0
    assert cal_haversine_dis((40.7128, -74.0060), (40.7128, -74.0060)) == 0

    df = pl.DataFrame({
        "lon": [0.0, 0.0],
        "lat": [0.0, 0.0]
    })
    distances = cal_haversine_dis_vector_polars(df)
    expected = 0
    assert distances[0] == pytest.approx(expected, rel=1e-5)

    distances = cal_haversine_dis_vector_numpy(df)
    expected = 0
    assert distances[0] == pytest.approx(expected, rel=1e-5)

def test_points_from_csv():
    path = '../../../tests/data/track/track_isolated_noise.csv'
    df = pl.read_csv(path)

    distances = cal_haversine_dis_vector_numpy(df)
    assert len(distances) == df.height - 1

def test_track_denoising():
    path = '../../../tests/data/track/track_isolated_noise.csv'
    df = pl.read_csv(path)

    denoising = Denoising(df)
    result = denoising.process()
    assert result["noise_num"] == 1


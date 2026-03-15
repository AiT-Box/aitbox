import math
import numpy as np
import polars as pl
from typing import List, Tuple, Dict, Any


def cal_haversine_dis(cur_point: Tuple[float, float], next_point: Tuple[float, float]) -> float:
    """
    采用haversine公式，根据坐标计算距离
    :param cur_point: 点的坐标
    :param next_point: 另一个点的坐标
    :return: 距离（单位：m）
    """
    AVG_EARTH_RADIUS = 6371.0088  # in kilometers

    lon1, lat1 = cur_point
    lon2, lat2 = next_point
    # 转换为弧度
    lon1_rad, lat1_rad, lon2_rad, lat2_rad = map(math.radians, [lon1, lat1, lon2, lat2])

    d_lon = lon2_rad - lon1_rad
    d_lat = lat2_rad - lat1_rad
    d = math.sin(d_lat * 0.5) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(d_lon * 0.5) ** 2
    d = 2 * AVG_EARTH_RADIUS * math.asin(math.sqrt(d))  # in kilometers
    return d * 1000


def cal_haversine_dis_vector_polars(df: pl.DataFrame) -> np.ndarray:
    """
    向量化计算相邻点之间的球面距离（单位：m），返回距离数组
    :param df: 轨迹数据，要求有lng、lat列（用于计算距离）
    :return: 距离数组
    """
    AVG_EARTH_RADIUS = 6371.0088  # in kilometers

    # 将经纬度转换为弧度（假设输入是度数）
    lon_rad = pl.col("lon").radians()
    lat_rad = pl.col("lat").radians()

    # 计算相邻点的差值
    dlon = lon_rad.shift(-1) - lon_rad
    dlat = lat_rad.shift(-1) - lat_rad

    # Haversine 公式
    half_dlat = dlat / 2
    half_dlon = dlon / 2
    a = (half_dlat.sin() ** 2 +
         lat_rad.cos() * lat_rad.shift(-1).cos() * half_dlon.sin() ** 2)
    c = 2 * a.sqrt().arcsin()

    # 距离（米）
    distance = AVG_EARTH_RADIUS * c * 1000

    # 执行计算，并去掉最后一个NaN（对应最后一行）
    return df.select(distance).to_numpy().flatten()[:-1]


def cal_haversine_dis_vector_numpy(df: pl.DataFrame) -> np.ndarray:
    """
    使用numpy向量化计算，性能更高
    """
    AVG_EARTH_RADIUS = 6371.0088  # in kilometers

    # 转换为numpy数组
    lon = np.radians(df["lon"].to_numpy())
    lat = np.radians(df["lat"].to_numpy())

    # 计算相邻差值
    dlon = lon[1:] - lon[:-1]
    dlat = lat[1:] - lat[:-1]

    # Haversine公式
    a = np.sin(dlat / 2) ** 2 + np.cos(lat[:-1]) * np.cos(lat[1:]) * np.sin(dlon / 2) ** 2
    c = 2 * np.arcsin(np.sqrt(a))

    # 计算距离
    distance = AVG_EARTH_RADIUS * c
    return distance * 1000

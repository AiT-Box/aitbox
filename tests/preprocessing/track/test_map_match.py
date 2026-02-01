#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File        : test_map_match
Project     : aitbox
Author      : gdd
Created     : 2026/1/18
Description : 地图匹配单元测试，含 matplotlib 可视化
"""

from __future__ import annotations

import numpy as np
import pytest

from aitbox.preprocessing.track.pd.map_match import map_match


def _sample_road_network():
    nodes = [
        {"id": "n1", "name": "路口1", "x": 116.38, "y": 39.90},
        {"id": "n2", "name": "路口2", "x": 116.39, "y": 39.90},
        {"id": "n3", "name": "路口3", "x": 116.39, "y": 39.91},
        {"id": "n4", "name": "路口4", "x": 116.38, "y": 39.91},
    ]
    edges = [
        {
            "id": "e1",
            "name": "路段1",
            "length": 1200.0,
            "start_node_id": "n1",
            "end_node_id": "n2",
            "geom": [[116.38, 39.90], [116.385, 39.90], [116.39, 39.90]],
        },
        {
            "id": "e2",
            "name": "路段2",
            "length": 1200.0,
            "start_node_id": "n2",
            "end_node_id": "n3",
            "geom": [[116.39, 39.90], [116.39, 39.905], [116.39, 39.91]],
        },
        {
            "id": "e3",
            "name": "路段3",
            "length": 1200.0,
            "start_node_id": "n3",
            "end_node_id": "n4",
            "geom": [[116.39, 39.91], [116.385, 39.91], [116.38, 39.91]],
        },
        {
            "id": "e4",
            "name": "路段4",
            "length": 1200.0,
            "start_node_id": "n4",
            "end_node_id": "n1",
            "geom": [[116.38, 39.91], [116.38, 39.905], [116.38, 39.90]],
        },
    ]
    return {"nodes": nodes, "edges": edges}


def _sample_track():
    return np.ascontiguousarray(
        [
            [116.381, 39.901, 0.0],
            [116.385, 39.899, 1.0],
            [116.39, 39.9005, 2.0],
            [116.391, 39.902, 3.0],
            [116.389, 39.906, 4.0],
            [116.388, 39.91, 5.0],
            [116.385, 39.91, 6.0],
        ],
        dtype=np.float64,
    )


@pytest.fixture
def road_network():
    return _sample_road_network()


@pytest.fixture
def tracks():
    return [_sample_track()]


def test_map_match_basic(road_network, tracks):
    results = map_match(
        road_network=road_network,
        tracks=tracks,
        track_ids=["track_001"],
        gps_sigma=50.0,
        beta=5.0,
        search_radius=200.0,
    )
    assert len(results) == len(tracks)
    assert results[0] is not None, (
        "地图匹配结果为 None, 请确认已编译 Rust 扩展：在项目根目录执行 maturin develop"
    )
    r = results[0]
    assert "matched_points" in r and "edge_ids" in r
    assert r["matched_points"].shape[0] == len(tracks[0])
    assert r["matched_points"].shape[1] == 2
    assert len(r["edge_ids"]) == r["matched_points"].shape[0]
    assert "log_probability" in r and isinstance(r["log_probability"], (int, float))
    assert r["edge_ids"][-1] == "e3"


def test_map_match_visualize(road_network, tracks):
    pytest.importorskip("matplotlib")
    import matplotlib.pyplot as plt

    results = map_match(
        road_network=road_network,
        tracks=tracks,
        track_ids=["track_001"],
        gps_sigma=50.0,
        beta=5.0,
        search_radius=200.0,
    )
    assert results[0] is not None, (
        "地图匹配结果为 None, 请确认已编译 Rust 扩展：在项目根目录执行 maturin develop"
    )
    raw = tracks[0]
    res = results[0]
    matched = res["matched_points"]

    fig, ax = plt.subplots(figsize=(8, 8))
    for edge in road_network["edges"]:
        geom = np.array(edge["geom"])
        ax.plot(geom[:, 0], geom[:, 1], "k-", linewidth=1.5, alpha=0.7)
        ax.text(
            geom.mean(axis=0)[0],
            geom.mean(axis=0)[1],
            edge["id"],
            fontsize=8,
            ha="center",
        )
    ax.scatter(raw[:, 0], raw[:, 1], c="blue", s=40, label="raw track", zorder=3)
    ax.scatter(
        matched[:, 0],
        matched[:, 1],
        c="red",
        s=60,
        marker="x",
        linewidths=2,
        label="matched",
        zorder=4,
    )
    ax.plot(
        matched[:, 0],
        matched[:, 1],
        "r--",
        alpha=0.6,
        linewidth=1,
        label="matched path",
    )
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_title("map match (track_001)")
    ax.legend(loc="upper left")
    ax.set_aspect("equal")
    ax.grid(True, alpha=0.3)

    plt.show()
    plt.close(fig)

//! -*- coding: utf-8 -*-
//!
//! File        : converters.rs
//! Project     : rust
//! Author      : gdd
//! Created     : 2026/1/25
//! Description : Python 数据格式转换函数

use pyo3::prelude::*;
use pyo3::types::PyDict;
use numpy::{PyArray2, PyArrayMethods, PyReadonlyArray2};

use crate::matching::matching::MatchResult;
use crate::schemas::road_network::{Edge, Node, RoadNetwork};
use crate::schemas::track::{Track, TrackPoint};
use geo_types::{coord, LineString};

// 从 numpy 数组构建轨迹
// 轨迹格式: shape=(n_points, 3), 列是 [x, y, t]
pub fn build_track_from_array(track_id: String, points: &PyReadonlyArray2<f64>) -> PyResult<Track> {
    let array_view = points.as_array();
    let shape = array_view.shape();
    if shape.len() != 2 {
        return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
            "轨迹点数组必须是二维数组 (n_points, 3)",
        ));
    }

    let n_points = shape[0];
    let n_cols = shape[1];

    if n_cols != 3 {
        return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
            "轨迹点数组必须是 3 列 (x, y, t)",
        ));
    }

    let mut track_points = Vec::with_capacity(n_points);
    for i in 0..n_points {
        let x = *points.get([i, 0]).ok_or_else(|| {
            PyErr::new::<pyo3::exceptions::PyIndexError, _>("索引越界")
        })?;
        let y = *points.get([i, 1]).ok_or_else(|| {
            PyErr::new::<pyo3::exceptions::PyIndexError, _>("索引越界")
        })?;
        let time = *points.get([i, 2]).ok_or_else(|| {
            PyErr::new::<pyo3::exceptions::PyIndexError, _>("索引越界")
        })?;

        track_points.push(TrackPoint::from_coords(x, y, time));
    }

    Ok(Track::from_points(track_id, track_points))
}

// 从 Python 字典构建路网
// 期望格式：
// {
//   "nodes": [{"id": str, "name": str, "x": float, "y": float}, ...],
//   "edges": [{"id": str, "name": str, "length": float, "start_node_id": str, 
//              "end_node_id": str, "geom": [[x, y], ...]}, ...]
// }
pub fn build_road_network_from_dict<'py>(_py: Python<'py>, data: &Bound<'py, PyAny>) -> PyResult<RoadNetwork> {
    let nodes_list = data.get_item("nodes")?;

    let edges_list = data.get_item("edges")?;

    // 构建节点
    let nodes: Vec<Node> = nodes_list
        .try_iter()?
        .map(|node_dict| {
            let node_dict: Bound<'_, PyAny> = node_dict?;
            Ok(Node {
                id: node_dict.get_item("id")?.extract::<String>()?,
                name: node_dict.get_item("name")?.extract::<String>().ok().unwrap_or_default(),
                x: node_dict.get_item("x")?.extract::<f64>()?,
                y: node_dict.get_item("y")?.extract::<f64>()?,
            })
        })
        .collect::<PyResult<Vec<Node>>>()?;

    // 构建边
    let edges: Vec<Edge> = edges_list
        .try_iter()?
        .map(|edge_dict| {
            let edge_dict: Bound<'_, PyAny> = edge_dict?;
            
            // 获取几何坐标
            let geom_list = edge_dict.get_item("geom")?;
            
            let coords: Vec<geo_types::Coord<f64>> = geom_list
                .try_iter()?
                .map(|coord_item| {
                    let coord_item: Bound<'_, PyAny> = coord_item?;
                    let coord_list = coord_item.cast_into::<pyo3::types::PyList>()
                        .map_err(|e| PyErr::new::<pyo3::exceptions::PyTypeError, _>(format!("坐标项必须是列表: {}", e)))?;
                    let coord_vec: Vec<f64> = coord_list
                        .iter()
                        .map(|v| {
                            v.extract::<f64>()
                        })
                        .collect::<PyResult<_>>()?;
                    if coord_vec.len() >= 2 {
                        Ok(coord! { x: coord_vec[0], y: coord_vec[1] })
                    } else {
                        Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                            "坐标点必须至少包含 x, y"
                        ))
                    }
                })
                .collect::<PyResult<Vec<geo_types::Coord<f64>>>>()?;
            
            Ok(Edge {
                id: edge_dict.get_item("id")?.extract::<String>()?,
                name: edge_dict.get_item("name")?.extract::<String>().ok().unwrap_or_default(),
                length: edge_dict.get_item("length")?.extract::<f64>()?,
                start_node_id: edge_dict.get_item("start_node_id")?.extract::<String>()?,
                end_node_id: edge_dict.get_item("end_node_id")?.extract::<String>()?,
                geom: LineString::new(coords),
            })
        })
        .collect::<PyResult<Vec<Edge>>>()?;

    Ok(RoadNetwork::from_nodes_and_edges(nodes, edges))
}

// 将匹配结果转换为 Python 字典
pub fn match_result_to_dict<'py>(py: Python<'py>, result: &MatchResult) -> PyResult<Bound<'py, PyAny>> {
    let dict = PyDict::new(py);
    
    // 匹配点坐标数组 (n_points, 2)
    let n_points = result.matched_points.len();
    let mut matched_coords_flat = Vec::with_capacity(n_points * 2);
    let mut edge_ids = Vec::with_capacity(n_points);
    
    for matched in &result.matched_points {
        let point = matched.point();
        matched_coords_flat.push(point.x());
        matched_coords_flat.push(point.y());
        edge_ids.push(matched.edge_id().to_string());
    }
    
    // 创建 (n_points, 2) 的数组
    // 使用 PyArray2::zeros 创建数组然后填充数据
    let coords_array = PyArray2::zeros(py, [n_points, 2], false);
    {
        let mut array_view = unsafe { coords_array.as_array_mut() };
        for (i, val) in matched_coords_flat.iter().enumerate() {
            let row = i / 2;
            let col = i % 2;
            array_view[[row, col]] = *val;
        }
    }
    
    dict.set_item("matched_points", coords_array)?;
    dict.set_item("edge_ids", edge_ids)?;
    dict.set_item("log_probability", result.log_probability)?;
    dict.set_item("path_indices", result.path_indices.clone())?;
    
    Ok(dict.into_pyobject(py)?.into_any())
}

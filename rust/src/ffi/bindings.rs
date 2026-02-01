//! -*- coding: utf-8 -*-
//!
//! File        : bindings.rs
//! Project     : rust
//! Author      : gdd
//! Created     : 2026/1/18
//! Description : Python FFI 绑定

use pyo3::prelude::*;
use numpy::PyReadonlyArray2;

use crate::ffi::converters::{build_road_network_from_dict, build_track_from_array, match_result_to_dict};
use crate::matching::matching::map_match_batch_with_threads;
use crate::matching::viterbi::MatchParams;

/// 地图匹配函数（批量处理多条轨迹）
/// 
/// 参数:
///     road_network: 路网数据字典，包含 nodes 和 edges
///     tracks: 轨迹列表，每个轨迹是 shape=(n_points, 3) 的数组，列是 [x, y, t]
///     track_ids: 轨迹ID列表（可选，默认自动生成）
///     gps_sigma: GPS误差标准差（可选，默认50.0米）
///     beta: 转移概率参数（可选，默认5.0）
///     search_radius: 候选边搜索半径（可选，默认100.0米）
///     num_threads: 线程数（可选，默认0表示使用默认线程数）
/// 
/// 返回:
///     匹配结果列表，每个元素是 result_dict 或 None（如果匹配失败）
#[pyfunction]
#[pyo3(signature = (
    road_network,
    tracks,
    *,
    track_ids = None,
    gps_sigma = None,
    beta = None,
    search_radius = None,
    num_threads = None
))]
pub fn map_match<'py>(
    py: Python<'py>,
    road_network: &Bound<'py, PyAny>,
    tracks: Vec<PyReadonlyArray2<f64>>,
    track_ids: Option<Vec<String>>,
    gps_sigma: Option<f64>,
    beta: Option<f64>,
    search_radius: Option<f64>,
    num_threads: Option<usize>,
) -> PyResult<Vec<Option<Py<PyAny>>>> {
    // 1. 构建路网
    let road_network = build_road_network_from_dict(py, road_network)?;

    // 2. 构建轨迹列表
    let mut rust_tracks = Vec::with_capacity(tracks.len());
    for (i, track_points) in tracks.iter().enumerate() {
        let track_id = track_ids
            .as_ref()
            .and_then(|ids| ids.get(i).cloned())
            .unwrap_or_else(|| format!("track_{:03}", i));
        rust_tracks.push(build_track_from_array(track_id, track_points)?);
    }

    // 3. 构建匹配参数
    let params = MatchParams {
        gps_sigma: gps_sigma.unwrap_or(50.0),
        beta: beta.unwrap_or(5.0),
        search_radius: search_radius.unwrap_or(100.0),
    };

    // 4. 执行批量匹配
    let thread_count = num_threads.unwrap_or(0);
    let results = map_match_batch_with_threads(&rust_tracks, &road_network, &params, thread_count);

    // 5. 转换为 Python 结果
    let mut py_results = Vec::with_capacity(results.len());
    for batch_result in results {
        if let Some(result) = batch_result.result {
            let dict = match_result_to_dict(py, &result)?;
            let py_obj: Py<PyAny> = dict.into_pyobject(py)?.into();
            py_results.push(Some(py_obj));
        } else {
            py_results.push(None);
        }
    }

    Ok(py_results)
}

pub fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(map_match, m)?)?;
    Ok(())
}

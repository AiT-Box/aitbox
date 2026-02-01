//! -*- coding: utf-8 -*-
//!
//! File        : matching.rs
//! Project     : rust
//! Author      : gdd
//! Created     : 2026/1/25
//! Description : 地图匹配入口函数

use rayon::prelude::*;

use crate::matching::candidate::{generate_candidates_for_track, CandidatePoint, TrackCandidates};
use crate::matching::viterbi::{viterbi_backward, viterbi_forward, MatchParams};
use crate::schemas::road_network::RoadNetwork;
use crate::schemas::track::Track;

// 地图匹配结果
#[derive(Debug, Clone)]
pub struct MatchResult {
    // 匹配的候选点序列
    pub matched_points: Vec<CandidatePoint>,
    // 最优路径的对数概率
    pub log_probability: f64,
    // 路径索引（每个时间步的候选点索引）
    pub path_indices: Vec<usize>,
    // 所有候选点列表
    pub candidates: TrackCandidates,
}

// 批量地图匹配结果
#[derive(Debug, Clone)]
pub struct BatchMatchResult {
    // 轨迹 ID
    pub track_id: String,
    // 匹配结果（如果成功）
    pub result: Option<MatchResult>,
}

// 执行完整的地图匹配
// 输入:
//   - track: 轨迹
//   - road_network: 路网
//   - params: 地图匹配参数
// 返回: 匹配结果
pub fn map_match(
    track: &Track,
    road_network: &RoadNetwork,
    params: &MatchParams,
) -> Option<MatchResult> {
    if track.points.is_empty() {
        return None;
    }

    // 1. 生成候选点
    let candidates = generate_candidates_for_track(
        track,
        road_network,
        params.search_radius,
        params.gps_sigma,
    );

    if candidates.is_empty() {
        return None;
    }

    // 2. 前向计算
    let state = viterbi_forward(&candidates, road_network, params.beta)?;

    // 3. 后向回溯
    let path_indices = viterbi_backward(&state);

    if path_indices.is_empty() {
        return None;
    }

    // 4. 提取匹配的候选点
    let mut matched_points = Vec::with_capacity(path_indices.len());
    for (t, &idx) in path_indices.iter().enumerate() {
        if !candidates[t].is_empty() && idx < candidates[t].len() {
            matched_points.push(candidates[t][idx].clone());
        }
    }

    // 5. 计算最终概率
    let n_steps = state.viterbi_prob.len();
    let log_probability = if !state.viterbi_prob[n_steps - 1].is_empty() {
        let last_idx = path_indices[n_steps - 1];
        if last_idx < state.viterbi_prob[n_steps - 1].len() {
            state.viterbi_prob[n_steps - 1][last_idx]
        } else {
            f64::NEG_INFINITY
        }
    } else {
        f64::NEG_INFINITY
    };

    Some(MatchResult {
        matched_points,
        log_probability,
        path_indices,
        candidates,
    })
}

// 批量地图匹配（并行处理多条轨迹）
// 输入:
//   - tracks: 轨迹列表
//   - road_network: 路网
//   - params: 地图匹配参数
// 返回: 批量匹配结果
pub fn map_match_batch(
    tracks: &[Track],
    road_network: &RoadNetwork,
    params: &MatchParams,
) -> Vec<BatchMatchResult> {
    tracks
        .par_iter()
        .map(|track| BatchMatchResult {
            track_id: track.id.clone(),
            result: map_match(track, road_network, params),
        })
        .collect()
}

// 批量地图匹配（带自定义线程数）
// 输入:
//   - tracks: 轨迹列表
//   - road_network: 路网
//   - params: 地图匹配参数
//   - num_threads: 线程数（0 表示使用默认线程数）
// 返回: 批量匹配结果
pub fn map_match_batch_with_threads(
    tracks: &[Track],
    road_network: &RoadNetwork,
    params: &MatchParams,
    num_threads: usize,
) -> Vec<BatchMatchResult> {
    if num_threads == 0 {
        return map_match_batch(tracks, road_network, params);
    }

    let pool = rayon::ThreadPoolBuilder::new()
        .num_threads(num_threads)
        .build()
        .unwrap();

    pool.install(|| map_match_batch(tracks, road_network, params))
}

// 仅返回成功匹配的结果
pub fn map_match_batch_successful(
    tracks: &[Track],
    road_network: &RoadNetwork,
    params: &MatchParams,
) -> Vec<(String, MatchResult)> {
    tracks
        .par_iter()
        .filter_map(|track| {
            map_match(track, road_network, params).map(|result| (track.id.clone(), result))
        })
        .collect()
}

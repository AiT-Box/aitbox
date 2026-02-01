//! -*- coding: utf-8 -*-
//!
//! File        : transition.rs
//! Project     : rust
//! Author      : gdd
//! Created     : 2026/1/25
//! Description : 转移概率计算

use geo_types::Point;

use crate::geometry::geometry::smart_distance;
use crate::matching::candidate::CandidatePoint;
use crate::schemas::road_network::RoadNetwork;

// 计算两点之间的智能距离（自动选择地理距离或欧氏距离）
fn distance_between_points(x1: f64, y1: f64, x2: f64, y2: f64) -> f64 {
    let p1 = Point::new(x1, y1);
    let p2 = Point::new(x2, y2);
    smart_distance(&p1, &p2)
}

// 计算转移概率（对数形式，数值稳定）
// 使用指数分布模型: P(c_i → c_j) = (1/β) * exp(-|d_route - d_direct| / β)
// 对数形式: ln(P) = -ln(β) - |d_route - d_direct| / β
// 参数:
//   - route_distance: 沿路网的距离
//   - direct_distance: 轨迹点之间的直线距离
//   - beta: 转移概率参数
pub fn compute_transition_prob(route_distance: f64, direct_distance: f64, beta: f64) -> f64 {
    let diff = (route_distance - direct_distance).abs();
    -beta.ln() - diff / beta
}

// 计算两个候选点之间沿路网的距离
pub fn compute_route_distance(
    from_candidate: &CandidatePoint,
    to_candidate: &CandidatePoint,
    road_network: &RoadNetwork,
) -> f64 {
    from_candidate.compute_distance_to(to_candidate, road_network)
}

// 计算相邻轨迹点候选点之间的转移概率矩阵
// 输入:
//   - prev_candidates: 前一个轨迹点的候选点列表
//   - curr_candidates: 当前轨迹点的候选点列表
//   - prev_track_point: 前一个轨迹点坐标 (x, y)
//   - curr_track_point: 当前轨迹点坐标 (x, y)
//   - road_network: 路网
//   - beta: 转移概率参数
// 返回: 转移概率矩阵 [prev_candidates.len()][curr_candidates.len()]
pub fn compute_transition_matrix(
    prev_candidates: &[CandidatePoint],
    curr_candidates: &[CandidatePoint],
    prev_track_point: (f64, f64),
    curr_track_point: (f64, f64),
    road_network: &RoadNetwork,
    beta: f64,
) -> Vec<Vec<f64>> {
    // 计算两个轨迹点之间的智能距离（自动选择地理距离或欧氏距离）
    let direct_distance = distance_between_points(
        prev_track_point.0,
        prev_track_point.1,
        curr_track_point.0,
        curr_track_point.1,
    );

    // 计算转移概率矩阵
    prev_candidates
        .iter()
        .map(|prev_cand| {
            curr_candidates
                .iter()
                .map(|curr_cand| {
                    let route_distance =
                        compute_route_distance(prev_cand, curr_cand, road_network);
                    compute_transition_prob(route_distance, direct_distance, beta)
                })
                .collect()
        })
        .collect()
}

//! -*- coding: utf-8 -*-
//!
//! File        : candidate.rs
//! Project     : rust
//! Author      : gdd
//! Created     : 2026/1/18
//! Description : 候选点定义

use std::f64::consts::PI;

use geo_types::Point;

use crate::geometry::geometry::{project_point_to_edge, ProjectionPoint};
use crate::schemas::road_network::RoadNetwork;
use crate::schemas::track::{Track, TrackPoint};

// 候选点结构体，继承自 ProjectionPoint
#[derive(Debug, Clone)]
pub struct CandidatePoint {
    // 投影信息（继承自 ProjectionPoint）
    pub projection: ProjectionPoint,
    // 观测概率（对数形式，数值稳定）
    pub observation_prob: f64,
    // 原始轨迹点坐标
    pub track_point: Point<f64>,
}

impl CandidatePoint {
    // 从 ProjectionPoint 创建 CandidatePoint
    // 默认使用对数概率（数值稳定）
    pub fn from_projection(projection: ProjectionPoint, track_point: Point<f64>, gps_sigma: f64) -> Self {
        let observation_prob = Self::compute_observation_prob(projection.distance, gps_sigma);
        Self {
            projection,
            observation_prob,
            track_point,
        }
    }

    // 计算观测概率（对数形式，数值稳定）
    // ln(P) = -ln(σ * sqrt(2π)) - d² / (2σ²)
    // 参数:
    //   - distance: 轨迹点到候选点的距离
    //   - sigma: GPS 测量误差的标准差
    pub fn compute_observation_prob(distance: f64, sigma: f64) -> f64 {
        let log_coefficient = -(sigma * (2.0 * PI).sqrt()).ln();
        let exponent = -(distance * distance) / (2.0 * sigma * sigma);
        log_coefficient + exponent
    }

    // 便捷方法：获取投影点
    pub fn point(&self) -> Point<f64> {
        self.projection.point
    }

    // 便捷方法：获取距离
    pub fn distance(&self) -> f64 {
        self.projection.distance
    }

    // 便捷方法：获取沿边距离
    pub fn distance_along_edge(&self) -> f64 {
        self.projection.distance_along_edge
    }

    // 便捷方法：获取边 ID
    pub fn edge_id(&self) -> &str {
        &self.projection.edge_id
    }

    // 便捷方法：获取原始轨迹点坐标
    pub fn track_point(&self) -> Point<f64> {
        self.track_point
    }

    // 计算两个候选点之间沿路网的距离
    // 考虑以下情况:
    // 1. 同一条边上: 直接计算 distance_along_edge 的差值
    // 2. 不同边上: 调用路网的最短路径计算
    pub fn compute_distance_to(&self, other: &CandidatePoint, road_network: &RoadNetwork) -> f64 {
        if self.edge_id() == other.edge_id() {
            // 同一条边上，直接计算距离差
            (other.distance_along_edge() - self.distance_along_edge()).abs()
        } else {
            // 不同边上，调用路网的最短路径计算
            let (path_distance, from_edge_length) =
                road_network.compute_edge_shortest_path(self.edge_id(), other.edge_id());

            if path_distance == f64::INFINITY {
                return f64::INFINITY;
            }

            // 总距离 = from 候选点到边终点的距离 + 路径距离 + to 边起点到候选点的距离
            let from_to_end = from_edge_length - self.distance_along_edge();
            from_to_end + path_distance + other.distance_along_edge()
        }
    }
}

// 单个轨迹点的候选点列表
pub type PointCandidates = Vec<CandidatePoint>;

// 整条轨迹的候选点列表（嵌套列表）
// 外层：每个轨迹点
// 内层：该轨迹点的所有候选点
pub type TrackCandidates = Vec<PointCandidates>;

// 为轨迹点生成候选点
// 输入：轨迹点、路网、搜索半径、GPS 误差标准差
// 返回：该轨迹点的候选点列表
pub fn generate_candidates_for_point(
    track_point: &TrackPoint,
    road_network: &RoadNetwork,
    radius: f64,
    gps_sigma: f64,
) -> PointCandidates {
    // 查找附近的候选边（radius 单位：米）
    let candidate_edges = road_network.find_candidate_edges(track_point.x(), track_point.y(), radius);

    // 将轨迹点投影到每条候选边上，生成候选点
    // 过滤掉距离超过搜索半径的候选点（使用地理距离）
    let origin_point = Point::new(track_point.x(), track_point.y());
    candidate_edges
        .iter()
        .map(|edge| {
            let projection = project_point_to_edge(track_point, edge);
            CandidatePoint::from_projection(projection, origin_point, gps_sigma)
        })
        .filter(|cand| cand.distance() <= radius)  // 过滤：只保留距离在搜索半径内的候选点
        .collect()
}

// 为整条轨迹生成候选点
// 输入：轨迹、路网、搜索半径、GPS 误差标准差
// 返回：轨迹的候选点列表（嵌套列表）
pub fn generate_candidates_for_track(
    track: &Track,
    road_network: &RoadNetwork,
    radius: f64,
    gps_sigma: f64,
) -> TrackCandidates {
    track
        .points
        .iter()
        .map(|point| generate_candidates_for_point(point, road_network, radius, gps_sigma))
        .collect()
}

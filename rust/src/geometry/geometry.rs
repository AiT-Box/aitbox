//! -*- coding: utf-8 -*-
//!
//! File        : geometry.rs
//! Project     : rust
//! Author      : gdd
//! Created     : 2026/1/18
//! Description : 几何计算相关函数

use geo_types::Point;

use crate::schemas::road_network::Edge;
use crate::schemas::track::TrackPoint;

// 地球半径（米）
const EARTH_RADIUS_M: f64 = 6371000.0;

// 使用 Haversine 公式计算两个 GPS 坐标点之间的地理距离（米）
// 参数: (lon1, lat1), (lon2, lat2) - 经纬度坐标
pub fn haversine_distance(lon1: f64, lat1: f64, lon2: f64, lat2: f64) -> f64 {
    let dlat = (lat2 - lat1).to_radians();
    let dlon = (lon2 - lon1).to_radians();
    
    let a = (dlat / 2.0).sin().powi(2)
        + lat1.to_radians().cos()
        * lat2.to_radians().cos()
        * (dlon / 2.0).sin().powi(2);
    
    let c = 2.0 * a.sqrt().asin();
    EARTH_RADIUS_M * c
}

// 计算两个点之间的地理距离（米）
// 假设 Point 的 x 是经度，y 是纬度
pub fn geographic_distance(p1: &Point<f64>, p2: &Point<f64>) -> f64 {
    haversine_distance(p1.x(), p1.y(), p2.x(), p2.y())
}

// 计算两个点之间的欧氏距离（适用于投影坐标系统）
pub fn euclidean_distance(p1: &Point<f64>, p2: &Point<f64>) -> f64 {
    let dx = p1.x() - p2.x();
    let dy = p1.y() - p2.y();
    (dx * dx + dy * dy).sqrt()
}

// 智能距离计算：根据坐标类型自动选择距离计算方法
// 如果坐标在 GPS 范围内（经度 -180 到 180，纬度 -90 到 90），使用地理距离
// 否则使用欧氏距离
pub fn smart_distance(p1: &Point<f64>, p2: &Point<f64>) -> f64 {
    // 判断是否为 GPS 坐标
    let is_gps = p1.x().abs() <= 180.0 && p1.y().abs() <= 90.0
        && p2.x().abs() <= 180.0 && p2.y().abs() <= 90.0
        && !(p1.x().abs() < 1000.0 && p1.y().abs() < 1000.0 && p2.x().abs() < 1000.0 && p2.y().abs() < 1000.0);
    
    if is_gps {
        geographic_distance(p1, p2)
    } else {
        euclidean_distance(p1, p2)
    }
}

// 投影结果结构体（也作为候选点使用）
#[derive(Debug, Clone)]
pub struct ProjectionPoint {
    // 投影点
    pub point: Point<f64>,
    // 投影点到原始轨迹点的距离
    pub distance: f64,
    // 投影点距离边起点的距离（沿边的累计距离）
    pub distance_along_edge: f64,
    // 投影到的边的 ID
    pub edge_id: String,
}

// 计算轨迹点到边的垂直投影点
// 返回投影点、到原始点的距离、沿边的累计距离、以及边的ID
// 如果投影落在边的延长线上，则返回起点或终点
pub fn project_point_to_edge(track_point: &TrackPoint, edge: &Edge) -> ProjectionPoint {
    let px = track_point.x();
    let py = track_point.y();
    let edge_id = edge.id.clone();

    let coords: Vec<_> = edge.geom.coords().collect();

    if coords.len() < 2 {
        // 边没有足够的坐标点，返回原点
        return ProjectionPoint {
            point: Point::new(px, py),
            distance: 0.0,
            distance_along_edge: 0.0,
            edge_id,
        };
    }

    // 计算边的总长度（使用智能距离）
    let mut total_length = 0.0;
    for i in 0..coords.len() - 1 {
        let p1 = Point::new(coords[i].x, coords[i].y);
        let p2 = Point::new(coords[i + 1].x, coords[i + 1].y);
        total_length += smart_distance(&p1, &p2);
    }

    // 检查是否投影到第一个线段的起点延长线上
    let first = &coords[0];
    let second = &coords[1];
    let track_point = Point::new(px, py);
    let first_point = Point::new(first.x, first.y);
    let t_first = compute_projection_t(px, py, first.x, first.y, second.x, second.y);
    if t_first < 0.0 {
        // 投影在起点延长线上，返回起点
        let dist = smart_distance(&track_point, &first_point);
        return ProjectionPoint {
            point: first_point,
            distance: dist,
            distance_along_edge: 0.0,
            edge_id,
        };
    }

    // 检查是否投影到最后一个线段的终点延长线上
    let last = &coords[coords.len() - 1];
    let second_last = &coords[coords.len() - 2];
    let track_point = Point::new(px, py);
    let last_point = Point::new(last.x, last.y);
    let t_last = compute_projection_t(px, py, second_last.x, second_last.y, last.x, last.y);
    if t_last > 1.0 {
        // 投影在终点延长线上，返回终点
        let dist = smart_distance(&track_point, &last_point);
        return ProjectionPoint {
            point: last_point,
            distance: dist,
            distance_along_edge: total_length,
            edge_id,
        };
    }

    // 正常情况：遍历边的每个线段，找到最近的投影点
    let mut min_distance = f64::INFINITY;
    let mut closest_point = Point::new(px, py);
    let mut distance_along_edge = 0.0;
    let mut accumulated_length = 0.0;

    let track_point = Point::new(px, py);
    for i in 0..coords.len() - 1 {
        let ax = coords[i].x;
        let ay = coords[i].y;
        let bx = coords[i + 1].x;
        let by = coords[i + 1].y;

        let segment_start = Point::new(ax, ay);
        let segment_end = Point::new(bx, by);
        let segment_length = smart_distance(&segment_start, &segment_end);
        
        let (proj_x, proj_y) = project_point_to_segment(px, py, ax, ay, bx, by);
        let proj_point = Point::new(proj_x, proj_y);
        let dist = smart_distance(&track_point, &proj_point);

        if dist < min_distance {
            min_distance = dist;
            closest_point = proj_point;
            let dist_to_segment_start = smart_distance(&segment_start, &proj_point);
            distance_along_edge = accumulated_length + dist_to_segment_start;
        }

        accumulated_length += segment_length;
    }

    ProjectionPoint {
        point: closest_point,
        distance: min_distance,
        distance_along_edge,
        edge_id,
    }
}

// 计算投影参数 t（不做 clamp）
fn compute_projection_t(px: f64, py: f64, ax: f64, ay: f64, bx: f64, by: f64) -> f64 {
    let abx = bx - ax;
    let aby = by - ay;
    let apx = px - ax;
    let apy = py - ay;
    let ab_squared = abx * abx + aby * aby;

    if ab_squared < 1e-10 {
        return 0.0;
    }

    (apx * abx + apy * aby) / ab_squared
}

// 计算点 (px, py) 到线段 (ax, ay) - (bx, by) 的垂直投影点
fn project_point_to_segment(px: f64, py: f64, ax: f64, ay: f64, bx: f64, by: f64) -> (f64, f64) {
    // 向量 AB
    let abx = bx - ax;
    let aby = by - ay;

    // 向量 AP
    let apx = px - ax;
    let apy = py - ay;

    // AB · AB
    let ab_squared = abx * abx + aby * aby;

    // 如果线段长度为0，返回线段起点
    if ab_squared < 1e-10 {
        return (ax, ay);
    }

    // t = (AP · AB) / (AB · AB)
    let t = (apx * abx + apy * aby) / ab_squared;

    // 限制 t 在 [0, 1] 范围内
    let t_clamped = t.clamp(0.0, 1.0);

    // 投影点 = A + t * AB
    let proj_x = ax + t_clamped * abx;
    let proj_y = ay + t_clamped * aby;

    (proj_x, proj_y)
}

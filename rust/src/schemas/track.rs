//! -*- coding: utf-8 -*-
//!
//! File        : track.rs
//! Project     : rust
//! Author      : gdd
//! Created     : 2026/1/18
//! Description : Track point structure

use geo_types::Point;

// 轨迹点结构体
// 表示一个轨迹采样点，包含原始位置信息和地图匹配结果
#[derive(Debug, Clone)]
pub struct TrackPoint {
    // 轨迹点的几何位置
    pub geom: Point<f64>,
    // 时间戳
    pub time: f64,
    // 映射到路段上的点坐标（地图匹配后）
    // 在地图匹配前为 None
    pub matched_point: Option<Point<f64>>,
    // 映射到的路段ID（地图匹配后）
    // 在地图匹配前为 None
    pub matched_edge_id: Option<String>,
}

impl TrackPoint {
    // 创建新的轨迹点（地图匹配前）
    pub fn new(geom: Point<f64>, time: f64) -> Self {
        Self {
            geom,
            time,
            matched_point: None,
            matched_edge_id: None,
        }
    }

    // 从坐标创建新的轨迹点（地图匹配前）
    pub fn from_coords(x: f64, y: f64, time: f64) -> Self {
        Self {
            geom: Point::new(x, y),
            time,
            matched_point: None,
            matched_edge_id: None,
        }
    }

    // 获取X坐标
    pub fn x(&self) -> f64 {
        self.geom.x()
    }

    // 获取Y坐标
    pub fn y(&self) -> f64 {
        self.geom.y()
    }
}

// 轨迹结构体
// 表示一条完整的轨迹，由一系列轨迹点组成
#[derive(Debug, Clone)]
pub struct Track {
    // 轨迹ID
    pub id: String,
    // 轨迹点序列
    pub points: Vec<TrackPoint>,
}

impl Track {
    // 创建新的轨迹
    pub fn new(id: String) -> Self {
        Self {
            id,
            points: Vec::new(),
        }
    }

    // 从轨迹点列表创建轨迹
    pub fn from_points(id: String, points: Vec<TrackPoint>) -> Self {
        Self { id, points }
    }

    // 添加轨迹点
    pub fn add_point(&mut self, point: TrackPoint) {
        self.points.push(point);
    }

    // 获取轨迹点数量
    pub fn len(&self) -> usize {
        self.points.len()
    }

    // 检查轨迹是否为空
    pub fn is_empty(&self) -> bool {
        self.points.is_empty()
    }

    // 获取轨迹点
    pub fn get_point(&self, index: usize) -> Option<&TrackPoint> {
        self.points.get(index)
    }

    // 获取轨迹点（可变引用）
    pub fn get_point_mut(&mut self, index: usize) -> Option<&mut TrackPoint> {
        self.points.get_mut(index)
    }
}

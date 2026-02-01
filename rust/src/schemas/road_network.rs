//! -*- coding: utf-8 -*-
//!
//! File        : road_network.rs
//! Project     : rust
//! Author      : gdd
//! Created     : 2026/1/18
//! Description :

use std::collections::HashMap;
use std::sync::atomic::{AtomicU64, Ordering};

use geo_types::LineString;
use moka::sync::Cache;
use petgraph::algo::dijkstra;
use petgraph::graph::NodeIndex;
use petgraph::{Directed, Graph};
use rstar::{AABB, RTree, RTreeObject};

// 路网节点，代表路口或交叉口
#[derive(Debug, Clone)]
pub struct Node {
    // 节点ID
    pub id: String,
    // 节点名称
    pub name: String,
    // X坐标
    pub x: f64,
    // Y坐标
    pub y: f64,
}

// 路网边，代表路段
#[derive(Debug, Clone)]
pub struct Edge {
    // 边ID
    pub id: String,
    // 边名称
    pub name: String,
    // 路段长度
    pub length: f64,
    // 起点节点ID
    pub start_node_id: String,
    // 终点节点ID
    pub end_node_id: String,
    // 路段几何形状
    pub geom: LineString,
}

impl RTreeObject for Edge {
    type Envelope = AABB<[f64; 2]>;

    fn envelope(&self) -> Self::Envelope {
        // 计算 LineString 的边界框
        let mut min_x = f64::INFINITY;
        let mut min_y = f64::INFINITY;
        let mut max_x = f64::NEG_INFINITY;
        let mut max_y = f64::NEG_INFINITY;

        for coord in self.geom.coords() {
            min_x = min_x.min(coord.x);
            min_y = min_y.min(coord.y);
            max_x = max_x.max(coord.x);
            max_y = max_y.max(coord.y);
        }

        // 如果没有坐标点，返回默认边界框
        if min_x == f64::INFINITY {
            return AABB::from_point([0.0, 0.0]);
        }

        // 避免退化的 AABB（高度或宽度为 0）
        // 对于水平线或垂直线，添加一个小的 epsilon
        let epsilon = 1e-6;
        if (max_x - min_x).abs() < epsilon {
            min_x -= epsilon;
            max_x += epsilon;
        }
        if (max_y - min_y).abs() < epsilon {
            min_y -= epsilon;
            max_y += epsilon;
        }

        AABB::from_corners([min_x, min_y], [max_x, max_y])
    }
}

// 最短路径缓存值
#[derive(Debug, Clone, Copy)]
struct PathCacheValue {
    path_distance: f64,
    from_edge_length: f64,
}

// 缓存统计
#[derive(Debug, Default)]
pub struct CacheStats {
    pub hits: AtomicU64,
    pub misses: AtomicU64,
}

impl CacheStats {
    pub fn hit_rate(&self) -> f64 {
        let hits = self.hits.load(Ordering::Relaxed);
        let misses = self.misses.load(Ordering::Relaxed);
        let total = hits + misses;
        if total == 0 {
            0.0
        } else {
            hits as f64 / total as f64
        }
    }

    pub fn reset(&self) {
        self.hits.store(0, Ordering::Relaxed);
        self.misses.store(0, Ordering::Relaxed);
    }
}

// 路网结构体
pub struct RoadNetwork {
    pub graph: Graph<Node, Edge, Directed>,
    pub spatial_index: RTree<Edge>,
    // 节点ID到节点索引的映射（用于快速查找）
    node_index_map: HashMap<String, NodeIndex>,
    // 边ID到边的映射（用于快速查找）
    edge_map: HashMap<String, Edge>,
    // 最短路径缓存（使用 TinyLFU 策略）
    // Key: "from_edge_id:to_edge_id"
    // Value: (path_distance, from_edge_length)
    path_cache: Cache<String, PathCacheValue>,
    // 缓存统计
    pub cache_stats: CacheStats,
}

// 默认缓存大小
const DEFAULT_CACHE_SIZE: u64 = 10000;

impl RoadNetwork {
    // 创建空的路网
    pub fn new() -> Self {
        Self::with_cache_size(DEFAULT_CACHE_SIZE)
    }

    // 创建空的路网（自定义缓存大小）
    pub fn with_cache_size(cache_size: u64) -> Self {
        Self {
            graph: Graph::new(),
            spatial_index: RTree::new(),
            node_index_map: HashMap::new(),
            edge_map: HashMap::new(),
            path_cache: Cache::new(cache_size),
            cache_stats: CacheStats::default(),
        }
    }

    // 从节点和边列表创建路网
    pub fn from_nodes_and_edges(nodes: Vec<Node>, edges: Vec<Edge>) -> Self {
        Self::from_nodes_and_edges_with_cache(nodes, edges, DEFAULT_CACHE_SIZE)
    }

    // 从节点和边列表创建路网（自定义缓存大小）
    pub fn from_nodes_and_edges_with_cache(
        nodes: Vec<Node>,
        edges: Vec<Edge>,
        cache_size: u64,
    ) -> Self {
        let mut graph = Graph::new();
        let mut node_index_map = HashMap::new();
        let mut edge_map = HashMap::new();

        // 添加所有节点到图中，并记录节点ID到索引的映射
        for node in &nodes {
            let idx = graph.add_node(node.clone());
            node_index_map.insert(node.id.clone(), idx);
        }

        // 添加所有边到图中，并构建边映射
        for edge in &edges {
            if let (Some(&start_idx), Some(&end_idx)) = (
                node_index_map.get(&edge.start_node_id),
                node_index_map.get(&edge.end_node_id),
            ) {
                graph.add_edge(start_idx, end_idx, edge.clone());
                edge_map.insert(edge.id.clone(), edge.clone());
            }
        }

        // 构建空间索引
        let spatial_index = RTree::bulk_load(edges.clone());

        Self {
            graph,
            spatial_index,
            node_index_map,
            edge_map,
            path_cache: Cache::new(cache_size),
            cache_stats: CacheStats::default(),
        }
    }

    // 根据轨迹点位置查找候选边
    // 输入：轨迹点坐标 (x=经度, y=纬度) 和搜索半径 radius（米）
    // 返回：半径范围内的候选边列表
    pub fn find_candidate_edges(&self, x: f64, y: f64, radius: f64) -> Vec<&Edge> {
        // 判断是否为 GPS 坐标
        // 更严格的判断：GPS 坐标通常在 -180 到 180（经度）和 -90 到 90（纬度）范围内
        // 但还需要检查坐标的"合理性"：如果坐标值很小（< 1000），且半径相对于坐标值很大，可能是投影坐标
        // 简单判断：如果坐标绝对值都小于 1000，且半径大于坐标值的 10%，则认为是投影坐标
        let is_gps = x.abs() <= 180.0 && y.abs() <= 90.0 
            && !(x.abs() < 1000.0 && y.abs() < 1000.0 && radius > x.abs().max(y.abs()) * 0.1);
        
        let (radius_x, radius_y) = if is_gps {
            // GPS 坐标：将米转换为度数
            // 1度经度 ≈ 111320 * cos(纬度) 米
            // 1度纬度 ≈ 111320 米
            let lat_rad = y.to_radians();
            let meters_per_degree_lon = 111320.0 * lat_rad.cos();
            let meters_per_degree_lat = 111320.0;
            
            let radius_lon = radius / meters_per_degree_lon;
            let radius_lat = radius / meters_per_degree_lat;
            (radius_lon, radius_lat)
        } else {
            // 非 GPS 坐标（如投影坐标系统），直接使用 radius
            (radius, radius)
        };
        
        let search_envelope = AABB::from_corners(
            [x - radius_x, y - radius_y],
            [x + radius_x, y + radius_y],
        );
        
        // 使用 locate_in_envelope_intersecting 查找与搜索区域相交的边
        // 注意：locate_in_envelope_intersecting 返回与搜索区域相交的所有对象
        let mut candidates = Vec::new();
        for edge in self.spatial_index.locate_in_envelope_intersecting(&search_envelope) {
            candidates.push(edge);
        }
        candidates
    }

    // 根据边ID获取边
    pub fn get_edge(&self, edge_id: &str) -> Option<&Edge> {
        self.edge_map.get(edge_id)
    }

    // 生成缓存键
    fn make_cache_key(from_edge_id: &str, to_edge_id: &str) -> String {
        format!("{}:{}", from_edge_id, to_edge_id)
    }

    // 计算两条边之间的最短路径距离（从 from_edge 终点到 to_edge 起点）
    // 使用 LFU 缓存加速重复查询
    // 输入:
    //   - from_edge_id: 起始边的 ID
    //   - to_edge_id: 目标边的 ID
    // 返回: (最短路径距离, from_edge 长度)，如果不可达返回 (f64::INFINITY, 0.0)
    pub fn compute_edge_shortest_path(
        &self,
        from_edge_id: &str,
        to_edge_id: &str,
    ) -> (f64, f64) {
        // 同一条边，路径距离为 0
        if from_edge_id == to_edge_id {
            return (0.0, 0.0);
        }

        // 生成缓存键
        let cache_key = Self::make_cache_key(from_edge_id, to_edge_id);

        // 尝试从缓存获取
        if let Some(cached) = self.path_cache.get(&cache_key) {
            self.cache_stats.hits.fetch_add(1, Ordering::Relaxed);
            return (cached.path_distance, cached.from_edge_length);
        }

        self.cache_stats.misses.fetch_add(1, Ordering::Relaxed);

        // 缓存未命中，计算最短路径
        let result = self.compute_shortest_path_internal(from_edge_id, to_edge_id);

        // 存入缓存
        self.path_cache.insert(
            cache_key,
            PathCacheValue {
                path_distance: result.0,
                from_edge_length: result.1,
            },
        );

        result
    }

    // 内部最短路径计算（不使用缓存）
    fn compute_shortest_path_internal(
        &self,
        from_edge_id: &str,
        to_edge_id: &str,
    ) -> (f64, f64) {
        // 从缓存中查找边（O(1) 复杂度）
        let from_edge = self.edge_map.get(from_edge_id);
        let to_edge = self.edge_map.get(to_edge_id);

        match (from_edge, to_edge) {
            (Some(from), Some(to)) => {
                // 获取节点索引
                let from_end_idx = self.node_index_map.get(&from.end_node_id);
                let to_start_idx = self.node_index_map.get(&to.start_node_id);

                match (from_end_idx, to_start_idx) {
                    (Some(&from_idx), Some(&to_idx)) => {
                        // 使用 Dijkstra 算法计算最短路径
                        let costs = dijkstra(
                            &self.graph,
                            from_idx,
                            Some(to_idx),
                            |e| e.weight().length,
                        );

                        match costs.get(&to_idx) {
                            Some(&path_cost) => (path_cost, from.length),
                            None => (f64::INFINITY, from.length),
                        }
                    }
                    _ => (f64::INFINITY, 0.0),
                }
            }
            _ => (f64::INFINITY, 0.0),
        }
    }

    // 获取缓存大小
    pub fn cache_size(&self) -> u64 {
        self.path_cache.entry_count()
    }

    // 获取缓存容量
    pub fn cache_capacity(&self) -> u64 {
        self.path_cache.weighted_size()
    }

    // 清空缓存
    pub fn clear_cache(&self) {
        self.path_cache.invalidate_all();
        self.cache_stats.reset();
    }

    // 获取缓存命中率
    pub fn cache_hit_rate(&self) -> f64 {
        self.cache_stats.hit_rate()
    }
}

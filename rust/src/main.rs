//! -*- coding: utf-8 -*-
//!
//! File        : main.rs
//! Project     : rust
//! Author      : gdd
//! Created     : 2026/1/18
//! Description : 地图匹配测试示例

#![allow(dead_code)]

mod geometry;
mod matching;
mod schemas;

use std::time::Instant;

use geo_types::{coord, LineString};
use matching::candidate::generate_candidates_for_track;
use matching::matching::{map_match, map_match_batch};
use matching::viterbi::MatchParams;
use rstar::{RTreeObject};
use schemas::road_network::{Edge, Node, RoadNetwork};
use schemas::track::{Track, TrackPoint};

// 创建示例路网
fn create_sample_road_network() -> RoadNetwork {
    // 创建示例节点（路口）- 一个正方形路网
    let nodes = vec![
        Node {
            id: "n1".to_string(),
            name: "路口1".to_string(),
            x: 0.0,
            y: 0.0,
        },
        Node {
            id: "n2".to_string(),
            name: "路口2".to_string(),
            x: 100.0,
            y: 0.0,
        },
        Node {
            id: "n3".to_string(),
            name: "路口3".to_string(),
            x: 100.0,
            y: 100.0,
        },
        Node {
            id: "n4".to_string(),
            name: "路口4".to_string(),
            x: 0.0,
            y: 100.0,
        },
    ];

    // 创建示例边（路段）- 正方形的四条边
    let edges = vec![
        Edge {
            id: "e1".to_string(),
            name: "路段1".to_string(),
            length: 100.0,
            start_node_id: "n1".to_string(),
            end_node_id: "n2".to_string(),
            geom: LineString::new(vec![
                coord! { x: 0.0, y: 0.0 },
                coord! { x: 50.0, y: 0.0 },
                coord! { x: 100.0, y: 0.0 },
            ]),
        },
        Edge {
            id: "e2".to_string(),
            name: "路段2".to_string(),
            length: 100.0,
            start_node_id: "n2".to_string(),
            end_node_id: "n3".to_string(),
            geom: LineString::new(vec![
                coord! { x: 100.0, y: 0.0 },
                coord! { x: 100.0, y: 50.0 },
                coord! { x: 100.0, y: 100.0 },
            ]),
        },
        Edge {
            id: "e3".to_string(),
            name: "路段3".to_string(),
            length: 100.0,
            start_node_id: "n3".to_string(),
            end_node_id: "n4".to_string(),
            geom: LineString::new(vec![
                coord! { x: 100.0, y: 100.0 },
                coord! { x: 50.0, y: 100.0 },
                coord! { x: 0.0, y: 100.0 },
            ]),
        },
        Edge {
            id: "e4".to_string(),
            name: "路段4".to_string(),
            length: 100.0,
            start_node_id: "n4".to_string(),
            end_node_id: "n1".to_string(),
            geom: LineString::new(vec![
                coord! { x: 0.0, y: 100.0 },
                coord! { x: 0.0, y: 50.0 },
                coord! { x: 0.0, y: 0.0 },
            ]),
        },
    ];

    RoadNetwork::from_nodes_and_edges(nodes, edges)
}

// 创建示例轨迹（沿着路段 e1 -> e2 行驶，带有 GPS 噪声）
fn create_sample_track(id: &str) -> Track {
    let points = vec![
        // 沿着 e1 (y=0) 行驶，带有一些 y 方向的噪声
        TrackPoint::from_coords(5.0, 2.0, 0.0),
        TrackPoint::from_coords(25.0, -1.0, 1.0),
        TrackPoint::from_coords(50.0, 3.0, 2.0),
        TrackPoint::from_coords(75.0, -2.0, 3.0),
        TrackPoint::from_coords(95.0, 1.0, 4.0),
        // 转向 e2 (x=100) 行驶
        TrackPoint::from_coords(102.0, 20.0, 5.0),
        TrackPoint::from_coords(98.0, 45.0, 6.0),
        TrackPoint::from_coords(101.0, 70.0, 7.0),
        TrackPoint::from_coords(99.0, 95.0, 8.0),
    ];

    Track::from_points(id.to_string(), points)
}

// 测试单轨迹地图匹配
fn test_single_track_match(road_network: &RoadNetwork) {
    println!("\n========== 单轨迹地图匹配测试 ==========");

    let track = create_sample_track("track_001");
    println!("轨迹 ID: {}", track.id);
    println!("轨迹点数量: {}", track.len());

    // 打印原始轨迹点
    println!("\n原始轨迹点:");
    for (i, point) in track.points.iter().enumerate() {
        println!("  点 {}: ({:.1}, {:.1}) @ t={:.1}", i, point.x(), point.y(), point.time);
    }

    // 调试：直接检查 R-tree 查询
    println!("\n调试 - R-tree 查询:");
    let test_point = &track.points[0];
    let radius = 50.0;
    
    // 计算搜索的 AABB（模拟 find_candidate_edges 的逻辑）
    let (radius_x, radius_y) = if test_point.x().abs() <= 180.0 && test_point.y().abs() <= 90.0 {
        let lat_rad = test_point.y().to_radians();
        let meters_per_degree_lon = 111320.0 * lat_rad.cos();
        let meters_per_degree_lat = 111320.0;
        (radius / meters_per_degree_lon, radius / meters_per_degree_lat)
    } else {
        (radius, radius)
    };
    
    println!("  搜索点: ({:.1}, {:.1}), 半径: {} 米", test_point.x(), test_point.y(), radius);
    println!("  搜索 AABB: [{:.6}, {:.6}] - [{:.6}, {:.6}]", 
        test_point.x() - radius_x, test_point.y() - radius_y,
        test_point.x() + radius_x, test_point.y() + radius_y);
    
    let edges = road_network.find_candidate_edges(test_point.x(), test_point.y(), radius);
    println!("  find_candidate_edges 返回: {} 条边", edges.len());
    for edge in &edges {
        println!("    - 边 {}", edge.id);
    }
    
    // 打印每条边的 AABB
    println!("  边的 AABB:");
    for edge in road_network.spatial_index.iter() {
        let env = edge.envelope();
        let lower = env.lower();
        let upper = env.upper();
        println!("    边 {}: [{:.6}, {:.6}] - [{:.6}, {:.6}]", 
            edge.id, lower[0], lower[1], upper[0], upper[1]);
    }

    // 执行地图匹配
    let params = MatchParams {
        gps_sigma: 10.0,       // GPS 误差 10 米
        beta: 5.0,             // 转移概率参数
        search_radius: 50.0,   // 搜索半径 50 米
    };

    // 调试：检查候选点生成
    println!("\n调试 - 候选点生成:");
    let candidates = generate_candidates_for_track(&track, road_network, params.search_radius, params.gps_sigma);
    for (i, point_candidates) in candidates.iter().enumerate() {
        println!("  点 {}: {} 个候选边", i, point_candidates.len());
        for cand in point_candidates {
            println!("    - 边 {}: 距离 {:.2}m", cand.edge_id(), cand.distance());
        }
    }

    let start = Instant::now();
    let result = map_match(&track, road_network, &params);
    let elapsed = start.elapsed();

    match result {
        Some(match_result) => {
            println!("\n匹配成功！耗时: {:?}", elapsed);
            println!("对数概率: {:.4}", match_result.log_probability);
            println!("匹配点数量: {}", match_result.matched_points.len());

            println!("\n匹配结果:");
            for (i, matched) in match_result.matched_points.iter().enumerate() {
                let proj = matched.point();
                println!(
                    "  点 {} -> 边 {}: 投影点 ({:.1}, {:.1}), 距离 {:.2}m, 沿边距离 {:.2}m",
                    i,
                    matched.edge_id(),
                    proj.x(),
                    proj.y(),
                    matched.distance(),
                    matched.distance_along_edge()
                );
            }
        }
        None => {
            println!("\n匹配失败！");
        }
    }

    // 缓存统计
    println!("\n缓存统计:");
    println!("  缓存大小: {}", road_network.cache_size());
    println!("  缓存命中率: {:.2}%", road_network.cache_hit_rate() * 100.0);
}

// 测试批量轨迹并行匹配
fn test_batch_match(road_network: &RoadNetwork) {
    println!("\n========== 批量轨迹并行匹配测试 ==========");

    // 清空缓存以测试新的统计
    road_network.clear_cache();

    // 创建多条轨迹
    let tracks: Vec<Track> = (0..100)
        .map(|i| create_sample_track(&format!("track_{:03}", i)))
        .collect();

    println!("轨迹数量: {}", tracks.len());

    let params = MatchParams {
        gps_sigma: 10.0,
        beta: 5.0,
        search_radius: 50.0,
    };

    // 批量并行匹配
    let start = Instant::now();
    let results = map_match_batch(&tracks, road_network, &params);
    let elapsed = start.elapsed();

    // 统计结果
    let success_count = results.iter().filter(|r| r.result.is_some()).count();
    let fail_count = results.len() - success_count;

    println!("\n批量匹配完成！");
    println!("总耗时: {:?}", elapsed);
    println!("平均每条轨迹耗时: {:?}", elapsed / tracks.len() as u32);
    println!("成功: {}, 失败: {}", success_count, fail_count);

    // 缓存统计
    println!("\n缓存统计:");
    println!("  缓存大小: {}", road_network.cache_size());
    println!("  缓存命中率: {:.2}%", road_network.cache_hit_rate() * 100.0);
}

fn main() {
    println!("========== 地图匹配测试 ==========\n");

    // 创建路网
    println!("创建路网...");
    let road_network = create_sample_road_network();
    println!("路网创建成功！");
    println!("  节点数量: {}", road_network.graph.node_count());
    println!("  边数量: {}", road_network.graph.edge_count());

    // 调试：检查空间索引中的边
    println!("\n调试 - 空间索引中的边:");
    for edge in road_network.spatial_index.iter() {
        let env = edge.envelope();
        println!("  边 {}: AABB = {:?}", edge.id, env);
    }

    // 测试单轨迹匹配
    test_single_track_match(&road_network);

    // 测试批量并行匹配
    test_batch_match(&road_network);

    println!("\n========== 测试完成 ==========");
}

//! -*- coding: utf-8 -*-
//!
//! File        : viterbi.rs
//! Project     : rust
//! Author      : gdd
//! Created     : 2026/1/25
//! Description : HMM Viterbi 算法实现

use crate::matching::candidate::TrackCandidates;
use crate::matching::transition::compute_transition_matrix;
use crate::schemas::road_network::RoadNetwork;

// Viterbi 算法状态
#[derive(Debug, Clone)]
pub struct ViterbiState {
    // 每个时间步的最优概率（对数形式）
    // viterbi_prob[t][i] = 到达时间 t 状态 i 的最大对数概率
    pub viterbi_prob: Vec<Vec<f64>>,
    // 回溯指针
    // backpointer[t][i] = 从时间 t-1 到达时间 t 状态 i 的最优前驱状态索引
    pub backpointer: Vec<Vec<usize>>,
}

// 地图匹配参数
#[derive(Debug, Clone)]
pub struct MatchParams {
    // GPS 误差标准差（用于观测概率）
    pub gps_sigma: f64,
    // 转移概率参数 beta
    pub beta: f64,
    // 候选边搜索半径
    pub search_radius: f64,
}

impl Default for MatchParams {
    fn default() -> Self {
        Self {
            gps_sigma: 50.0,      // 默认 50 米
            beta: 5.0,            // 默认 beta
            search_radius: 100.0, // 默认搜索半径 100 米
        }
    }
}

// Viterbi 算法前向计算
// 输入:
//   - candidates: 候选点列表
//   - road_network: 路网
//   - beta: 转移概率参数
// 返回: Viterbi 状态（包含概率矩阵和回溯指针）
pub fn viterbi_forward(
    candidates: &TrackCandidates,
    road_network: &RoadNetwork,
    beta: f64,
) -> Option<ViterbiState> {
    if candidates.is_empty() {
        return None;
    }

    let n_steps = candidates.len();
    let mut viterbi_prob: Vec<Vec<f64>> = Vec::with_capacity(n_steps);
    let mut backpointer: Vec<Vec<usize>> = Vec::with_capacity(n_steps);

    // 初始化第一个时间步（只有观测概率，没有转移概率）
    let first_candidates = &candidates[0];
    if first_candidates.is_empty() {
        return None;
    }

    let first_probs: Vec<f64> = first_candidates
        .iter()
        .map(|c| c.observation_prob)
        .collect();
    viterbi_prob.push(first_probs);
    backpointer.push(vec![0; first_candidates.len()]); // 第一步没有前驱

    // 前向计算
    for t in 1..n_steps {
        let prev_candidates = &candidates[t - 1];
        let curr_candidates = &candidates[t];

        if curr_candidates.is_empty() {
            // 当前时间步没有候选点，跳过
            viterbi_prob.push(vec![]);
            backpointer.push(vec![]);
            continue;
        }

        if prev_candidates.is_empty() {
            // 前一个时间步没有候选点，重新初始化
            let probs: Vec<f64> = curr_candidates
                .iter()
                .map(|c| c.observation_prob)
                .collect();
            viterbi_prob.push(probs);
            backpointer.push(vec![0; curr_candidates.len()]);
            continue;
        }

        // 从候选点获取原始轨迹点坐标
        let prev_track_point = prev_candidates[0].track_point();
        let curr_track_point = curr_candidates[0].track_point();

        // 计算转移概率矩阵
        let trans_matrix = compute_transition_matrix(
            prev_candidates,
            curr_candidates,
            (prev_track_point.x(), prev_track_point.y()),
            (curr_track_point.x(), curr_track_point.y()),
            road_network,
            beta,
        );

        let prev_probs = &viterbi_prob[t - 1];
        let mut curr_probs = Vec::with_capacity(curr_candidates.len());
        let mut curr_backpointer = Vec::with_capacity(curr_candidates.len());

        // 对每个当前候选点，找到最优的前驱状态
        for (j, curr_cand) in curr_candidates.iter().enumerate() {
            let mut max_prob = f64::NEG_INFINITY;
            let mut best_prev = 0;

            for (i, prev_prob) in prev_probs.iter().enumerate() {
                // 对数概率相加 = 概率相乘
                let prob = prev_prob + trans_matrix[i][j];
                if prob > max_prob {
                    max_prob = prob;
                    best_prev = i;
                }
            }

            // 加上当前状态的观测概率
            curr_probs.push(max_prob + curr_cand.observation_prob);
            curr_backpointer.push(best_prev);
        }

        viterbi_prob.push(curr_probs);
        backpointer.push(curr_backpointer);
    }

    Some(ViterbiState {
        viterbi_prob,
        backpointer,
    })
}

// Viterbi 算法后向回溯
// 输入: Viterbi 状态
// 返回: 最优路径（每个时间步的候选点索引）
pub fn viterbi_backward(state: &ViterbiState) -> Vec<usize> {
    let n_steps = state.viterbi_prob.len();
    if n_steps == 0 {
        return vec![];
    }

    let mut path = vec![0; n_steps];

    // 找到最后一个时间步的最优状态
    let last_probs = &state.viterbi_prob[n_steps - 1];
    if last_probs.is_empty() {
        return vec![];
    }

    let mut best_last = 0;
    let mut max_prob = f64::NEG_INFINITY;
    for (i, &prob) in last_probs.iter().enumerate() {
        if prob > max_prob {
            max_prob = prob;
            best_last = i;
        }
    }
    path[n_steps - 1] = best_last;

    // 后向回溯
    for t in (1..n_steps).rev() {
        let curr_state = path[t];
        if state.backpointer[t].is_empty() {
            // 如果当前时间步没有回溯指针，尝试找到前一个有效状态
            path[t - 1] = 0;
        } else {
            path[t - 1] = state.backpointer[t][curr_state];
        }
    }

    path
}

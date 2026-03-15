import os
import json
import numpy as np
import polars as pl
from src.aitbox.utils.track.track_utils import cal_haversine_dis, cal_haversine_dis_vector_numpy


class Denoising:
    def __init__(self, data: pl.DataFrame, save_path: str = "", denoising_level: str = "low"):
        self.data = data
        self.save_path = save_path
        self.pl_data = data.clone()  # polars使用clone()而不是copy(deep=True)
        self.denoising_level = denoising_level

        self.denoising_limit_info = {
            "low": {"distance_limit": 10000, "time_limit": 3},
            "mid": {"distance_limit": 8000, "time_limit": 2},
            "high": {"distance_limit": 5000, "time_limit": 1},
        }

        self.result_data = {
            "noise_num": 0,
            "noise_points": None,
            "points": self.data.to_dicts()  # polars使用to_dicts()
        }

        # 获取坐标数组
        self.coordinates = self.data.select(["lon", "lat"]).to_numpy()

    def __denoising_core(self):
        # 轨迹降噪
        distance_limit = self.denoising_limit_info[self.denoising_level]["distance_limit"]
        time_limit = self.denoising_limit_info[self.denoising_level]["time_limit"]

        # 向量化计算距离 - 使用numpy版本提高性能
        distance_list = cal_haversine_dis_vector_numpy(self.pl_data)

        # 根据距离阈值确定噪点（初筛）
        detected_noise_segments = np.where(distance_list >= distance_limit)[0]
        segment_dis_list = distance_list[detected_noise_segments]

        # 调整为轨迹点对
        detected_noise_segments = np.column_stack((detected_noise_segments, detected_noise_segments + 1))

        # 根据相邻的noise_segment，判断要剔除的噪点
        noise_list = []
        for i in range(len(detected_noise_segments) - 1):
            left_index = detected_noise_segments[i][0]
            right_index = detected_noise_segments[i + 1][1]
            cur_point = self.coordinates[left_index]
            next_point = self.coordinates[right_index]
            dis = cal_haversine_dis(tuple(cur_point), tuple(next_point))

            if (segment_dis_list[i] >= time_limit * dis and
                    segment_dis_list[i + 1] >= time_limit * dis):
                noise_list.extend(list(range(left_index + 1, right_index)))

        if len(noise_list) == 0:
            print("未识别到噪点")
            return
        else:
            print(f"识别到{len(noise_list)}个噪点，信息如下：")
            self.result_data["noise_num"] = len(noise_list)

            # 获取噪点数据
            noise_indices = np.array(noise_list)
            if len(noise_indices) > 0:
                noise_df = self.pl_data[noise_indices]
                self.result_data["noise_points"] = noise_df.to_dicts()

            for i in sorted(noise_list):
                print(i, "\t", self.coordinates[i], "\t")

            # 确定降噪后的轨迹点、坐标
            remained_points = sorted(set(range(len(self.coordinates))) - set(noise_list))
            self.coordinates = self.coordinates[remained_points]

            # 使用filter筛选剩余点
            self.pl_data = self.pl_data.filter(
                pl.arange(0, pl.len()).is_in(remained_points)
            )

            # 重置索引 - polars不需要显式重置，但我们可以添加新列
            # self.pl_data = self.pl_data.with_row_count("row_index")
            self.pl_data = self.pl_data.with_row_index("row_index")
            self.result_data["points"] = self.pl_data.to_dicts()

        # if self.save_path:
        #     os.makedirs(self.save_path, exist_ok=True)
        #     with open(os.path.join(self.save_path, 'denoising_points.json'), 'w', encoding='utf-8') as f:
        #         json.dump(self.result_data, f, ensure_ascii=False, indent=4)

    def process(self):
        self.__denoising_core()
        return self.result_data


# 主函数，展示如何使用
if __name__ == '__main__':
    path = '../../../../../tests/data/track/'
    # save_path = r'data/result_data'

    # 【孤立噪点】
    file = 'track_isolated_noise.csv'
    data_df = pl.read_csv(os.path.join(path, file))

    # file = 'track_isolated_noise.json'
    # 读取异常段轨迹信息
    # with open(os.path.join(path, file), 'r', encoding='utf-8') as f:
    #     data = json.load(f)

    # data_df = pl.DataFrame(data['points'])

    # 实例化并处理
    denoising = Denoising(data_df)
    result = denoising.process()
    print("finished")

    # 可选：将结果保存为新的polars DataFrame
    if result and "points" in result:
        cleaned_df = pl.DataFrame(result["points"])
        print(f"清理后数据行数: {cleaned_df.height}")
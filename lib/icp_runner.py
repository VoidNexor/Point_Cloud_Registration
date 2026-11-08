"""Shared command-line implementation for the point-to-plane ICP workflows."""

import os
import random

import numpy as np

from .kdtree import KdTree
from .utils import load_pts, load_xf, write_pts, write_txt, write_xf


def _identity_transform():
    # The legacy implementation uses ``.I`` and matrix multiplication.
    return np.matrix(np.identity(4))


def _load_transform(path, missing_message, default_message):
    if os.path.isfile(path):
        return load_xf(path)
    print(missing_message.format(path))
    print(default_message)
    return _identity_transform()


def run_icp(
    file1,
    file2,
    output_path,
    sample_size,
    outlier_scale,
    max_iterations=50,
    seed=None,
    write_text_output=False,
    log_path=None,
    language="en",
):
    """Align ``file1`` to ``file2`` and write the resulting transforms."""
    if not os.path.isfile(file1):
        raise FileNotFoundError("Could not find .pts file: " + file1)
    if not os.path.isfile(file2):
        raise FileNotFoundError("Could not find .pts file: " + file2)

    pts1 = load_pts(file1)
    pts2 = load_pts(file2)
    if not pts1 or not pts2:
        raise ValueError("Both point-cloud files must contain at least one point")

    file1_xf = os.path.splitext(file1)[0] + ".xf"
    file2_xf = os.path.splitext(file2)[0] + ".xf"
    if language == "zh":
        missing = "警告：找不到.xf文件：{}"
        default = "默认使用4x4单位矩阵..."
        target_message = "使用变换 {} 作为目标"
        build_message = "正在从 {} 构建KdTree..."
        start_message = "开始迭代..."
        singular_message = "错误：点云几何信息不足，无法计算ICP变换"
        distance_error = "错误：在计算距离平均值时出了问题"
        iteration_message = "完成了迭代 #{}，改进了 {:2.4%}"
        success_message = "成功终止，采样的平均距离为 {}"
    else:
        missing = "Warning: Could not find .xf file: {}"
        default = "Defaulting to 4x4 identity matrix..."
        target_message = "Using the transformation {} as target"
        build_message = "Building KdTree from {}..."
        start_message = "Starting iteration..."
        singular_message = "Error: the point set does not provide enough geometry for ICP"
        distance_error = "Error: something went wrong when computing distance means"
        iteration_message = "Finished iteration #{} with improvement of {:2.4%}"
        success_message = "Terminated successfully with a sampled mean distance of {}"

    M1 = _load_transform(file1_xf, missing, default)
    output_file2_xf = os.path.join(output_path, os.path.basename(file2_xf))
    if os.path.isfile(output_file2_xf):
        print(target_message.format(output_file2_xf))
        M2 = load_xf(output_file2_xf)
    else:
        M2 = _load_transform(file2_xf, missing, default)

    print(build_message.format(file2))
    kdtree = KdTree()
    for point in pts2:
        kdtree.insert(point)

    print(start_message)
    ratio = 0.0
    M2_inverse = M2.I
    point_indices = list(range(len(pts1)))
    rng = random.Random(seed)
    count = 0
    new_mean = float("inf")

    while (1.0 - ratio > 0.0001 and count < max_iterations):
        rng.shuffle(point_indices)
        sampled = [
            pts1[index].copy().transform(M1).transform(M2_inverse)
            for index in point_indices[:sample_size]
        ]
        nearest = [kdtree.nearest(point) for point in sampled]

        point2plane = [
            abs(np.subtract(point.s, target.s).dot(target.n))
            for point, target in zip(sampled, nearest)
        ]
        cutoff = outlier_scale * np.median(point2plane)
        point_pairs = [
            pair for distance, pair in zip(point2plane, zip(sampled, nearest))
            if distance <= cutoff
        ]
        if not point_pairs:
            raise ValueError(distance_error)

        old_mean = sum(
            abs(np.subtract(point.s, target.s).dot(target.n))
            for point, target in point_pairs
        ) / len(point_pairs)

        C = np.zeros(shape=(6, 6))
        d = np.zeros(shape=(6, 1))
        for point, target in point_pairs:
            A = np.matrix(np.append(np.cross(point.s, target.n), target.n))
            AT = A.T
            b = np.subtract(target.s, point.s).dot(target.n)
            C += AT * A
            d += AT * b

        try:
            x = np.linalg.solve(C, d).flatten()
        except np.linalg.LinAlgError as error:
            raise ValueError(singular_message) from error

        rx, ry, rz, tx, ty, tz = x
        Micp = np.matrix(
            [
                [1.0, ry * rx - rz, rz * rx + ry, tx],
                [rz, 1.0 + rz * ry * rx, rz * ry - rx, ty],
                [-ry, rx, 1.0, tz],
                [0, 0, 0, 1.0],
            ]
        )

        dist_sum = 0.0
        for point, target in point_pairs:
            transformed = point.transform(Micp)
            dist_sum += abs(np.subtract(transformed.s, target.s).dot(target.n))
        new_mean = dist_sum / len(point_pairs)
        count += 1
        ratio = new_mean / old_mean if old_mean else 1.0

        if ratio < 1.0:
            M1 = M2 * Micp * M2_inverse * M1
        else:
            new_mean = old_mean

        print(iteration_message.format(count, 1.0 - ratio))

    print(success_message.format(new_mean))
    os.makedirs(output_path, exist_ok=True)

    output_file1_pts = os.path.join(output_path, os.path.basename(file1))
    output_file1_xf = os.path.join(output_path, os.path.basename(file1_xf))
    output_file2_pts = os.path.join(output_path, os.path.basename(file2))
    write_pts(output_file1_pts, pts1)
    write_pts(output_file2_pts, pts2)
    write_xf(output_file1_xf, M1)
    write_xf(output_file2_xf, M2)

    if write_text_output:
        file1_txt = os.path.join(
            output_path, os.path.splitext(os.path.basename(file1))[0] + ".txt"
        )
        file2_txt = os.path.join(
            output_path, os.path.splitext(os.path.basename(file2))[0] + ".txt"
        )
        write_txt(file1_txt, M1)
        write_txt(file2_txt, M2)

    if log_path:
        with open(log_path, "a", encoding="utf-8") as log_file:
            log_file.write(success_message.format(new_mean) + "\n")

    return {"mean_distance": new_mean, "iterations": count, "output_path": output_path}

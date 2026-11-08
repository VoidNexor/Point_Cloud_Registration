# 文件：icp.py
# 简介：实现了迭代最近点算法
#       接受两个*.pts文件作为参数，尝试将第一个文件中的点与第二个文件中的点对齐。
#       期望每个文件都有对应的*.xf文件。

import os
import numpy as np
from sys import argv
from random import shuffle
from math import *
from lib.utils import *
from lib.kdtree import KdTree

output_path = 'output01'

# 检查使用情况
if (len(argv) != 3):
    print("使用错误：icp.py需要两个额外的参数。\n"
          "正确的用法是 \"icp.py file1.pts file2.pts\"")
    quit()

# 检查pts文件是否存在
file1 = argv[1]
file2 = argv[2]
if (not os.path.isfile(file1)):
    print("错误：找不到.pts文件：" + file1)
    quit()
if (not os.path.isfile(file2)):
    print("错误：找不到.pts文件：" + file2)
    quit()

# 加载pts
pts1 = load_pts(file1)
pts2 = load_pts(file2)

# 检查xf文件是否存在
file1_xf = os.path.splitext(file1)[0] + '.xf'
file2_xf = os.path.splitext(file2)[0] + '.xf'
if (not os.path.isfile(file1_xf)):
    print("警告：找不到.xf文件：" + file1_xf)
    print("默认使用4x4单位矩阵...")
    M1 = np.matrix(np.identity(4))
else:
    M1 = load_xf(file1_xf)

# 注意，如果存在"output"file2.xf，则需要加载，否则会覆盖之前的工作
output_file2_xf = os.path.join(output_path, os.path.basename(file2_xf))
if (not os.path.isfile(output_file2_xf)):
    if (not os.path.isfile(file2_xf)):
        print("警告：找不到.xf文件：" + file2_xf)
        print("默认使用4x4单位矩阵...")
        M2 = np.matrix(np.identity(4))
    else:
        M2 = load_xf(file2_xf)
else:
    print("使用变换 {} 作为目标".format(output_file2_xf))
    M2 = load_xf(output_file2_xf)

# 从文件2中的点构建一个kd树
print("正在从 {} 构建KdTree...".format(file2))
kdtree = KdTree()
for p in pts2:
    kdtree.insert(p)

# ICP迭代（直到正负改进小于设定比例）

max_iterations = 50  # 设置最大迭代次数
print("开始迭代...")
ratio = 0.0
M2_inverse = M2.I
pts_index = [i for i in range(len(pts1))]
count = 0
while (1.0 - ratio > 0.0001 and count < max_iterations):
    # 随机选择1000个点
    shuffle(pts_index)
    # 应用M1和M2的逆
    p = [pts1[i].copy().transform(M1).transform(M2_inverse) for i in pts_index[:2000]]
    q = [kdtree.nearest(point) for point in p]

    # 计算点到平面的距离
    point2plane = [abs(np.subtract(pi.s, qi.s).dot(qi.n)) for pi,qi in zip(p,q)]
    median_3x = 0.75 * np.median(point2plane) # 数据集坐标值比较大时可设置为3倍，较小时根据实际情况调整

    # 剔除异常值
    point_pairs = []
    dist_sum = 0.0
    for i, pair in enumerate(zip(p,q)):
        if (point2plane[i] <= median_3x):
            point_pairs.append(pair)
            dist_sum += point2plane[i]
    if (len(point_pairs) > 0):
        old_mean = dist_sum/len(point_pairs)
    else:
        print("错误：在计算距离平均值时出了问题")
        quit()

    # 构建C和d
    C = np.zeros(shape=(6,6))
    d = np.zeros(shape=(6,1))
    for (p, q) in point_pairs:
        Ai = np.matrix(np.append(np.cross(p.s, q.n),q.n))
        AiT = Ai.T
        bi = np.subtract(q.s, p.s).dot(q.n)

        C += AiT*Ai
        d += AiT*bi

    # 解线性方程组并计算Micp
    try:
        x = np.linalg.solve(C,d).flatten()
    except np.linalg.LinAlgError:
        print("错误：点云几何信息不足，无法计算ICP变换")
        raise SystemExit(1)
    rx,ry,rz,tx,ty,tz = x
    Micp = np.matrix([[1.0, ry*rx - rz, rz*rx + ry, tx],[rz, 1.0 + rz*ry*rx, rz*ry - rx, ty], [-ry, rx, 1.0, tz], [0, 0, 0, 1.0]])

    # 计算新的平均点到平面距离
    dist_sum = 0.0
    for (p, q) in point_pairs:
        # 应用Micp
        p = p.transform(Micp)
        dist_sum += abs(np.subtract(p.s, q.s).dot(q.n))
    new_mean = dist_sum/len(point_pairs)
    count += 1
    ratio = new_mean / old_mean

    # 如果我们改进了就更新M1（否则，将终止）
    if (ratio < 1.0):
        M1 = M2*Micp*M2_inverse*M1
    else:
        new_mean = old_mean

    print("完成了迭代 #{}，改进了 {:2.4%}".format(count, 1.0 - ratio))

print("成功终止，采样的平均距离为 {}".format(new_mean))
# 添加日志记录函数
def log_to_file(message, log_file):
    with open(log_file, "a") as f:  # 使用追加模式'a'
        f.write(message + "\n")
log_message = "成功终止，采样的平均距离为 {}".format(new_mean)
log_to_file(log_message, "结果记录.txt")  # 将日志写入文件

# 将结果写入文件
output_file1_pts = os.path.join(output_path, os.path.basename(file1))
output_file1_xf = os.path.join(output_path, os.path.basename(file1_xf))
output_file2_pts = os.path.join(output_path, os.path.basename(file2))
output_file2_xf = os.path.join(output_path, os.path.basename(file2_xf))
write_pts(output_file1_pts, pts1)
write_pts(output_file2_pts, pts2)
write_xf(output_file1_xf, M1)
write_xf(output_file2_xf, M2)

# 将转移矩阵写入文件.txt，方便配合CloudCompare使用
file1_txt = os.path.join(output_path, os.path.splitext(os.path.basename(file1))[0] + '.txt')
file2_txt = os.path.join(output_path, os.path.splitext(os.path.basename(file2))[0] + '.txt')
write_txt(file1_txt, M1)
write_txt(file2_txt, M2)

# 全部完成
quit()

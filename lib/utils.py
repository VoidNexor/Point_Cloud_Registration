# 项目：点云配准
#
# 文件：utils.py
# 简介：提供用于读写.pts和.xf文件的实用函数

import os
import numpy as np
from .point import Point

# 从给定的.xf文件加载数据到4x4的np矩阵
def load_xf(file_name):
    with open(file_name) as f:
        data = f.read()
        rows = []
        for r in data.split('\n'):
            if (len(r) > 0):
                rows.append(r)

        if (len(rows) != 4):
            print("错误：在.xf文件中检测到的行数无效")
            rows = ["0 0 0 0" for i in range(4)]

        # 可以用一行代码完成，但这样有错误检查
        result = []
        for r in rows:
            c = []
            for v in r.split():
                c.append(float(v))
            if (len(c) != 4):
                print("错误：在{}中检测到的列数无效".format(file_name))
                c = [0, 0, 0, 0]
            result.append(c)

    return np.matrix(result)

# 从给定的.pts文件加载数据到点的列表
def load_pts(file_name):
    with open(file_name) as f:
        data = f.read()
        rows = data.split('\n')

        result = []
        for r in rows:
            if (len(r) == 0):
                continue
            pData = [float(v) for v in r.split()]
            if (len(pData) != 6):
                print("错误：在{}中为一个点提供的数据不足".format(file_name))
                pData = [0, 0, 0, 0, 0, 0]
            result.append(Point(pData[0:3], pData[3:6]))

    return result

# 将提供的矩阵M写入指定的.xf文件
def write_xf(file_name, M):
    # 如果需要，创建目录
    dir = os.path.dirname(file_name)
    if (not os.path.exists(dir)):
        os.makedirs(dir)

    # 写入文件
    with open(file_name, "w") as f:
        for row in M.A:
            for val in row:
                f.write(str(val))
                f.write(' ')
            f.write('\n')
    return

# 将提供的点列表写入指定的.pts文件
def write_pts(file_name, pts):
    # 如果需要，创建目录
    dir = os.path.dirname(file_name)
    if (not os.path.exists(dir)):
        os.makedirs(dir)

    # 写入文件
    with open(file_name, "w") as f:
        for p in pts:
            for val in (p.s + p.n):
                f.write(str(val))
                f.write(' ')
            f.write('\n')
    return

# 将提供的矩阵 M 写入指定的 .txt 文件
def write_txt(file_name, M):
    # 如果需要，创建目录
    dir = os.path.dirname(file_name)
    if not os.path.exists(dir):
        os.makedirs(dir)

    # 写入文件
    with open(file_name, "w") as f:
        for row in M.A:
            f.write(' '.join(map(str, row)) + '\n')
    return

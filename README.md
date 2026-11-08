# 点云配准

这是一个使用 Python 和 NumPy 实现的点云 ICP 配准示例，包含 Stanford Bunny 数据和可选的 Open3D FPFH 快速全局配准流程。

此项目是在Reilly Bova公开的[Point-Cloud-Registration](https://github.com/ReillyBova/Point-Cloud-Registration)基础上的拓展，新增了基于FPFH特征的快速全局配准（Fast Global Registration）功能。
通过Open3D库中的FPFH特征描述符和特征匹配算法，本项目实现了点云数据的快速粗配准，为精确配准提供了一个接近正确的初始对齐估计。

这个代码库包含了一个使用 Python 3 编写的脚本，实现了点云的迭代最近点（ICP）算法，用于 3D 点云的配准。由于是ICP点对面算法，主要针对带有法向量的bunny数据集进行适配，也可对计算法向量后的bunny点云数据集进行配准。
增加txt格式的输出，以方便配合CloudCompare使用。

数据集：源自斯坦福3D扫描存储库，一个在学术界广泛认可的资源，提供原始的PLY格式点云数据。

数据集路径为`bunny/`。

## 开始

按照以下说明，您可以在本地机器上运行这个脚本。项目已在 Windows 11 和 Linux 环境中验证。

## English quick start

The core ICP workflow requires Python 3.8+ and NumPy. Install the dependency and run a bundled example:

```bash
python -m pip install -r requirements.txt
python icp.py PLY_PTS/bun045.pts PLY_PTS/bun000.pts
```

Results are written to `output02/`. The `.xf` transform files are optional; identity transforms are used when they are absent. Run the smoke tests with:

```bash
python -m unittest discover -s tests -v
```

Install `requirements-optional.txt` for PLY conversion and Open3D FPFH global registration.

### 先决条件和安装

需要 Python 3.8 或更高版本。核心 ICP 流程只需要 NumPy：

```
python -m pip install -r requirements.txt
```

运行内置 smoke tests：

```
python -m unittest discover -s tests -v
```

要运行 PLY 转换和 FPFH 快速全局配准，还需要安装 Open3D：

```
python -m pip install -r requirements-optional.txt
```

### 最小示例

以下命令会将 `bun045` 配准到 `bun000`，结果写入当前目录的 `output02/`：

```
python icp.py PLY_PTS/bun045.pts PLY_PTS/bun000.pts
```

如果 `.xf` 文件不存在，程序会使用单位变换矩阵；输出目录会自动创建。

### 可选的 PLY / FPFH 流程

要对没有法向量的数据集进行法向量计算，则需要安装 Open3D，使用现有的 Open3D 库函数将 PLY 转换为 PTS：

```
python PLY_PTS.py bunny/data/bun000.ply
python PLY_PTS.py bunny/data/bun045.ply
python PLY_PTS.py bunny/data/bun090.ply
python PLY_PTS.py bunny/data/bun180.ply
python PLY_PTS.py bunny/data/bun270.ply
python PLY_PTS.py bunny/data/bun315.ply
python PLY_PTS.py bunny/data/chin.ply
python PLY_PTS.py bunny/data/ear_back.ply
python PLY_PTS.py bunny/data/top2.ply
python PLY_PTS.py bunny/data/top3.ply
```
并进行快速全局配准（Fast Global Registration）粗配准，获取转移矩阵，得到一个较好的初始位置。
获得的转移矩阵文件需要放到对应配准点云数据文件夹下。

```
python registration.py bunny/data/bun045.ply bunny/data/bun000.ply
python registration.py bunny/data/bun090.ply bunny/data/bun045.ply
python registration.py bunny/data/bun315.ply bunny/data/bun000.ply
python registration.py bunny/data/bun270.ply bunny/data/bun315.ply
python registration.py bunny/data/bun180.ply bunny/data/bun090.ply
python registration.py bunny/data/chin.ply bunny/data/bun315.ply
python registration.py bunny/data/ear_back.ply bunny/data/bun180.ply
python registration.py bunny/data/top2.ply bunny/data/bun180.ply
python registration.py bunny/data/top3.ply bunny/data/bun045.ply
```

### 运行脚本

运行这个脚本需要两个 `.pts` 文件；对应的 `.xf` 文件是可选的。程序会尝试调整源点云的刚体变换，使其与目标点云对齐，并将结果写入 `output01/` 或 `output02/`。

程序的执行方式如下：

```
python icp_ply_pts.py file1.pts file2.pts

```

两个脚本都支持 `--output`、`--iterations`、`--sample-size` 和 `--seed` 参数。使用 `--help` 查看完整选项；例如：

```
python icp.py PLY_PTS/bun045.pts PLY_PTS/bun000.pts --output /tmp/icp-result --seed 0
```

注意 `.xf` 文件名会根据 `.pts` 文件名自动推断。程序会首先在对应输出目录中查找目标 `.xf`，然后再查找输入文件旁边的 `.xf`；如果两处都没有，就使用单位矩阵。

`icp_ply_pts.py` 默认输出到 `output01/`，`icp.py` 默认输出到 `output02/`。两个目录均相对于运行命令时的当前目录。
这些输出目录和运行日志属于生成物，已加入 Git 忽略规则。

## 程序解释

### 实现细节

这个程序使用了一个自定义的 Python 实现的 kd 树。

此外，该脚本严重依赖于 NumPy 库提供的矩阵操作和线性代数方法。

### 迭代点云算法

在每次 ICP 迭代中，从源数据集（`file1`）中随机采样 1000 个点，然后计算每个采样点在目标数据集（`file2`）中的最近邻。然后，应用异常值剔除，并将剩余的点输入到过度约束的线性系统中。解决这个问题后，计算出应用于源数据集的新变换矩阵，如果有显著改进的话，继续开始新的迭代周期。否则，ICP 算法终止，并给出了一个刚体变换矩阵，将源数据集中的点与目标数据集中的点对齐。

有关此算法的更多细节可以在[这里](http://www.cs.princeton.edu/courses/archive/fall18/cos526/notes/cos526_f18_lecture10_acquisition_registration.pdf)找到。

### 其他说明

这个程序包含了相当健全的错误处理，但是还没有经过严格的测试以发现错误。

## 结果

|                           配准前                           | 配准后 |
|:-------------------------------------------------------:|:----------------:|
| ![Before alignment](/results/bunny_before.png?raw=true) | ![After alignment](/results/bunny_after.png?raw=true) |

查看此项目配准前后结果，需配合CloudCompare进行查看。

要自己生成对齐的兔子，请运行 `icp_ply_pts.py`；如需使用另一套核心 ICP 输出，则运行 `icp.py`。两个脚本都会在运行目录下生成对应的输出目录。

数据集
```

python icp_ply_pts.py .\PLY_PTS\bun045.pts .\PLY_PTS\bun000.pts
python icp_ply_pts.py .\PLY_PTS\bun090.pts .\PLY_PTS\bun045.pts
python icp_ply_pts.py .\PLY_PTS\bun315.pts .\PLY_PTS\bun000.pts
python icp_ply_pts.py .\PLY_PTS\bun270.pts .\PLY_PTS\bun315.pts
python icp_ply_pts.py .\PLY_PTS\bun180.pts .\PLY_PTS\bun270.pts
python icp_ply_pts.py .\PLY_PTS\chin.pts .\PLY_PTS\bun315.pts
python icp_ply_pts.py .\PLY_PTS\ear_back.pts .\PLY_PTS\bun180.pts
python icp_ply_pts.py .\PLY_PTS\top2.pts .\PLY_PTS\bun180.pts
python icp_ply_pts.py .\PLY_PTS\top3.pts .\PLY_PTS\bun000.pts

```

采样的平均距离的结果输出会追加到对应的txt文件中。

## 作者

* **熊泰** 


## 参考文献
[1] Rusinkiewicz, S.; Levoy, M. Efficient Variants of the ICP Algorithm. In Proceedings Third International Conference on 3-D Digital Imaging and Modeling; 2001; pp 145–152. https://doi.org/10.1109/IM.2001.924423. 

## 许可证

此项目根据 MIT 许可证获得许可 - 有关详细信息，请参见 [LICENSE.md](LICENSE.md) 文件。

## 致谢

特别感谢 Reilly Bova 公开其 [Point-Cloud-Registration](https://github.com/ReillyBova/Point-Cloud-Registration) 项目。该项目不仅为我提供了实践点云配准算法的宝贵资源，还极大地启发了我的思路和方法。

此外，还要对Open3D社区表示衷心的感谢，Open3D是一个功能强大且易于使用的开源库。


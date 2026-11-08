"""Chinese command-line entry point for the PTS ICP workflow."""

import argparse
import os

from lib.icp_runner import run_icp


def build_parser():
    parser = argparse.ArgumentParser(
        description="使用点到平面 ICP 对齐两个 PTS 点云。"
    )
    parser.add_argument("file1", help="源 .pts 文件")
    parser.add_argument("file2", help="目标 .pts 文件")
    parser.add_argument("--output", default="output01", help="输出目录")
    parser.add_argument("--iterations", type=int, default=50)
    parser.add_argument("--sample-size", type=int, default=2000)
    parser.add_argument("--seed", type=int, help="随机采样种子")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.iterations < 1 or args.sample_size < 1:
        build_parser().error("--iterations 和 --sample-size 必须为正数")
    try:
        run_icp(
            args.file1,
            args.file2,
            output_path=args.output,
            sample_size=args.sample_size,
            outlier_scale=0.75,
            max_iterations=args.iterations,
            seed=args.seed,
            write_text_output=True,
            log_path=os.path.join(args.output, "result.log"),
            language="zh",
        )
    except (FileNotFoundError, ValueError) as error:
        build_parser().error(str(error))


if __name__ == "__main__":
    main()

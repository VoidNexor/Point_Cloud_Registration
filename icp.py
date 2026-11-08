"""Command-line entry point for the NumPy ICP workflow."""

import argparse

from lib.icp_runner import run_icp


def build_parser():
    parser = argparse.ArgumentParser(
        description="Align two point clouds with point-to-plane ICP."
    )
    parser.add_argument("file1", help="source .pts file")
    parser.add_argument("file2", help="target .pts file")
    parser.add_argument("--output", default="output02", help="output directory")
    parser.add_argument("--iterations", type=int, default=50)
    parser.add_argument("--sample-size", type=int, default=1000)
    parser.add_argument("--seed", type=int, help="random sampling seed")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.iterations < 1 or args.sample_size < 1:
        build_parser().error("--iterations and --sample-size must be positive")
    try:
        run_icp(
            args.file1,
            args.file2,
            output_path=args.output,
            sample_size=args.sample_size,
            outlier_scale=3.0,
            max_iterations=args.iterations,
            seed=args.seed,
        )
    except (FileNotFoundError, ValueError) as error:
        build_parser().error(str(error))


if __name__ == "__main__":
    main()

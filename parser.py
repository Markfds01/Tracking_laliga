import sys
import argparse


def parse_args(args=sys.argv[1:]):
    custom_parser = argparse.ArgumentParser()

    # Mandatory parameters
    custom_parser.add_argument(
        "filename",
        help="Name of the file in data/processed to analyze (without the extension)"
    )

    # Optional parameters
    custom_parser.add_argument(
        "-s",
        "--single-frame",
        type=int,
        help="Analyze just the file provided"
    )

    # Add a boolean argument (flag)
    custom_parser.add_argument(
        "-iv",
        "--include-velocities",
        action=argparse.BooleanOptionalAction,
        help="A boolean flag argument"
    )

    custom_parser.add_argument(
        "-o",
        "--one-half",
        type=int,
        help="Analyze one half"
    )

    custom_parser.add_argument(
        "-sh",
        "--stamine-home",
        type=float,
        help="Apply a stamine factor to the home team"
    )

    custom_parser.add_argument(
        "-sa",
        "--stamine-away",
        type=float,
        help="Apply a stamine factor to the away team"
    )

    custom_parser.add_argument(
        "-pos",
        "--position-increase",
        type=str,
        nargs='+',
        help ="Increase the velocities only for the positions given"

    )

    custom_parser.add_argument(
        "-m",
        "--multiple-frames",
        type=int,
        nargs='+',  # Accept one or more integers
        help="Analyze this list of frames"
    )

    return custom_parser.parse_args(args)

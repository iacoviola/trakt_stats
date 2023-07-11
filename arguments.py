import argparse

def get_args():
    parser = argparse.ArgumentParser(description="Trakt.tv library sync")
    parser.add_argument(
        "-v",
        "--verbose",
        dest="verbose",
        action="store_true",
        default=False,
        help="Verbose output",
    )

    return parser.parse_args()

args = get_args()
vprint = print if args.verbose else lambda *a, **k: None
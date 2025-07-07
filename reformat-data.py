# SPDX-License-Identifier: AGPL-3.0-or-later
"""Merge two player records in LurkBait Twitch Fishing record files"""

import json
from argparse import ArgumentParser
from collections.abc import Collection
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class Args:
    target: str
    other_handles: list[str]


def without_keys(d: dict[str, Any], keys: Collection[str]):
    return {k: v for k, v in d.items() if k not in keys}


def main() -> None:
    parser = ArgumentParser()
    args = parser.parse_args(namespace=Args)

    data = Path(".") / "data"

    for data_file in data.glob("*.txt"):
        print("reformatting", data_file)
        with data_file.open("r", encoding="utf8") as fp:
            text = fp.read().strip("﻿")
            data = json.loads(text)
        with data_file.open("w", encoding="utf8") as fp:
            json.dump(data, fp, indent=2, sort_keys=True)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass

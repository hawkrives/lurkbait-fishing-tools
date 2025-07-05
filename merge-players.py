# SPDX-License-Identifier: AGPL-3.0-or-later
"""Merge two player records in LurkBait Twitch Fishing record files"""

import json
from argparse import ArgumentParser
from collections.abc import Collection
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from sqlite_utils import Database
from sqlite_utils.db import NotFoundError, Table


@dataclass(frozen=True, slots=True)
class Args:
    target: str
    other_handles: list[str]


def without_keys(d: dict[str, Any], keys: Collection[str]):
    return {k: v for k, v in d.items() if k not in keys}


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument(
        "-t", "--target", required=True, help="the handle to merge into"
    )
    parser.add_argument("other_handles", nargs="+", help="the handles to be merged")
    args = parser.parse_args(namespace=Args)
    all_handles = [args.target, *args.other_handles]

    # Path("./lurkbait.sqlite3").unlink()
    db = Database(memory=True, strict=True)
    player_data: Table = cast(Table, db.table("player_data", pk="handle"))

    examples = Path(".") / "examples"

    # step 1, load the player data into a sqlite3 database
    with (examples / "PlayerData.txt.json").open("r", encoding="utf8") as fp:
        data = json.load(fp)
        player_data.insert_all({"handle": key, **value} for key, value in data.items())

    # step 1.5, ensure that the target handles exist
    missing_handles = set()
    for handle in all_handles:
        try:
            player_data.get(handle)
        except NotFoundError:
            missing_handles.add(handle)

    if missing_handles:
        print(
            f"could not find Twitch handles {sorted(missing_handles)} in the PlayerData file."
        )
        return

    # step 2, merge each other_handle into target_handle
    all_handles = [args.target, *args.other_handles]
    all_updated = db.query(
        f"""
            SELECT
                SUM(gold) AS gold,
                SUM(goldSnapshot) AS goldSnapshot,
                SUM(totalCasts) AS totalCasts,
                SUM(totalCastsSnapshot) AS totalCastsSnapshot,
                MAX(lastCast) AS lastCast
            FROM player_data
            WHERE handle IN ({",".join("?" for _ in all_handles)})
            GROUP BY ?
        """,
        [*all_handles, args.target],
    )
    updated = next(all_updated)

    player_data.delete(args.other_handles)
    player_data.update(args.target, updated)

    # step 3, write the data back to disk
    with (examples / "PlayerData.txt.json").open("w", encoding="utf8") as fp:
        data = {
            record["handle"]: without_keys(record, "handle")
            for record in player_data.rows
        }
        json.dump(data, fp, indent=2, sort_keys=True)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass

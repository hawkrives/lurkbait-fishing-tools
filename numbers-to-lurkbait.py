# SPDX-License-Identifier: AGPL-3.0-or-later
"""Extract data from a specific Numbers.app spreadsheet into the CustomCatches.txt and CustomCatches/ folder expected by LurkBait Twitch Fishing"""

import argparse
import json
import types
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import numbers_parser
import numbers_parser.cell
import sqlite_utils
from numbers_parser.cell import BoolCell, EmptyCell, NumberCell, TextCell
from PIL import Image


@dataclass(frozen=True, slots=True)
class Args:
    numbers_file: Path


def main() -> None:
    args = argparse.ArgumentParser()
    args.add_argument("numbers_file", type=Path)
    parser = args.parse_args(namespace=Args)

    db = sqlite_utils.Database("./custom_catches.sqlite3", strict=True, recreate=True)

    custom_catches = cast(
        sqlite_utils.db.Table,
        db.table(
            "custom_catches",
            pk="FullName",
            columns={
                "FullName": str,
                "Description": str,
                "BaseValue": int,
                "BaseWeight": float,
                "SpritePath": str,
                "AudioPath": str,
                "LoadError": bool,
            },
        ),
    )

    input_data = cast(
        sqlite_utils.db.Table,
        db.table(
            "input_data",
            pk="Fish",
            columns={
                "Fish": str,
                "Image": bytes,
                "Excluded": bool,
                "Source": str,
                "Gold": int,
                "Weight": float,
                "Rarity": str,
            },
        ),
    )

    doc = numbers_parser.Document(parser.numbers_file)
    sheets = doc.sheets
    tables = sheets[0].tables
    rows = tables[0].rows()
    data_rows = cast(list[list[numbers_parser.cell.Cell]], rows[1:])

    row_schema: list[tuple[str, type | types.UnionType]] = [
        ("Fish", TextCell),
        ("Image", EmptyCell | TextCell),
        ("Excluded", BoolCell),
        ("Source", TextCell),
        ("Gold", NumberCell),
        ("Weight", NumberCell),
        ("Rarity", TextCell),
    ]

    def validate_row(
        row: list[numbers_parser.cell.Cell],
    ) -> tuple[
        TextCell,
        EmptyCell | TextCell,
        BoolCell,
        TextCell,
        NumberCell,
        NumberCell,
        TextCell,
    ]:
        output = []
        for i, (cell, (name, instance)) in enumerate(zip(row, row_schema)):
            try:
                assert isinstance(cell, instance), (
                    f"expected {instance} but got {type(cell)} for column {name!r}"
                )
                output.append(cell)
            except AssertionError:
                for cell in row:
                    print(f"- {cell}")
                raise
        return tuple(output)

    for i, row in enumerate(data_rows):
        if isinstance(row[0], numbers_parser.cell.EmptyCell):
            continue

        fish, image, excluded, source, gold, weight, rarity = validate_row(row)
        assert image.style is not None
        assert isinstance(image.style.bg_image, numbers_parser.cell.BackgroundImage)

        input_data.insert(
            {
                "Fish": fish.value,
                "Image": image.style.bg_image.data,
                "Excluded": excluded.value,
                "Source": source.value,
                "Gold": gold.value,
                "Weight": weight.value,
                "Rarity": rarity.value,
            }
        )

    output_dir = Path(".") / "data"

    catches_dir = output_dir / "CustomCatches"
    catches_dir.mkdir(exist_ok=True)
    for row in input_data.rows:
        if row["Excluded"]:
            continue
        print(row["Fish"])
        sprite_path = catches_dir / cast(str, row["Fish"])
        sprite_path = sprite_path.with_suffix(".png")
        with sprite_path.open("wb") as fp:
            fp.write(row["Image"])
        with Image.open(sprite_path) as im:
            im.thumbnail((256, 256), Image.Resampling.LANCZOS)
            im.save(sprite_path, "PNG")

        custom_catches.insert(
            {
                "FullName": row["Fish"],
                "Description": row["Source"],
                "BaseValue": row["Gold"],
                "BaseWeight": row["Weight"],
                "SpritePath": str(sprite_path.name),
                "AudioPath": "",
                "LoadError": False,
            }
        )

    catches_file = output_dir / "CustomCatches.txt"

    with catches_file.open("w", encoding="utf8") as fp:
        data = {}
        for record in custom_catches.rows:
            record["LoadError"] = bool(record["LoadError"])
            data[record["FullName"]] = record

        json.dump(data, fp, indent=2, sort_keys=True)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass

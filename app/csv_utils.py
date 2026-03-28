from __future__ import annotations

import csv
import io
from itertools import chain
from dataclasses import dataclass
from typing import BinaryIO, TextIO


@dataclass
class SubtractResult:
    freqs: list[float]
    ampl: list[float]
    matched: int
    only_in_a: int
    only_in_b: int


@dataclass
class MergeResult:
    freqs: list[float]
    ampl: list[float]
    only_in_a: int
    only_in_b: int
    duplicate_freqs: int


def _parse_csv_reader(reader: csv.reader) -> dict[float, float]:
    header_row = next(reader, None)
    first_data_row = next(reader, None)
    if header_row is None or first_data_row is None:
        raise ValueError("В файле нет данных (нужен заголовок и хотя бы одна строка).")

    header = [h.strip().lower() for h in header_row]

    def col_index(*names: str) -> int:
        for i, h in enumerate(header):
            if h in names:
                return i
        return -1

    fi = col_index("freq", "frequency", "f")
    ai = col_index("ampl", "amp", "amplitude", "a")
    if fi < 0 or ai < 0:
        raise ValueError("Ожидаются колонки freq и ampl (допустимы frequency, amplitude).")

    out: dict[float, float] = {}
    for parts in chain([first_data_row], reader):
        if len(parts) <= max(fi, ai):
            continue
        try:
            f = float(parts[fi].strip().replace(",", "."))
            a = float(parts[ai].strip().replace(",", ".").strip('"'))
        except ValueError:
            continue
        out[f] = a

    if not out:
        raise ValueError("Не удалось прочитать ни одной числовой строки.")
    return out


def _parse_csv_text_stream(stream: TextIO, sample: str) -> dict[float, float]:
    reader = csv.reader(stream, delimiter="," if "," in sample or ";" not in sample else ";")
    return _parse_csv_reader(reader)


def parse_csv(text: str) -> dict[float, float]:
    text = text.strip()
    if not text:
        raise ValueError("Пустой файл.")

    sample = text.partition("\n")[0]
    return _parse_csv_text_stream(io.StringIO(text), sample)


def parse_csv_upload(file_obj: BinaryIO) -> dict[float, float]:
    file_obj.seek(0)
    text_stream = io.TextIOWrapper(file_obj, encoding="utf-8", newline="")
    try:
        sample = text_stream.readline().strip()
        if not sample:
            raise ValueError("Пустой файл.")
        text_stream.seek(0)
        return _parse_csv_text_stream(text_stream, sample)
    finally:
        text_stream.detach()


def sorted_series(m: dict[float, float]) -> tuple[list[float], list[float]]:
    freqs = sorted(m.keys())
    return freqs, [m[f] for f in freqs]


def subtract(
    map_a: dict[float, float],
    map_b: dict[float, float],
    a_minus_b: bool,
) -> SubtractResult:
    minuend = map_a if a_minus_b else map_b
    subtrahend = map_b if a_minus_b else map_a

    only_in_a = sum(1 for f in map_a if f not in map_b)
    only_in_b = sum(1 for f in map_b if f not in map_a)

    freqs: list[float] = []
    ampl: list[float] = []
    for f in sorted(minuend.keys()):
        if f in subtrahend:
            freqs.append(f)
            ampl.append(minuend[f] - subtrahend[f])

    return SubtractResult(
        freqs=freqs,
        ampl=ampl,
        matched=len(freqs),
        only_in_a=only_in_a,
        only_in_b=only_in_b,
    )


def merge_series(
    map_a: dict[float, float],
    map_b: dict[float, float],
    on_duplicate: str,
) -> MergeResult:
    if on_duplicate not in ("average", "a", "b"):
        raise ValueError("on_duplicate должен быть: average, a или b.")

    only_in_a = sum(1 for f in map_a if f not in map_b)
    only_in_b = sum(1 for f in map_b if f not in map_a)

    freqs_sorted = sorted(set(map_a) | set(map_b))
    ampl_out: list[float] = []
    duplicate_freqs = 0

    for f in freqs_sorted:
        in_a = f in map_a
        in_b = f in map_b
        if in_a and in_b:
            duplicate_freqs += 1
            if on_duplicate == "average":
                v = (map_a[f] + map_b[f]) / 2.0
            elif on_duplicate == "a":
                v = map_a[f]
            else:
                v = map_b[f]
        elif in_a:
            v = map_a[f]
        else:
            v = map_b[f]
        ampl_out.append(v)

    return MergeResult(
        freqs=freqs_sorted,
        ampl=ampl_out,
        only_in_a=only_in_a,
        only_in_b=only_in_b,
        duplicate_freqs=duplicate_freqs,
    )


def result_to_csv(freqs: list[float], ampl: list[float]) -> str:
    lines = ["freq,ampl"]
    for f, a in zip(freqs, ampl):
        lines.append(f"{f},{a}")
    return "\n".join(lines)

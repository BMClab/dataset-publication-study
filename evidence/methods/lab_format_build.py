"""Encode the same eight tables as a native database and Vortex, then verify every row."""

import argparse
import hashlib
import json
import time
from pathlib import Path

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq
import vortex as vx


def check_stream(reference, candidate):
    """Compare order and values in equal-sized slices regardless of batch boundaries."""
    batches = iter(candidate)
    block = None
    count = 0
    for expected in reference.iter_batches(batch_size=65536):
        offset = 0
        while offset < len(expected):
            while block is None or not len(block):
                block = next(batches)
            n = min(len(block), len(expected) - offset)
            actual = block.slice(0, n).cast(expected.schema)
            if not actual.equals(expected.slice(offset, n)):
                raise ValueError(f"Value mismatch at row {count}")
            count += n
            offset += n
            block = block.slice(n)
    assert (block is None or not len(block)) and not any(len(b) for b in batches)
    return count


def annotations(schema):
    metadata = {("table", k): v for k, v in (schema.metadata or {}).items()}
    for field in schema:
        metadata.update({(field.name, k): v for k, v in (field.metadata or {}).items()})
    return metadata


def inspect_schemas(work):
    """Which source annotations survive plain table access through each stored representation?"""
    rows = {}
    with duckdb.connect(str(work / "ppds.duckdb"), read_only=True) as con:
        for source in sorted((work / "parquet").glob("*.parquet")):
            name = source.stem
            schema = pq.ParquetFile(source).schema_arrow
            baseline = annotations(schema)
            candidates = {
                "sql_duckdb": con.sql(f'SELECT * FROM "{name}" LIMIT 0')
                .to_arrow_table()
                .schema
            }
            for folder in ("vortex", "vortex_compact"):
                candidates[folder] = vx.open(
                    str(work / folder / (name + ".vortex"))
                ).dtype.to_arrow_schema()
            rows[name] = {"parquet_annotation_keys": len(baseline), "readers": {}}
            for label, returned in candidates.items():
                meta = annotations(returned)
                rows[name]["readers"][label] = {
                    "same_field_names": schema.names == returned.names,
                    "same_types": all(
                        a.type == b.type for a, b in zip(schema, returned, strict=True)
                    ),
                    "matching_annotations": sum(
                        meta.get(k) == v for k, v in baseline.items()
                    ),
                }
    return {
        "tables": rows,
        "definition": "Source table-level and field-level key/value annotations, counted separately per field. Parquet file schema, native SQL result schema and Vortex dtype schema are the observed public surfaces.",
    }


def compact(work):
    """Measure Vortex's size-oriented writer on the identical Parquet inputs."""
    dest = work / "vortex_compact"
    dest.mkdir(exist_ok=False)
    manifest = json.loads((work / "fixture.json").read_text())
    rows = {}
    writer = vx.io.VortexWriteOptions.compact()
    with duckdb.connect(config={"threads": 1}) as con:
        con.execute("LOAD vortex")
        for name, item in manifest["tables"].items():
            path = work / "parquet" / f"{name}.parquet"
            with path.open("rb") as source:
                assert (
                    hashlib.file_digest(source, "sha256").hexdigest() == item["sha256"]
                )
            pf = pq.ParquetFile(path)
            output = dest / f"{name}.vortex"
            started = time.perf_counter()
            writer.write(
                pa.RecordBatchReader.from_batches(
                    pf.schema_arrow, pf.iter_batches(batch_size=65536)
                ),
                str(output),
            )
            elapsed = time.perf_counter() - started
            result = con.sql(
                "SELECT * FROM read_vortex(?)", params=[str(output)]
            ).to_arrow_reader(65536)
            assert check_stream(pf, result) == item["rows"]
            rows[name] = {
                "rows": item["rows"],
                "bytes": output.stat().st_size,
                "write_s": elapsed,
            }
            print("Verified compact", name, flush=True)
    return {
        "tables": rows,
        "bytes": sum(x["bytes"] for x in rows.values()),
        "verification": "Full ordered values against the same Parquet inputs.",
    }


def main(work):
    manifest = json.loads((work / "fixture.json").read_text())
    dbpath = work / "ppds.duckdb"
    vdir = work / "vortex"
    vdir.mkdir(exist_ok=False)
    if dbpath.exists():
        raise FileExistsError(dbpath)
    con = duckdb.connect(str(dbpath), config={"threads": 1})
    con.execute("LOAD vortex")
    rows = {}
    for name, item in manifest["tables"].items():
        source = work / "parquet" / (name + ".parquet")
        with source.open("rb") as f:
            assert hashlib.file_digest(f, "sha256").hexdigest() == item["sha256"]
        pf = pq.ParquetFile(source)
        dest = vdir / (name + ".vortex")
        t = time.perf_counter()
        vx.io.write(
            pa.RecordBatchReader.from_batches(
                pf.schema_arrow, pf.iter_batches(batch_size=65536)
            ),
            str(dest),
        )
        write_v = time.perf_counter() - t
        t = time.perf_counter()
        con.execute(
            f'CREATE TABLE "{name}" AS SELECT * FROM read_parquet(?)', [str(source)]
        )
        con.execute("CHECKPOINT")
        write_db = time.perf_counter() - t
        for query in [f'SELECT * FROM "{name}"', "SELECT * FROM read_vortex(?)"]:
            cursor = con.execute(query, [str(dest)] if "?" in query else [])
            assert check_stream(pf, cursor.to_arrow_reader(65536)) == item["rows"]
        rows[name] = {
            "rows": item["rows"],
            "parquet_bytes": item["bytes"],
            "vortex_bytes": dest.stat().st_size,
            "vortex_write_seconds": write_v,
            "db_write_checkpoint_seconds": write_db,
        }
        print("Verified", name, item["rows"], flush=True)
    con.close()
    return {
        "tables": rows,
        "bytes": {
            "parquet": sum(x["parquet_bytes"] for x in rows.values()),
            "vortex": sum(x["vortex_bytes"] for x in rows.values()),
            "duckdb": dbpath.stat().st_size,
        },
        "reference": manifest,
        "verification": "Full ordered row and column value equality after restoring source column types. Includes nulls and STL bytes; source schema metadata not guaranteed by conversions.",
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("work", type=Path)
    p.add_argument("output", type=Path)
    group = p.add_mutually_exclusive_group()
    group.add_argument("--compact", action="store_true")
    group.add_argument("--schemas", action="store_true")
    a = p.parse_args()
    operation = inspect_schemas if a.schemas else compact if a.compact else main
    a.output.write_text(json.dumps(operation(a.work), indent=2) + "\n")

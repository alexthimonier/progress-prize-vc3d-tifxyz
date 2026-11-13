import json
from pathlib import Path
import sqlite3
import sys
import uuid


def surface(database, identifier):
    with sqlite3.connect(f"{database.resolve().as_uri()}?mode=ro&immutable=1", uri=True) as store:
        key = uuid.UUID(identifier).bytes
        if store.execute("PRAGMA user_version").fetchone()[0] == 20:
            head = "SELECT revision_uuid FROM geometry_heads WHERE object_uuid = ?"
        else:
            head = ("SELECT r.geometry_uuid FROM object_heads h JOIN object_revisions r "
                    "ON r.uuid = h.revision_uuid WHERE h.object_uuid = ?")
        (revision,) = store.execute(head, (key,)).fetchone()
        meta, attributes = store.execute(
            """SELECT o.meta, json_extract(g.manifest, '$.attributes') FROM objects o
               JOIN geometry_revisions g ON o.uuid = g.object_uuid
               WHERE o.uuid = ? AND g.uuid = ?""", (key, revision),
        ).fetchone()
        data = {}
        for name, blob in store.execute(
            """SELECT r.array_name, c.data FROM geometry_revision_chunks r
               JOIN geometry_chunks c ON c.hash = r.hash WHERE r.revision_uuid = ?
               ORDER BY r.array_name, r.chunk_index""", (revision,),
        ):
            data.setdefault(name, bytearray()).extend(blob)
    return json.loads(meta), json.loads(attributes), data


original, roundtrip, exported = map(Path, sys.argv[1:])
export_meta = json.loads((exported / "meta.json").read_text())
identifier = export_meta["uuid"]
before_meta, before_geometry, before_arrays = surface(original, identifier)
after_meta, after_geometry, after_arrays = surface(roundtrip, identifier)
assert before_meta["coordinates"] == after_meta["coordinates"] == export_meta["coordinates"]
assert before_geometry["scale"] == after_geometry["scale"] == export_meta["scale"]
assert export_meta["source"] == after_meta["source"]["source"] == before_meta["source"]
for field in ("points", "generations"):
    assert before_arrays[field] == after_arrays[field], field
    print(f"{field}: {len(before_arrays[field])} bytes identical")
print(f"Volume binding {export_meta['coordinates']}; grid scale {export_meta['scale']}; provenance {export_meta['source']}")

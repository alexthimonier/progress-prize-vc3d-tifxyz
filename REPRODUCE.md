# Reproduce the VC3D TIFXYZ export failure and fix

## Create the input in VC3D

1. Open PHerc. 800 from the [Vesuvius Challenge open-data catalog](https://scrollprize.org/data_browser/PHerc0800). Use CT volume `20250521135224` and its associated m7 surface prediction (`20260413222639`).
2. Use **Create Segment (GrowPatch)** around XYZ `(5144, 5123, 8632)`. Request eight generations. This creates a native surface directly in the VC3D project. Do not export and import it before the comparison; that would take the other metadata path.
3. Export the resulting object as TIFXYZ using `objects.export` through the [VC3D agent bridge](https://github.com/ScrollPrize/villa/blob/14d4e725df8b569e6fc8ceb3c04d130f705c1565/volume-cartographer/apps/VC3D/agent_bridge/SPEC.md). Use a new output path on each run. The [bridge script](repro/bridge_export.py) sends the command below and polls `job.status` until it finishes:

```json
{"jsonrpc":"2.0","id":1,"method":"objects.export","params":{"uuid":"<native-surface-uuid>","path":"<new-tifxyz-directory>"}}
```

The pre-fix release tested was Apple Silicon VC3D `740f0103b9574e9e88bbb24a8438dbe1d5a1a0c0`. The export ends in `failed`, with `[json.exception.type_error.307] cannot use erase() with string`. A surface imported from TIFXYZ in the same project served as the control: it exported successfully.

## Apply the fix and run the regression

Clone [villa](https://github.com/ScrollPrize/villa) and check out `14d4e725df8b569e6fc8ceb3c04d130f705c1565`. From the villa root, apply `patches/native-surface-tifxyz-export.patch` from this repository. The supported full VC3D build scripts are in [`volume-cartographer/scripts`](https://github.com/ScrollPrize/villa/tree/14d4e725df8b569e6fc8ceb3c04d130f705c1565/volume-cartographer/scripts).

### Native macOS comparison

For the published before/after, build the `VC3D` target with the `macos-homebrew-llvm` preset, `CMAKE_BUILD_TYPE=QuickBuild`, and OpenCV 4 (`-DOpenCV_DIR=/opt/homebrew/opt/opencv@4/lib/cmake/opencv4` on the test Mac). Optional FlatBoi, Fiberlets, CUDA and the object-store server were disabled (`VC_BUILD_FLATBOI`, `VC_BUILD_FIBERLETS`, `VC_READER_ENABLE_CUDA`, `VC_OBJECT_STORE_BUILD_SERVER`). Homebrew LLVM 23 also required the [explicit `<exception>` include](repro/llvm23-include.patch), applied to both builds. For the control, omit the TIFXYZ patch while keeping all other build inputs the same.

Start each binary on a separate copy of the project and its referenced store, using `--project /path/to/copy/PHerc0800.vcproj --agent-bridge-name /path/to/private/run/vc3d.sock`. Run `python3 repro/bridge_export.py /path/to/private/run/vc3d.sock '<native-surface-uuid>' /path/to/new-output`. The fixed build returns `succeeded`; the control returns `failed`.

### Standalone regression

The following standalone build exercises the same shared geometry exporter. The included [Dockerfile](repro/Dockerfile) lists the dependencies used on Ubuntu 24.04 arm64.

```sh
git apply /path/to/patches/native-surface-tifxyz-export.patch
cmake -S vc_object_store -B build-export -G Ninja \
  -DCMAKE_BUILD_TYPE=Release \
  -DVC_OBJECT_STORE_BUILD_ADAPTERS=ON \
  -DVC_OBJECT_STORE_BUILD_LINKING=OFF \
  -DVC_OBJECT_STORE_BUILD_TOOLS=ON \
  -DVC_OBJECT_STORE_BUILD_TESTS=ON \
  -DVC_OBJECT_STORE_BUILD_SERVER=OFF
cmake --build build-export --target vc_object_export vc_object_ingest vc_object_convert test_json_boundaries
ctest --test-dir build-export -R '^object_store_json_boundaries$' --output-on-failure
```

## Verify the same surface after export and reimport

Work on a copy. Use SQLite's backup command to snapshot the `.vcobj` object store if VC3D is open. In this experiment the release used schema 20 and the checkout used schema 21, so the official converter was run once. Skip conversion if your copy already uses the checkout's schema.

```sh
build-export/bin/vc_object_convert original.vcobj migrated.vcobj
build-export/bin/vc_object_export --db migrated.vcobj \
  --uuid '<native-surface-uuid>' --output exported
build-export/bin/vc_object_ingest --db reimported.vcobj --author validation \
  --surface exported --no-progress
python3 /path/to/repro/verify_roundtrip.py original.vcobj reimported.vcobj exported
```

The check compares stored coordinate and generation arrays byte for byte and verifies the coordinate binding, grid scale and provenance. It reads closed or checkpointed copies of the stores. The TIFXYZ directory contains `x.tif`, `y.tif`, `z.tif`, `generations.tif` and `meta.json`.

To check downstream use, run `vc_render_tifxyz --volume "$CT_ZARR" --segmentation exported --group-idx 0 --scale 1 --num-slices 1 --tif-output rendered`, where `CT_ZARR` is the PHerc. 800 volume URL from the catalog. For the original store render, replace `--segmentation exported` with `--store original.vcobj --surface '<native-surface-uuid>' --volume-uuid 20250521135224` using a release compatible with that store. Compare the resulting center TIFFs.

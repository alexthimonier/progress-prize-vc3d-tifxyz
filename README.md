# Export VC3D GrowPatch surfaces as TIFXYZ

VC3D could grow and display a new surface on PHerc. 800, but could not export it as TIFXYZ. The same export worked on surfaces that had first been imported from TIFXYZ. The [patch](patches/native-surface-tifxyz-export.patch) fixes that difference and adds a regression test for creating, exporting and reimporting a native surface.

TIFXYZ is a handoff format in the [Vesuvius Challenge unwrapping workflow](https://scrollprize.org/tutorial1). A usable export lets downstream tools render or flatten a surface grown in VC3D and lets another operator inspect that same surface. The patch changes export metadata handling. It does not change the GrowPatch algorithm, the quality of the trace, or ink detection.

## Cause and fix

Native GrowPatch writes a producer label such as `"source": "vc_grow_seg_from_seed"`; the import path stores an object in `source`. The shared geometry exporter expected an object and attempted to erase coordinate keys from the string. It now wraps a non-object value as a source label before that cleanup. The output retains the label and takes its coordinate binding from the native geometry record.

## Validation on PHerc. 800

The input was a native 18 × 18 GrowPatch surface from the [public PHerc. 800 scan](https://scrollprize.org/data_browser/PHerc0800), volume `20250521135224` at 8.64 µm. On Apple Silicon, VC3D without the patch failed with `[json.exception.type_error.307] cannot use erase() with string` and wrote no files. VC3D built from the same revision with the patch exported all five TIFXYZ files. Reimporting the output preserved all 3,888 bytes of XYZ samples, 648 bytes of generation values, the grid scale `[0.05, 0.05]`, volume binding and source label. A 360 × 360 render from the TIFXYZ also matched the same slice rendered from the original store.

See [the evidence](evidence/) and the [reproduction steps](REPRODUCE.md). The patch applies to [villa `14d4e725`](https://github.com/ScrollPrize/villa/tree/14d4e725df8b569e6fc8ceb3c04d130f705c1565).

Code and documentation are available under the [MIT License](LICENSE). PHerc. 800 scan data is provided by Vesuvius Challenge under [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/). The scan and local project database are not included. Codex assisted with diagnosis, implementation, testing and documentation.

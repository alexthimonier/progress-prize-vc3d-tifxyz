"""Show the PHerc. 800 validation patch and capture the VC3D window."""

import argparse
from pathlib import Path
import time

from bridge_export import rpc


def capture(endpoint, surface, output):
    assert rpc(endpoint, "state.get")["volume"]["id"] == "20250521135224"
    rpc(endpoint, "segments.activate", segmentId=surface)
    rpc(endpoint, "viewer.set_axis_aligned_slices", enabled=True)
    rpc(endpoint, "viewer.set_overlay", clear=True)
    rpc(endpoint, "viewer.set_intersects", surfaceIds=[surface])
    rpc(endpoint, "viewer.set_render_settings", intersectionOpacity=1,
        intersectionThickness=2, planeIntersectionLinesVisible=False,
        composite={"enabled": False})
    point = {"x": 5144, "y": 5123, "z": 8632}
    for viewer, fixed in (("v2", "z"), ("v4", "x")):
        cursor = rpc(endpoint, "canvas.get_cursor_volume_point", viewer=viewer,
                     scene={"x": 150, "y": 150})
        rpc(endpoint, "canvas.click", viewer=viewer,
            position={**point, fixed: cursor["volumePoint"][fixed]},
            space="volume", button="left", modifiers=["ctrl"])
    for viewer in ("v2", "v4"):
        rpc(endpoint, "viewer.center_on_point", viewer=viewer, point=point, forceRender=True)
    time.sleep(3)
    rpc(endpoint, "screenshot.capture", target="window", maxDim=1800,
        filePath=str(output.resolve()))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("socket", type=Path)
    parser.add_argument("uuid")
    parser.add_argument("png", type=Path)
    arguments = parser.parse_args()
    capture(arguments.socket, arguments.uuid, arguments.png)

"""Run the real VC3D export job and save its relevant result fields."""

import argparse
import json
from pathlib import Path
import socket
import sys
import time


def rpc(endpoint, method, **params):
    request = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.settimeout(30)
        client.connect(str(endpoint))
        client.sendall(json.dumps(request).encode() + b"\n")
        with client.makefile(encoding="utf-8") as stream:
            for line in stream:
                response = json.loads(line)
                if response.get("id") == 1:
                    if "error" in response:
                        raise RuntimeError(f"{method}: {response['error']}")
                    return response["result"]
    raise RuntimeError(f"No response to {method}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("socket", type=Path)
    parser.add_argument("uuid")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        parser.error("use a new path for the TIFXYZ export")
    started = rpc(args.socket, "objects.export", uuid=args.uuid, path=str(output))
    job_id = started["jobId"]
    for _ in range(120):
        job = rpc(args.socket, "job.status", jobId=job_id)
        if job.get("finishedAtMs") is not None:
            break
        time.sleep(0.25)
    else:
        raise TimeoutError(f"export job {job_id} did not finish")
    print(json.dumps({
        "uuid": args.uuid,
        "jobId": job_id,
        "kind": job["kind"],
        "state": job["state"],
        "message": job["message"].replace(str(output), "<output>"),
        "files": sorted(p.name for p in output.iterdir()) if output.is_dir() else [],
    }, indent=2))
    return 0 if job["state"] == "succeeded" else 1


if __name__ == "__main__":
    sys.exit(main())

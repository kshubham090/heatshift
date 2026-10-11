"""Copy only deployable source, verify Linux ARM64 binaries, then write the ZIP.

This deliberately does not import the cross-platform package on the build host.
It validates files, not a live Lambda execution or model entitlement.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import struct
import sys
import zipfile


def main() -> None:
    project, stage, output = (Path(p).resolve() for p in sys.argv[1:])
    for name in ("backend", "dist"):
        source = project / name
        if not source.is_dir():
            raise SystemExit(f"Missing required build directory: {source}")
        shutil.copytree(source, stage / name, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo", ".env*"))
    required = ["backend/app.py", "backend/agent.py", "backend/cloud_budget.py", "dist/index.html"]
    if not all((stage / name).is_file() for name in required):
        raise SystemExit("The package is missing an application or daily-limit component.")

    binary_names = []
    for path in stage.rglob("*.so"):
        header = path.read_bytes()[:20]
        if len(header) < 20 or header[:4] != b"\x7fELF" or header[4] != 2 or header[5] != 1:
            raise SystemExit(f"Not a 64-bit little-endian Linux ELF binary: {path.name}")
        if struct.unpack("<H", header[18:20])[0] != 183:  # EM_AARCH64
            raise SystemExit(f"Not an ARM64 binary: {path.name}")
        binary_names.append(str(path.relative_to(stage)))
    if not any("pydantic_core" in name for name in binary_names):
        raise SystemExit("The Python 3.13 ARM64 pydantic-core extension was not packaged.")

    files = sorted(path for path in stage.rglob("*") if path.is_file())
    if any(path.is_symlink() for path in files):
        raise SystemExit("Package symlinks are not allowed.")
    size = sum(path.stat().st_size for path in files)
    if size >= 250 * 1024 * 1024:
        raise SystemExit(f"Uncompressed package {size:,} bytes reaches Lambda's 250 MiB limit.")

    package = output / "heatshift-lambda.zip"
    with zipfile.ZipFile(package, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            archive.write(path, path.relative_to(stage))
    dependencies = []
    for metadata in sorted(stage.glob("*.dist-info/METADATA")):
        fields = {}
        for line in metadata.read_text().splitlines():
            if line.startswith(("Name: ", "Version: ")):
                key, value = line.split(": ", 1)
                fields[key] = value
        dependencies.append({"name": fields.get("Name"), "version": fields.get("Version")})
    report = {
        "runtime": "python3.13", "architecture": "arm64", "linux": "Amazon Linux 2023",
        "zip": package.name,
        "sha256": hashlib.sha256(package.read_bytes()).hexdigest(),
        "zipBytes": package.stat().st_size, "uncompressedBytes": size,
        "files": len(files), "verifiedArm64Extensions": binary_names,
        "dependencies": dependencies,
        "validation": "Build and ELF inspection only; not executed on AWS.",
    }
    manifest = output / "package-manifest.json"
    manifest.write_text(json.dumps(report, indent=2) + "\n")
    print(f"Package: {package}\nManifest: {manifest}")
    print(f"ZIP {package.stat().st_size / 1024**2:.1f} MiB; uncompressed {size / 1024**2:.1f} MiB")
    print(f"Verified {len(binary_names)} Linux ARM64 extensions. No AWS resources were created.")


if __name__ == "__main__":
    main()

"""Build one flake package and check it the ways CI can without a display."""

import re
import subprocess
from pathlib import Path

import common

# Every library a binary may name: what it links plus what package.nix puts on
# its RPATH for dlopen(). A name outside this set means upstream started
# loading something new, which would only fail at runtime -- so reject it and
# let a human extend package.nix. "library" is a false positive in LightCraft.
KNOWN_LIBS = {
    "libc", "libm", "libgcc_s", "libdl", "libpthread", "librt",
    "libasound", "libdbus-1", "libEGL", "libvulkan",
    "libwayland-client", "libwayland-egl",
    "libX11", "libX11-xcb", "libxcb", "libXcursor", "libXi",
    "libxkbcommon", "libxkbcommon-x11",
    "libva", "libva-drm",
    # NVIDIA driver libraries, found via /run/opengl-driver/lib.
    "libcuda", "libnvcuvid", "libnvidia-encode",
    "library",
}
# The last "lib" before ".so": binaries also embed distro package hints that
# run together (e.g. "libvulkan1vulkan-loaderlibEGL.so.1").
SONAME = re.compile(rb"(lib(?:(?!lib)[A-Za-z0-9_+-])+)\.so")


def attr(app, version=None):
    return app if version is None else f"{app}_{version.replace('.', '_')}"


def check(name):
    """Build flake attribute `name`; return a list of problems (empty = good)."""
    for _ in range(2):  # one retry: GitHub downloads occasionally arrive corrupted
        proc = subprocess.run(
            ["nix", "build", "--no-link", "--print-out-paths", f"{common.ROOT}#{name}"],
            capture_output=True, text=True,
        )
        if proc.returncode == 0:
            break
    else:
        return [f"nix build .#{name} failed:\n{proc.stderr[-3000:]}"]
    out = Path(proc.stdout.split()[-1])
    problems = []
    for binary in sorted((out / "bin").iterdir()):
        data = binary.read_bytes()
        if not data.startswith(b"\x7fELF"):
            continue  # makeWrapper script; its target is checked too
        unknown = {m.decode() for m in SONAME.findall(data)} - KNOWN_LIBS
        if unknown:
            problems.append(f"{binary.name} references unknown libraries: {', '.join(sorted(unknown))}")
        if binary.name.endswith("-cli"):
            run = subprocess.run([binary, "--version"], capture_output=True, text=True, timeout=60)
            if run.returncode != 0:
                problems.append(f"{binary.name} --version exited {run.returncode}: {run.stderr[-500:]}")
    return problems

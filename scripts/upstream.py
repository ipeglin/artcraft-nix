"""Discover upstream ArtCraft releases and their GitHub-published checksums."""

import re

import common

ASSET = re.compile(r"^(?P<bin>[a-z0-9]+(?:-[a-z0-9]+)*)-(?P<version>\d+\.\d+\.\d+)-linux-x86_64\.AppImage$")

def discover(repo):
    """Map version -> manifest entry for every stable x86_64 AppImage in repo.

    None when the repo is gone. Releases without a sha256 digest are skipped:
    the digest is what lets mirrors be trusted without trusting the mirror.
    """
    releases = common.get_pages(f"https://api.github.com/repos/{repo}/releases", common.github_headers())
    if releases is None:
        return None
    found = {}
    for rel in releases:
        if rel["draft"] or rel["prerelease"]:
            continue
        for asset in rel["assets"]:
            m = ASSET.match(asset["name"])
            digest = asset.get("digest") or ""
            if m and digest.startswith("sha256:"):
                found[m["version"]] = {
                    "tag": rel["tag_name"],
                    "file": asset["name"],
                    "bin": m["bin"],
                    "hash": common.to_sri(digest.removeprefix("sha256:")),
                }
    return found

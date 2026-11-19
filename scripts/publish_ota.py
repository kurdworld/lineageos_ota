#!/usr/bin/env python3
#
# SPDX-License-Identifier: Apache-2.0
#
"""Add a LineageOS OTA zip to the updater feed.

The script reads META-INF/com/android/metadata from the zip, so the feed entry
matches the build that was actually produced. Run it from anywhere; the default
feed is athena-4p19.json next to this repository's README.
"""

import argparse
import hashlib
import json
import os
import re
import sys
import zipfile

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_FEED = os.path.join(REPO_ROOT, "athena-4p19.json")
DEFAULT_REPO = "kurdworld/lineageos_ota"


def fail(message):
    print(f"error: {message}", file=sys.stderr)
    sys.exit(1)


def read_ota_metadata(zip_path):
    try:
        with zipfile.ZipFile(zip_path) as archive:
            raw = archive.read("META-INF/com/android/metadata")
    except KeyError:
        fail(f"{zip_path} has no META-INF/com/android/metadata")
    except zipfile.BadZipFile as exc:
        fail(f"{zip_path} is not a valid zip: {exc}")

    metadata = {}
    for line in raw.decode("utf-8", "replace").splitlines():
        line = line.strip()
        if not line or "=" not in line:
            continue
        key, value = line.split("=", 1)
        metadata[key.strip()] = value.strip()
    return metadata


def sha256sum(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_version(filename, explicit):
    if explicit:
        return explicit
    match = re.match(r"lineage-(\d+\.\d+)-", filename)
    if match:
        return match.group(1)
    fail("cannot determine the LineageOS version from the filename; pass --version")


def load_feed(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as stream:
        contents = stream.read().strip()
    if not contents:
        return []
    feed = json.loads(contents)
    if not isinstance(feed, list):
        fail(f"{path} is not a JSON array")
    return feed


def feed_filename(entry):
    files = entry.get("files")
    if not isinstance(files, list) or not files:
        return None
    return files[0].get("filename")


def main():
    parser = argparse.ArgumentParser(
        description="Add a LineageOS OTA zip to the updater feed.")
    parser.add_argument("zip", help="path to the OTA zip")
    parser.add_argument("--feed", default=DEFAULT_FEED,
                        help=f"feed file to update (default: {DEFAULT_FEED})")
    parser.add_argument("--device", default="athena",
                        help="device name expected in the OTA metadata")
    parser.add_argument("--type", dest="build_type", default="UNOFFICIAL",
                        help="value for ro.lineage.releasetype")
    parser.add_argument("--version",
                        help="LineageOS version (default: parsed from the filename)")
    parser.add_argument("--datetime", type=int,
                        help="build timestamp (default: post-timestamp from the zip)")
    parser.add_argument("--repo", default=DEFAULT_REPO,
                        help=f"GitHub repository holding the release (default: {DEFAULT_REPO})")
    parser.add_argument("--tag",
                        help="release tag; builds the asset URL from --repo and --tag")
    parser.add_argument("--url",
                        help="explicit asset download URL (overrides --tag)")
    parser.add_argument("--keep", type=int, default=10,
                        help="number of entries to keep in the feed (default: 10, 0 = all)")
    args = parser.parse_args()

    zip_path = os.path.abspath(args.zip)
    if not os.path.isfile(zip_path):
        fail(f"{zip_path} does not exist")

    filename = os.path.basename(zip_path)
    metadata = read_ota_metadata(zip_path)

    pre_device = metadata.get("pre-device", "")
    devices = [device.strip() for device in pre_device.split(",") if device.strip()]
    if devices and args.device not in devices:
        fail(f"OTA is for {pre_device}, not {args.device}")

    if args.url:
        url = args.url
    elif args.tag:
        url = f"https://github.com/{args.repo}/releases/download/{args.tag}/{filename}"
    else:
        fail("pass --url or --tag")

    timestamp = args.datetime
    if timestamp is None:
        raw_timestamp = metadata.get("post-timestamp", "")
        if raw_timestamp.isdigit():
            timestamp = int(raw_timestamp)
    if timestamp is None:
        timestamp = int(os.path.getmtime(zip_path))
        print(f"warning: no post-timestamp, using file mtime {timestamp}", file=sys.stderr)

    raw_sdk = metadata.get("post-sdk-level", "")
    if not raw_sdk.isdigit():
        fail("OTA metadata has no post-sdk-level; the Updater would discard the entry")
    sdk_level = int(raw_sdk)

    entry_file = {
        "filename": filename,
        "os_sdk_level": sdk_level,
        "sha256": sha256sum(zip_path),
        "size": os.path.getsize(zip_path),
        "url": url,
    }
    patch_level = metadata.get("post-security-patch-level")
    if patch_level:
        entry_file["os_patch_level"] = patch_level
    property_files = metadata.get("ota-property-files")
    if property_files:
        entry_file["ota_property_files"] = property_files

    entry = {
        "datetime": timestamp,
        "files": [entry_file],
        "type": args.build_type,
        "version": parse_version(filename, args.version),
    }

    feed_path = os.path.abspath(args.feed)
    feed = [item for item in load_feed(feed_path)
            if feed_filename(item) != filename]
    feed.insert(0, entry)
    if args.keep > 0:
        feed = feed[:args.keep]

    with open(feed_path, "w", encoding="utf-8") as stream:
        json.dump(feed, stream, indent=2)
        stream.write("\n")

    print(f"Updated {feed_path}")
    print(f"  {filename}")
    print(f"  version {entry['version']}, type {entry['type']}, datetime {timestamp}")
    print(f"  sha256 {entry_file['sha256']}")
    print(f"  url {url}")


if __name__ == "__main__":
    main()

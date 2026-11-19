# LineageOS OTA feed for BlackBerry KEY2 (athena)

This repository is the OTA update feed for the unofficial LineageOS 24.0
builds for the BlackBerry KEY2 (`athena`). The Updater app reads:

```
https://raw.githubusercontent.com/kurdworld/lineageos_ota/main/athena.json
```

`athena.json` uses the JSON format expected by the LineageOS Updater
(LineageOS 23.2 and newer). Each entry describes one OTA zip.

## Publishing a build

1. Create a GitHub release in this repository and upload the OTA zip:

   ```bash
   gh release create v24.0-20261120 \
       --repo kurdworld/lineageos_ota \
       --title "LineageOS 24.0 (2026-11-20)" \
       --notes "..." \
       lineage-24.0-20261120-UNOFFICIAL-athena.zip
   ```

   If the release already exists, upload the asset instead:

   ```bash
   gh release upload v24.0-20261120 \
       --repo kurdworld/lineageos_ota \
       lineage-24.0-20261120-UNOFFICIAL-athena.zip
   ```

2. Add the build to the feed:

   ```bash
   cd lineageos_ota
   ./scripts/publish_ota.py /path/to/lineage-24.0-20261120-UNOFFICIAL-athena.zip \
       --tag v24.0-20261120
   ```

   The script reads `META-INF/com/android/metadata` from the zip to fill in
   `post-timestamp`, `post-sdk-level`, `post-security-patch-level`, and
   `ota-property-files`. It computes the SHA-256 and the file size itself.

3. Commit and push the updated feed:

   ```bash
   git add athena.json
   git commit -m "Add 2026-11-20 build"
   git push
   ```

The Updater only offers builds whose `datetime` is newer than the installed
build, whose `os_sdk_level` is at least the device SDK, and whose `type`
matches `ro.lineage.releasetype` (`UNOFFICIAL` for these builds).

## Manual entry

If you prefer not to use the script, add an entry to the front of the JSON
array:

```json
{
  "datetime": 1795086306,
  "files": [
    {
      "filename": "lineage-24.0-20261119-UNOFFICIAL-athena.zip",
      "os_patch_level": "2026-11-01",
      "os_sdk_level": 37,
      "ota_property_files": "metadata:69:339,metadata.pb:476:228",
      "sha256": "<sha256>",
      "size": 1068582677,
      "url": "https://github.com/kurdworld/lineageos_ota/releases/download/v24.0-20261119/lineage-24.0-20261119-UNOFFICIAL-athena.zip"
    }
  ],
  "type": "UNOFFICIAL",
  "version": "24.0"
}
```

`os_sdk_level` is required in practice: the Updater drops entries with a
missing or lower SDK level.

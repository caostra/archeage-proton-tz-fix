# ArcheAge Chronicles — Steam Deck Proton TZ Fix

[한국어](README.md) · **English**

[Download the automatic patch tool v0.1.0](https://github.com/caostra/archeage-proton-tz-fix/raw/refs/heads/main/downloads/ArcheAge-Proton-TZFix-0.1.0.zip)

An **unofficial, experimental workaround** for this startup error in ArcheAge Chronicles:

> The procedure entry point SystemTimeToTzSpecificLocalTimeEx could not be located in the dynamic link library KERNEL32.dll.

The identical patched DLL reached the game's startup screen on Steam Deck in **Gaming Mode**. Server login, actual gameplay, long-term stability, and continued anti-cheat acceptance have **not** been verified.

## Read this first

- **Only one explicitly verified Proton Experimental build is supported.** Having a build named “Experimental” is not enough.
- If the version or DLL hashes do not match, stop. Do not edit the version label, hashes, or patch data to force installation. There is no force option.
- **Only Proton is copied, not the game.** Allow roughly 1.5–2 GiB or more for the separate tool. The installer checks available space against the source's actual size.
- The original Proton, game executables, and anti-cheat files are not patched. Anti-cheat is not disabled.
- This forwards the missing Ex APIs to existing non-Ex implementations. It is **not a complete implementation** of dynamic time-zone and year-specific daylight-saving behavior.
- Python 3.9+ and GNU `cp` are required. No administrator access, `sudo`, `pip`, LIEF, or additional Python packages are needed.

### Supported source build

The source Proton's `version` file must contain this exact value, and its DLLs must pass the hash checks:

```text
1793759737 experimental-bleeding-edge-11.0-464679-20261104-pa44208-w56e5a9-dcf0a0d-v15dd1e-x86_64
```

The installer does **not** download this build or downgrade Proton. Neither regular Experimental nor the latest bleeding-edge build is automatically compatible. Other builds require a new verified tool release.

## Installation

### 1. Extract the ZIP

Switch your Steam Deck to **Desktop Mode** and extract the ZIP linked above.

Open a terminal in the folder containing `archeage_proton_fix.py`. You can use the file manager's **Open Terminal Here** action. Keep `patch.json` in the same folder as the script.

### 2. Check compatibility without changing anything

```bash
python3 archeage_proton_fix.py check
```

Continue only if the tool reports that the source version and DLLs are compatible.

### 3. Install the separate patched Proton

```bash
python3 archeage_proton_fix.py install
```

Review the source, destination, and estimated copy size. Enter `y` to proceed.

The installer copies Proton into a temporary directory, backs up the original DLL in that copy, applies the patch, and verifies both the result and the untouched source. Only then does it register the separate Steam compatibility tool. It does not copy the game or the existing game prefix, and it does not overwrite an existing tool directory.

### 4. Select it in Steam — including Gaming Mode

Completely restart Steam, or reboot your Steam Deck. Then:

1. Open **Gaming Mode → ArcheAge Chronicles**.
2. Open **Gear icon → Properties → Compatibility**.
3. Enable **Force the use of a specific Steam Play compatibility tool**.
4. Select **Proton Experimental (ArcheAge TZ Fix 20261104)**.
5. Press **Play** on the existing Steam library entry.

No separate game entry or desktop shortcut is needed. Shader preparation may take a long time on the first launch.

The installer does not edit your Steam settings or close Steam automatically. Make the compatibility selection yourself. If account registration, terms, privacy consent, or age-confirmation screens appear, review and decide on them yourself.

## Check the installed tool

From the extracted package folder, run:

```bash
python3 archeage_proton_fix.py status
```

This verifies the installed DLLs and the backup hashes.

## Roll back or remove

To stop using the patch, close the game and select your previous Proton in **Properties → Compatibility**. The original startup error may return with the unpatched version.

To also remove the patched tool from disk, select another Proton, **fully exit Steam**, and run:

```bash
python3 archeage_proton_fix.py remove
```

Only the copy owned by this installer is removed. The original Proton, game, and saves are not deleted. Removal is refused if Steam is running, its configuration still references the tool, or the tool's verification fails.

## Non-default paths

The installer looks for `~/.local/share/Steam`, `~/.steam/steam`, and `~/.steam/root`. If necessary, supply the actual paths:

```bash
python3 archeage_proton_fix.py check --steam-root "/actual/Steam" --source "/actual/Proton - Experimental"
python3 archeage_proton_fix.py install --steam-root "/actual/Steam" --source "/actual/Proton - Experimental"
```

`--steam-root` is the Steam directory containing `steamapps`. A symlinked `compatibilitytools.d` directory is not supported. Flatpak layouts and other Linux distributions have not been separately tested.

## Troubleshooting

- **Unsupported version:** Stop. Do not force the patch onto another build.
- **Tool missing from Steam's list:** Completely restart Steam or reboot.
- **Already installed:** Run `status`; do not overwrite the folder manually.
- **Removal refused:** Select another compatibility tool, then close both the game and Steam.
- **A different error after the DLL problem:** This workaround does not fix every compatibility issue in the game.

When reporting problems, include your SteamOS version, the `check` result, the exact error, and the last screen reached. Do not post passwords or account details. Review logs for personal information before publishing them.

The separate copy does **not** automatically receive Steam's Proton updates.

## Package contents and validation

- `archeage_proton_fix.py`: install, verify, and remove logic
- `patch.json`: verified byte changes and hashes, not a complete DLL or Proton distribution
- `SHA256SUMS.txt`: per-file checksums
- [Validation record](TESTING.md) · [Sources and licensing scope](NOTICE.md) · [Code license](LICENSE.txt)

No personal logs, IP addresses, account details, SSH keys, or game files are included. Checksums are not digital signatures or proof of publisher identity; obtain the tool from a source you trust.

This project is not provided or endorsed by Valve, Wine, or the game's developer or publisher.

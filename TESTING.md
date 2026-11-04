# Validation record — 0.1.0

Date: 2026-11-04.

## DLL output

The installer deterministically reproduced the exact already-tested 64-bit DLL:

- Original kernel32 SHA-256: `0bee33aefb13e419d5e5eef0f6f1f76a6601a5143fe84b2862feca4eb37eca78`
- Patched kernel32 SHA-256: `feb9138985fd27ac0f36ce5917a36d90c9f5a17dc859d9f880672d22067d32ab`
- Required kernelbase SHA-256: `5b2fca30737212c69fd6e11a46c635f0ed63957f8281c165b70cfa53437c1eaa`

Independent PE parsing verified preservation of all 1,363 existing named exports (ordinals and targets), preservation of every original section's bytes, exactly two new named exports, and a correct PE checksum with no parser warnings. The corresponding actual DLL had also been checked with objdump on SteamOS. These development checks used pefile; end users do not need it.

The new delta function rejected a truncated source, a one-byte-modified source, and an already-patched source.

## Installer tests on SteamOS

Read-only preflight against the installed full Proton source passed.

Installation/removal logic was tested in a small synthetic Proton directory containing the actual verified DLLs and minimal required metadata. This did not copy another complete game or modify the real Steam configuration. Checks passed:

- Installation, status verification, source preservation and separate file inodes.
- Internal absolute symlinks rebased to the new copy, remaining valid after final rename.
- Duplicate installation rejected without overwriting.
- Modified installed DLL detected.
- Removal blocked while Steam is running.
- Removal blocked while the Steam config references the tool.
- Owned-folder removal with Steam-exit state simulated; source remained intact.
- Destination/removal symlinks refused.
- Unsupported source version refused before copying.
- Modified patch manifest refused.

The temporary fixture was removed. The removal success test simulated Steam having exited so the active user's Steam session was not interrupted. A full-size installation by this new release wrapper and its user-interface selection on another person's system have not been tested.

## Game execution boundary

The identical patched DLL in a full separate Proton installation was tested on Steam Deck SteamOS 3.9.5 with game build 26404487:

- Desktop mode: startup and initial terms/registration screen reached.
- Gaming Mode using the existing Steam game installation: startup screen reached.
- The observed Gaming Mode log had zero NtRaiseHardError and zero unimplemented-function reports.
- The running game loaded kernel32.dll from the separate patched Proton.

No account terms were accepted by the tool. Server login, character control, extended gameplay, and ongoing anti-cheat acceptance remain unverified. This is not a general Proton compatibility certification.

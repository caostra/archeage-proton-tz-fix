# Sources and scope

This package is an independent, unofficial installer. It is not provided or endorsed by Valve, Wine, XLGAMES, or the game publisher.

The method adds these 64-bit kernel32 exports, forwarding to the existing non-Ex implementations:

```
SystemTimeToTzSpecificLocalTimeEx -> kernelbase.SystemTimeToTzSpecificLocalTime
TzSpecificLocalTimeToSystemTimeEx -> kernelbase.TzSpecificLocalTimeToSystemTime
```

The original Ex exports in kernelbase were unimplemented stubs in the tested build. Forwarding to those same Ex names is NOT this patch.

References consulted:

- Valve Proton compatibility report: https://github.com/ValveSoftware/Proton/issues/10337
- Community description, comment #14, including a quoted workaround: https://steamcommunity.com/app/3218230/discussions/0/571553842245728118/
- Proton local tool installation: https://github.com/ValveSoftware/Proton#install-proton-locally
- Valve Wine source: https://github.com/ValveSoftware/wine
- Microsoft API semantics: https://learn.microsoft.com/en-us/windows/win32/api/timezoneapi/nf-timezoneapi-systemtimetotzspecificlocaltimeex

The installer reproduces a locally tested DLL byte-for-byte. It does not execute a downloaded patch script, fetch third-party binaries, use LIEF, or download a Proton version. Its patch data contains binary header/export-table changes, not a complete Proton or DLL distribution.

LICENSE.txt covers the original Python installer code and documentation only. Underlying Proton/Wine components and any derived patch data retain applicable upstream terms; this file does not relicense them. The installation copy retains upstream license notices. Anyone redistributing a full patched Proton must separately address its upstream licensing and source-distribution requirements.

The copied tool does not automatically receive Steam's Proton updates. A future supported release requires fresh source/hash verification, export checks, and execution testing. Do not broaden the allowlist based solely on a filename or version label.

#!/usr/bin/env python3
"""Version-pinned, offline Proton copy installer. Python standard library only."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zlib

TOOL = "Proton-ArcheAge-TZFix-20261104"
DISPLAY = "Proton Experimental (ArcheAge TZ Fix 20261104)"
OWNER = "archeage-tz-fix/0.1.0"
MANIFEST_SHA = "8101a073e8e780ae1721402617446bf63f83597498fbf988bfc32b3448eabf21"
K32 = Path("files/lib/wine/x86_64-windows/kernel32.dll")
KBASE = K32.with_name("kernelbase.dll")
DEFAULT = Path("files/share/default_pfx/drive_c/windows/system32/kernel32.dll")
MARKER = ".archeage-tz-fix.json"


class Refuse(RuntimeError):
    pass


def require(condition, message):
    if not condition:
        raise Refuse(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def manifest():
    raw = Path(__file__).with_name("patch.json").read_bytes()
    require(sha(raw) == MANIFEST_SHA, "patch.json integrity check failed. / 패치 파일 검증 실패")
    return json.loads(raw)


def patched_bytes(original, m):
    require(len(original) == m["source_size"] and sha(original) == m["source_sha256"],
            "Unsupported or modified DLL. No changes made. / 지원하지 않는 DLL입니다.")
    out = bytearray(original)
    last = 0
    for item in m["replacements"]:
        pos = item["offset"]
        before, after = bytes.fromhex(item["before"]), bytes.fromhex(item["after"])
        require(last <= pos and len(before) == len(after) and pos + len(before) <= len(out),
                "Invalid replacement range")
        require(bytes(out[pos:pos + len(before)]) == before, "Replacement bytes mismatch")
        out[pos:pos + len(after)] = after
        last = pos + len(before)
    out.extend(zlib.decompress(base64.b64decode(m["append_zlib_base64"], validate=True)))
    require(len(out) == m["output_size"] and sha(out) == m["output_sha256"],
            "Patched DLL verification failed")
    return bytes(out)


def steam_root(explicit=None):
    candidates = [Path(explicit).expanduser()] if explicit else [
        Path.home() / ".local/share/Steam", Path.home() / ".steam/steam",
        Path.home() / ".steam/root",
    ]
    for p in candidates:
        if (p / "steamapps").is_dir():
            return p.resolve()
    raise Refuse("Steam not found. Supply --steam-root /path/to/Steam. / Steam 경로를 지정하세요.")


def tool_path(root):
    parent = root / "compatibilitytools.d"
    require(not parent.is_symlink(), "compatibilitytools.d must be a real directory, not a symlink")
    require(not parent.exists() or parent.is_dir(), "compatibilitytools.d is not a directory")
    return parent / TOOL


def local_file(root, relative):
    p = root / relative
    require(p.is_file() and p.resolve().is_relative_to(root.resolve()),
            "File missing or linked outside its Proton copy: " + str(relative))
    return p


def check_source(source, m):
    require(source.is_dir(), "Proton source directory not found: " + str(source))
    for name in ["proton", "version", "toolmanifest.vdf"]:
        local_file(source, Path(name))
    require((source / "version").read_text().strip() == m["source_version"],
            "Unsupported Proton version. This tool intentionally refuses newer/different builds.\n"
            "검증한 빌드와 다릅니다. 업데이트된 Proton에 강제로 적용하지 않습니다.\n"
            "Required / 지원 버전: " + m["source_version"])
    original = local_file(source, K32).read_bytes()
    require(sha(local_file(source, KBASE).read_bytes()) == m["kernelbase_sha256"],
            "Unsupported kernelbase.dll")
    require(sha(local_file(source, DEFAULT).read_bytes()) == m["source_sha256"],
            "Default prefix kernel32.dll does not match")
    patched_bytes(original, m)
    return original


def tree_size(root):
    # Conservative: counts internal hardlinks twice; skips symlink targets.
    return sum(p.stat().st_size for p in root.rglob("*") if p.is_file() and not p.is_symlink())


def confirm(text, yes):
    if yes:
        return
    require(sys.stdin.isatty(), "Use --yes for non-interactive operation")
    require(input(text + " [y/N] ").strip().lower() == "y", "Cancelled / 취소했습니다.")


def rebase_internal_links(stage, source):
    # Never leave new absolute symlinks pointing back to source Proton.
    for p in stage.rglob("*"):
        if p.is_symlink():
            raw = Path(os.readlink(p))
            if raw.is_absolute() and raw.is_relative_to(source):
                new = stage / raw.relative_to(source)
                p.unlink()
                p.symlink_to(os.path.relpath(new, p.parent))


def install(root, source, m, yes=False):
    target = tool_path(root)
    require(not target.exists() and not target.is_symlink(),
            "Destination already exists. Use status; it will not be overwritten. / 기존 폴더는 덮어쓰지 않습니다.")
    require(not source.is_relative_to(target) and not target.is_relative_to(source),
            "Source and destination must be separate")
    original = check_source(source, m)
    size = tree_size(source)
    require(shutil.disk_usage(root).free > size + 256 * 1024 * 1024, "Not enough free space")
    require(shutil.which("cp") is not None, "GNU cp is required")
    print("Source / 원본:", source)
    print("Destination / 별도 복사본:", target)
    print("Copy estimate / 복사 용량: %.2f GiB (Proton ONLY; no game copy)" % (size / 1024**3))
    confirm("Create and patch this separate Proton copy? / 위 Proton 복사본을 만들까요?", yes)
    target.parent.mkdir(exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix="." + TOOL + "-", dir=target.parent))
    try:
        subprocess.run(["cp", "-a", "--reflink=auto", "--", str(source) + "/.", str(stage)], check=True)
        rebase_internal_links(stage, source)
        require(check_source(stage, m) == original, "Source changed during copying")
        require(not os.path.samefile(source / K32, stage / K32), "Copy is hardlinked to original")
        backup = stage / ".archeage-fix-backup"
        require(not backup.exists(), "Unexpected existing backup directory")
        backup.mkdir()
        (backup / "kernel32.dll").write_bytes(original)
        output = patched_bytes(original, m)
        for relative in [K32, DEFAULT]:
            p = local_file(stage, relative)
            mode = p.stat().st_mode & 0o777
            p.chmod(mode | 0o200)
            p.write_bytes(output)
            p.chmod(mode)
            require(sha(p.read_bytes()) == m["output_sha256"], "Installed DLL mismatch")
        vdf = stage / "compatibilitytool.vdf"
        require(not vdf.is_symlink(), "Unexpected manifest symlink")
        if vdf.exists():
            shutil.copy2(vdf, backup / "compatibilitytool.vdf")
            vdf.chmod(vdf.stat().st_mode | 0o200)
        vdf.write_text('"compatibilitytools"\n{\n "compat_tools"\n {\n  "' + TOOL +
                       '"\n  {\n   "install_path" "."\n   "display_name" "' + DISPLAY +
                       '"\n   "from_oslist" "windows"\n   "to_oslist" "linux"\n  }\n }\n}\n', encoding="utf-8")
        require(not (stage / MARKER).exists() and not (stage / MARKER).is_symlink(),
                "Unexpected existing ownership marker")
        (stage / MARKER).write_text(json.dumps({"owner": OWNER, "tool": TOOL,
            "source_version": m["source_version"], "original_sha256": m["source_sha256"],
            "patched_sha256": m["output_sha256"]}, indent=2) + "\n", encoding="utf-8")
        require(check_source(source, m) == original, "Original changed during installation")
        require(not target.exists() and not target.is_symlink(), "Destination appeared during install")
        stage.rename(target)
        print("Installed and verified / 설치 및 검증 완료:", DISPLAY)
        print("Restart Steam. Game Properties > Compatibility > select this tool.\n"
              "Steam을 완전히 재시작한 뒤, 게임 속성 → 호환성에서 위 도구를 선택하세요.\n"
              "Gaming Mode uses the same setting. / 게임 모드에도 같은 설정이 적용됩니다.")
    finally:
        if stage.exists():
            require(stage.parent.resolve() == target.parent.resolve() and not stage.is_symlink(),
                    "Unsafe temporary cleanup path")
            shutil.rmtree(stage)


def status(root, m):
    target = tool_path(root)
    require(target.is_dir() and not target.is_symlink(), "Tool is not installed / 설치되어 있지 않습니다.")
    info = json.loads(local_file(target, Path(MARKER)).read_text())
    require(info.get("owner") == OWNER and info.get("tool") == TOOL, "Tool ownership marker mismatch")
    for relative in [K32, DEFAULT]:
        require(sha(local_file(target, relative).read_bytes()) == m["output_sha256"],
                "Patched DLL has changed / 패치 DLL이 변경되었습니다.")
    require(sha(local_file(target, KBASE).read_bytes()) == m["kernelbase_sha256"], "kernelbase.dll changed")
    require(sha(local_file(target, Path(".archeage-fix-backup/kernel32.dll")).read_bytes()) == m["source_sha256"],
            "Backup hash mismatch")
    print("Verified / 검증 완료:", target)
    return target


def steam_running():
    for p in Path("/proc").glob("[0-9]*"):
        try:
            if (p / "comm").read_text().strip() == "steam":
                return True
        except (OSError, UnicodeError):
            pass
    return False


def remove(root, m, yes=False):
    target = status(root, m)
    require(not steam_running(), "Select another Proton in Steam, then fully exit Steam before removal.\n"
            "다른 Proton을 선택하고 Steam을 완전히 종료한 뒤 제거하세요.")
    config = root / "config/config.vdf"
    require(not config.exists() or TOOL not in config.read_text(errors="replace"),
            "Steam still references this tool. Change the game's compatibility selection first.")
    for p in Path("/proc").glob("[0-9]*"):
        try:
            maps = (p / "maps").read_text()
        except (OSError, UnicodeError):
            continue
        require(str(target) not in maps, "This tool still has running processes; close the game first")
    require(target.resolve() == root / "compatibilitytools.d" / TOOL, "Unsafe removal path")
    confirm("Remove ONLY this tool folder? / 이 패치 Proton 폴더만 제거할까요? " + str(target), yes)
    shutil.rmtree(target)
    print("Removed / 제거 완료. Original Proton and games were not removed.")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", nargs="?", default="check", choices=["check", "install", "status", "remove"])
    parser.add_argument("--steam-root", help="Steam directory containing steamapps")
    parser.add_argument("--source", help="Proton source directory (default: Proton - Experimental)")
    parser.add_argument("--yes", action="store_true", help="Skip this tool's copy/removal prompt")
    args = parser.parse_args(argv)
    try:
        require(sys.platform.startswith("linux"), "Run on SteamOS/Linux, not Windows")
        require(os.geteuid() != 0, "Do not run as root or with sudo / sudo로 실행하지 마세요.")
        m = manifest()
        root = steam_root(args.steam_root)
        source = (Path(args.source).expanduser() if args.source else root / "steamapps/common/Proton - Experimental").resolve()
        if args.command == "check":
            check_source(source, m)
            print("Compatible / 지원하는 버전과 DLL입니다. No changes made / 변경 없음.")
        elif args.command == "install":
            install(root, source, m, args.yes)
        elif args.command == "status":
            status(root, m)
        else:
            remove(root, m, args.yes)
        return 0
    except (Refuse, OSError, ValueError, subprocess.SubprocessError, zlib.error) as exc:
        print("STOP / 중단:", exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

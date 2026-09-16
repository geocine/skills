import argparse
import datetime
import os
import re
import shutil
import struct
import subprocess
import sys
from pathlib import Path

DEFAULT_SYMBOL_PATH = r"srv*C:\Symbols*https://msdl.microsoft.com/download/symbols"
DEFAULT_MINIDUMP_DIR = r"C:\Windows\Minidump"

DUMP_TYPE_NAMES = {
    1: "FULL",
    2: "SUMMARY",
    3: "HEADER",
    4: "TRIAGE",
    5: "BITMAP_FULL",
    6: "BITMAP_KERNEL",
    7: "AUTOMATIC",
}

PRODUCT_TYPE_NAMES = {
    1: "WORKSTATION",
    2: "DOMAIN_CONTROLLER",
    3: "SERVER",
}


def to_ascii(text):
    return text.encode("ascii", errors="replace").decode("ascii")


def find_latest_dump(dir_path):
    if not dir_path:
        return None
    path = Path(dir_path)
    if not path.exists():
        return None
    dumps = list(path.glob("*.dmp"))
    if not dumps:
        return None
    return max(dumps, key=lambda p: p.stat().st_mtime)


def resolve_dump_path(path_str):
    if not path_str:
        return find_latest_dump(DEFAULT_MINIDUMP_DIR)
    path = Path(path_str)
    if path.is_dir():
        return find_latest_dump(path)
    return path


def find_cdb(user_path=None):
    candidates = []
    if user_path:
        candidates.append(Path(user_path))
    env_path = os.environ.get("CDB_PATH")
    if env_path:
        candidates.append(Path(env_path))
    which = shutil.which("cdb")
    if which:
        candidates.append(Path(which))

    default_paths = [
        Path(r"C:\Program Files (x86)\Windows Kits\10\Debuggers\x64\cdb.exe"),
        Path(r"C:\Program Files (x86)\Windows Kits\10\Debuggers\x86\cdb.exe"),
    ]
    candidates.extend(default_paths)

    for c in candidates:
        if c and c.exists():
            return c
    return None


def run_cdb(cdb_path, dump_path, symbol_path):
    cmd = [
        str(cdb_path),
        "-z",
        str(dump_path),
        "-y",
        symbol_path,
        "-c",
        "!analyze -v; q",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
    output = result.stdout
    if result.stderr:
        output += "\n" + result.stderr
    return output, result.returncode


def first_match(output, patterns):
    for pattern in patterns:
        m = re.search(pattern, output, re.MULTILINE)
        if m:
            return m.group(1).strip()
    return None


def parse_cdb_output(output):
    data = {}
    data["bugcheck_line"] = first_match(output, [r"^BugCheck\s+([0-9A-Fa-fx]+),\s*\{([^}]*)\}"]) 

    bugcheck_name = first_match(output, [r"^([A-Z0-9_]+)\s+\((0x[0-9A-Fa-f]+|[0-9A-Fa-f]+)\)"])
    if bugcheck_name:
        data["bugcheck_name"] = bugcheck_name.split()[0]

    data["bugcheck_str"] = first_match(output, [r"^BUGCHECK_STR:\s*(.+)$"])
    data["bugcheck_p1"] = first_match(output, [r"^BUGCHECK_P1:\s*(.+)$"])
    data["bugcheck_p2"] = first_match(output, [r"^BUGCHECK_P2:\s*(.+)$"])
    data["bugcheck_p3"] = first_match(output, [r"^BUGCHECK_P3:\s*(.+)$"])
    data["bugcheck_p4"] = first_match(output, [r"^BUGCHECK_P4:\s*(.+)$"])
    data["probably_caused_by"] = first_match(output, [r"^Probably caused by\s*:\s*(.+)$"])
    data["image_name"] = first_match(output, [r"^IMAGE_NAME:\s*(.+)$"])
    data["module_name"] = first_match(output, [r"^MODULE_NAME:\s*(.+)$"])
    data["process_name"] = first_match(output, [r"^PROCESS_NAME:\s*(.+)$"])
    data["failure_bucket_id"] = first_match(output, [r"^FAILURE_BUCKET_ID:\s*(.+)$"])
    data["build_version"] = first_match(output, [r"^BUILD_VERSION_STRING:\s*(.+)$", r"^BUILDOSVER_STR:\s*(.+)$"])
    data["os_build"] = first_match(output, [r"^OSBUILD:\s*(.+)$"])
    data["debug_session_time"] = first_match(output, [r"^Debug session time:\s*(.+)$", r"^ANALYSIS_SESSION_TIME:\s*(.+)$"])
    data["system_uptime"] = first_match(output, [r"^System Uptime:\s*(.+)$"])

    stack_block = None
    m = re.search(r"STACK_TEXT:\s*(.*?)(?:\n\n|\Z)", output, re.DOTALL)
    if m:
        stack_block = m.group(1)
    if stack_block:
        lines = [line.rstrip() for line in stack_block.splitlines() if line.strip()]
        data["stack_text"] = lines[:12]

    return data


def parse_dump_header(path):
    with open(path, "rb") as f:
        data = f.read(0x2000)

    if len(data) < 32:
        return {"error": "File too small"}

    sig = data[0:4]
    if sig == b"PAGE":
        return parse_dump_header64(data)
    if sig == b"MDMP":
        return parse_minidump_header(data)

    return {"error": f"Unknown signature {sig!r}"}


def parse_dump_header64(data):
    def u32(off):
        return struct.unpack_from("<I", data, off)[0]

    def u64(off):
        return struct.unpack_from("<Q", data, off)[0]

    header = {}
    header["signature"] = data[0:4].decode("ascii", errors="replace")
    header["valid_dump"] = data[4:8].decode("ascii", errors="replace")
    header["major"] = u32(0x8)
    header["minor"] = u32(0xC)
    header["machine_image_type"] = u32(0x30)
    header["number_processors"] = u32(0x34)
    header["bugcheck_code"] = u32(0x38)
    header["bugcheck_params"] = [u64(0x40), u64(0x48), u64(0x50), u64(0x58)]
    header["dump_type"] = u32(0xF90)
    header["dump_type_name"] = DUMP_TYPE_NAMES.get(header["dump_type"], "UNKNOWN")
    header["required_dump_space"] = u64(0xF98)

    system_time = u64(0xFA0)
    if system_time:
        epoch = datetime.datetime(1601, 1, 1, tzinfo=datetime.timezone.utc)
        header["system_time"] = epoch + datetime.timedelta(microseconds=system_time / 10)

    uptime = u64(0x1028)
    if uptime:
        header["system_uptime_seconds"] = uptime / 10_000_000

    header["product_type"] = u32(0x1040)
    header["product_type_name"] = PRODUCT_TYPE_NAMES.get(header["product_type"], "UNKNOWN")
    header["suite_mask"] = u32(0x1044)
    header["attributes"] = u32(0x1048)
    header["boot_id"] = u32(0x104C)

    return header


def parse_minidump_header(data):
    header = {}
    sig, ver, num_streams, dir_rva, checksum, timestamp, flags = struct.unpack_from("<IIIIIIQ", data, 0)
    header["signature"] = "MDMP"
    header["version"] = ver
    header["streams"] = num_streams
    header["flags"] = flags

    if timestamp:
        header["timestamp"] = datetime.datetime.utcfromtimestamp(timestamp).replace(tzinfo=datetime.timezone.utc)

    streams = []
    for i in range(num_streams):
        off = dir_rva + i * 12
        if off + 12 > len(data):
            break
        stype, size, rva = struct.unpack_from("<III", data, off)
        streams.append((stype, size, rva))

    for stype, size, rva in streams:
        if stype == 0x0C and rva + size <= len(data):
            buf = data[rva : rva + size]
            if size >= 40:
                vals = struct.unpack_from("<Q Q Q Q Q", buf, 0)
                header["bugcheck_code"] = vals[0]
                header["bugcheck_params"] = list(vals[1:])
            elif size >= 20:
                vals = struct.unpack_from("<I I I I I", buf, 0)
                header["bugcheck_code"] = vals[0]
                header["bugcheck_params"] = list(vals[1:])

        if stype == 7 and rva + size <= len(data):
            base = data[rva : rva + size]
            if len(base) >= 56:
                proc_arch, proc_level, proc_rev, num_procs, product_type, major, minor, build, platform_id, csd_rva, suite_mask, reserved2 = struct.unpack_from(
                    "<HHHBBIII I I HH", base, 0
                )
                header["os_version"] = f"{major}.{minor}.{build}"
                header["product_type"] = product_type
                header["suite_mask"] = suite_mask

    return header


def render_report(dump_path, cdb_data, header_data, raw_output, include_raw):
    lines = []
    lines.append(f"# Minidump Analysis: {dump_path.name}")
    lines.append("")
    lines.append("## Summary")

    if cdb_data:
        source = "CDB"
    else:
        source = "Header parsing"
    lines.append(f"- Source: {source}")

    bugcheck = None
    params = None

    if cdb_data:
        if cdb_data.get("bugcheck_line"):
            parts = cdb_data["bugcheck_line"].split(",", 1)
            if parts:
                bugcheck = parts[0].strip()
            if len(parts) > 1:
                params = parts[1].strip()
        if not bugcheck and cdb_data.get("bugcheck_str"):
            bugcheck = cdb_data["bugcheck_str"]

    if not bugcheck and header_data:
        code = header_data.get("bugcheck_code")
        if code is not None:
            bugcheck = f"0x{int(code):x}"
            if header_data.get("bugcheck_params"):
                params = "{" + ", ".join(f"0x{int(p):x}" for p in header_data["bugcheck_params"]) + "}"

    if bugcheck:
        lines.append(f"- Bugcheck: {bugcheck}")
    if params:
        lines.append(f"- Parameters: {params}")

    if cdb_data:
        if cdb_data.get("probably_caused_by"):
            lines.append(f"- Likely cause: {cdb_data['probably_caused_by']}")
        if cdb_data.get("image_name"):
            lines.append(f"- Image: {cdb_data['image_name']}")
        if cdb_data.get("module_name"):
            lines.append(f"- Module: {cdb_data['module_name']}")

    if header_data:
        if header_data.get("system_time"):
            lines.append(f"- System time: {header_data['system_time']}")
        if header_data.get("system_uptime_seconds"):
            uptime = header_data["system_uptime_seconds"]
            lines.append(f"- System uptime (s): {uptime:.3f}")
        if header_data.get("dump_type_name"):
            lines.append(f"- Dump type: {header_data['dump_type_name']}")

    if cdb_data and cdb_data.get("debug_session_time"):
        lines.append(f"- Debug session time: {cdb_data['debug_session_time']}")
    if cdb_data and cdb_data.get("system_uptime"):
        lines.append(f"- CDB uptime: {cdb_data['system_uptime']}")

    lines.append("")
    lines.append("## Details")
    lines.append(f"- Dump file: {dump_path}")

    if cdb_data and cdb_data.get("build_version"):
        lines.append(f"- Build version: {cdb_data['build_version']}")
    if cdb_data and cdb_data.get("os_build"):
        lines.append(f"- OS build: {cdb_data['os_build']}")
    if cdb_data and cdb_data.get("process_name"):
        lines.append(f"- Process: {cdb_data['process_name']}")
    if cdb_data and cdb_data.get("failure_bucket_id"):
        lines.append(f"- Failure bucket: {cdb_data['failure_bucket_id']}")

    if cdb_data and cdb_data.get("stack_text"):
        lines.append("")
        lines.append("## Stack Trace (trimmed)")
        lines.append("```")
        lines.extend(cdb_data["stack_text"])
        lines.append("```")

    if include_raw and raw_output:
        lines.append("")
        lines.append("## Raw CDB Output")
        lines.append("```")
        lines.append(raw_output)
        lines.append("```")

    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description="Analyze a Windows minidump and write a markdown report.")
    parser.add_argument("dump", nargs="?", help="Path to .dmp or a directory containing dumps")
    parser.add_argument("--out", help="Output markdown path (defaults next to dump)")
    parser.add_argument("--symbol-path", default=DEFAULT_SYMBOL_PATH, help="Symbol path for CDB")
    parser.add_argument("--cdb", help="Path to cdb.exe")
    parser.add_argument("--include-raw", action="store_true", help="Include raw CDB output in report")
    parser.add_argument("--no-cdb", action="store_true", help="Skip CDB and only parse dump headers")

    args = parser.parse_args()

    dump_path = resolve_dump_path(args.dump)
    if not dump_path or not dump_path.exists():
        print("Dump file not found.", file=sys.stderr)
        return 1

    out_path = Path(args.out) if args.out else dump_path.with_suffix(".md")

    cdb_data = None
    raw_output = None

    if not args.no_cdb:
        cdb_path = find_cdb(args.cdb)
        if cdb_path:
            raw_output, code = run_cdb(cdb_path, dump_path, args.symbol_path)
            raw_output = to_ascii(raw_output)
            cdb_data = parse_cdb_output(raw_output)
        else:
            print("cdb.exe not found; falling back to header parsing.", file=sys.stderr)

    header_data = parse_dump_header(dump_path)

    report = render_report(dump_path, cdb_data, header_data, raw_output, args.include_raw)
    report = to_ascii(report)
    with open(out_path, "w", encoding="ascii", errors="replace") as f:
        f.write(report)

    print(f"Wrote report: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

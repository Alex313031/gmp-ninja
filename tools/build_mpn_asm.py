#!/usr/bin/env python3
"""All-in-one driver for the gmp-ninja asm pipeline.

This is the GN action entrypoint -- it composes the three stand-alone
scripts (gen_config_m4.py, select_mpn_asm.py, build_mpn_asm_archive.py)
into a single command:

  1. Generate config.m4 for the active (cpu, os).
  2. Resolve the (function, asm_path, operation) tuple list for the
     active CPU tune.
  3. Run m4 + as on each tuple in parallel; bundle the .o files into a
     static archive (libgmp_asm.a).

Outputs the archive at --out-archive.  Intermediate artifacts (config.m4,
the JSON pair list) live next to the archive for debugging.
"""
import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def run(cmd: list[str]):
    print("+ " + " ".join(cmd), file=sys.stderr)
    r = subprocess.run(cmd)
    if r.returncode != 0:
        sys.exit(f"command failed (exit {r.returncode}): {cmd[0]}")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--cpu", required=True, choices=("x86", "x64"))
    p.add_argument("--os", dest="os_", required=True,
                   choices=("linux", "win"))
    p.add_argument("--tune", required=True,
                   help="One of the tunes printed by select_mpn_asm.py "
                        "--list-tunes (e.g. generic, haswell, zen, "
                        "skylake).")
    p.add_argument("--top-srcdir", required=True,
                   help="Path to gmp/ srcdir.")
    p.add_argument("--out-archive", required=True,
                   help="Output libgmp_asm.a path.")
    p.add_argument("--m4", default="m4")
    p.add_argument("--as", dest="as_bin", required=True)
    p.add_argument("--ar", required=True)
    p.add_argument("--asflags", default="")
    p.add_argument("--jobs", type=int,
                   default=int(os.environ.get("MAKEFLAGS_JOBS", "0"))
                           or (os.cpu_count() or 4))
    args = p.parse_args()

    out_archive = os.path.abspath(args.out_archive)
    out_dir = os.path.dirname(out_archive)
    os.makedirs(out_dir, exist_ok=True)

    config_m4 = os.path.join(out_dir, "config.m4")
    asm_json = os.path.join(out_dir, "mpn_asm.json")

    # 1. Generate config.m4.
    run([
        sys.executable, os.path.join(HERE, "gen_config_m4.py"),
        "--cpu", args.cpu,
        "--os", args.os_,
        "--top-srcdir", args.top_srcdir,
        "--out", config_m4,
    ])

    # 2. Resolve asm pairs to JSON.
    with open(asm_json, "w") as f:
        r = subprocess.run([
            sys.executable, os.path.join(HERE, "select_mpn_asm.py"),
            "--gmp-srcdir", args.top_srcdir,
            "--cpu", args.cpu,
            "--tune", args.tune,
        ], stdout=f)
    if r.returncode != 0:
        sys.exit(f"select_mpn_asm.py failed (exit {r.returncode})")

    # 3. Build the archive.
    run([
        sys.executable, os.path.join(HERE, "build_mpn_asm_archive.py"),
        "--asm-json", asm_json,
        "--config-m4", config_m4,
        "--top-srcdir", args.top_srcdir,
        "--out-archive", out_archive,
        "--m4", args.m4,
        "--as", args.as_bin,
        "--ar", args.ar,
        "--asflags", args.asflags,
        "--jobs", str(args.jobs),
    ])


if __name__ == "__main__":
    main()

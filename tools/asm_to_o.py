#!/usr/bin/env python3
"""Compile a single GMP .asm file to a .o, the way upstream Makeasm.am does.

Steps:

  1. Run m4 from the asm file's directory (so its `include('../config.m4')`
     resolves to <stage>/mpn/config.m4) to produce a .s file.
  2. Run the assembler ($AS) on the .s to produce a .o file.

The "from the asm file's directory" requirement is awkward to satisfy
without polluting the gmp/ tree, so this script materialises a per-call
staging dir under the build's output: it symlinks the asm file in place
and writes config.m4 alongside.  No file in gmp/ is touched.

Used as a GN action_foreach script.
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--asm", required=True,
                   help="Path to the input .asm file (under gmp/mpn/...).")
    p.add_argument("--config-m4", required=True,
                   help="Path to the generated config.m4.")
    p.add_argument("--top-srcdir", required=True,
                   help="Path to gmp/ srcdir (must contain mpn/asm-defs.m4).")
    p.add_argument("--operation", required=True,
                   help="OPERATION_<name> macro for the multi-function asm.")
    p.add_argument("--out-o", required=True, help="Output .o path.")
    p.add_argument("--out-s", default=None,
                   help="Optional .s output path (kept for debugging).")
    p.add_argument("--m4", default="m4", help="Path to m4 binary.")
    p.add_argument("--as", dest="as_tool", required=True,
                   help="Path to the assembler binary (e.g. "
                        "x86_64-w64-mingw32-as).")
    p.add_argument("--asflags", default="",
                   help="Extra flags for the assembler, space-separated.")
    args = p.parse_args()

    asm = os.path.abspath(args.asm)
    if not os.path.isfile(asm):
        sys.exit(f"--asm not found: {asm}")
    config_m4 = os.path.abspath(args.config_m4)
    if not os.path.isfile(config_m4):
        sys.exit(f"--config-m4 not found: {config_m4}")
    top_srcdir = os.path.abspath(args.top_srcdir)
    if not os.path.isdir(os.path.join(top_srcdir, "mpn")):
        sys.exit(f"--top-srcdir does not contain mpn/: {top_srcdir}")
    out_o = os.path.abspath(args.out_o)
    os.makedirs(os.path.dirname(out_o), exist_ok=True)
    out_s = os.path.abspath(args.out_s) if args.out_s else (out_o + ".s")
    os.makedirs(os.path.dirname(out_s), exist_ok=True)

    # GMP's .asm files all do `include('../config.m4')`, which m4 resolves
    # relative to *m4's current working directory*, not the asm file's
    # location.  Upstream's autoconf build sidesteps depth by always running
    # m4 from `gmp/mpn/`, with the asm file given as a relative path
    # (`x86_64/coreihwl/aors_n.asm` etc.); `../config.m4` then unambiguously
    # points at `gmp/config.m4` regardless of how nested the asm file is.
    #
    # We mirror that here:
    #
    #   <stage>/config.m4              <- our generated config.m4
    #   <stage>/mpn/                   <- m4's cwd (via -I-equivalent)
    #   <stage>/mpn/<sub>/<asm>        <- symlink to the real asm

    # Determine the asm file's location relative to the gmp/ srcdir:
    # e.g. mpn/x86_64/aors_n.asm -> asm_path_under_mpn = "x86_64/aors_n.asm"
    asm_rel = os.path.relpath(asm, top_srcdir)
    if not asm_rel.startswith("mpn" + os.sep):
        sys.exit(f"--asm must live under {top_srcdir}/mpn/ (got {asm})")
    asm_path_under_mpn = asm_rel[len("mpn" + os.sep):]  # e.g. "x86_64/aors_n.asm"
    asm_subdir_under_mpn = os.path.dirname(asm_path_under_mpn)  # e.g. "x86_64"
    if not asm_subdir_under_mpn:
        sys.exit(f"asm file should be in an mpn subdir (got {asm_rel})")

    with tempfile.TemporaryDirectory(prefix="gmp_asm_") as stage:
        stage_mpn = os.path.join(stage, "mpn")
        stage_subdir = os.path.join(stage_mpn, asm_subdir_under_mpn)
        os.makedirs(stage_subdir, exist_ok=True)

        # Place config.m4 ABOVE mpn/ -- include('../config.m4') from m4's
        # cwd at <stage>/mpn/ resolves to <stage>/config.m4.
        shutil.copy2(config_m4, os.path.join(stage, "config.m4"))

        # Symlink the asm file at <stage>/mpn/<sub>/<name>.asm.
        os.symlink(asm, os.path.join(stage_mpn, asm_path_under_mpn))

        # Step 1: m4.  cwd = <stage>/mpn/, file = <sub>/<name>.asm.
        m4_cmd = [
            args.m4,
            f"-DOPERATION_{args.operation}",
            asm_path_under_mpn,
        ]
        with open(out_s, "wb") as fout:
            r = subprocess.run(m4_cmd, cwd=stage_mpn, stdout=fout)
        if r.returncode != 0:
            sys.exit(f"m4 failed (exit {r.returncode}): {' '.join(m4_cmd)}")

        # Step 2: assembler.
        as_cmd = [args.as_tool]
        if args.asflags:
            as_cmd += args.asflags.split()
        as_cmd += [out_s, "-o", out_o]
        r = subprocess.run(as_cmd)
        if r.returncode != 0:
            sys.exit(f"as failed (exit {r.returncode}): {' '.join(as_cmd)}")


if __name__ == "__main__":
    main()

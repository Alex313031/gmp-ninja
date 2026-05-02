#!/usr/bin/env python3
"""Build libgmp_asm.a -- the static archive of all asm-implemented mpn functions.

Driven by `select_mpn_asm.py`'s JSON description of the (function, asm_path,
operation_define) tuples for the active CPU tune.  For each tuple this script
runs m4 + the assembler to produce a .o, then bundles them into a .a via ar.

Designed to be invoked as a single GN action; runs the per-asm builds in
parallel using a thread pool.
"""
import argparse
import concurrent.futures as cf
import json
import os
import shutil
import subprocess
import sys
import tempfile


def compile_one(idx: int, asm_abs: str, op: str, top_srcdir: str,
                config_m4: str, m4_bin: str, as_bin: str,
                asflags: list[str], out_dir: str) -> str:
    """m4 + as a single (asm, op) pair.  Returns the produced .o path.

    See asm_to_o.py for the staging-layout rationale -- in short, m4 must
    run from <stage>/mpn/ so that `include('../config.m4')` resolves to
    <stage>/config.m4 regardless of how deeply the asm file is nested
    (e.g., mpn/x86_64/coreihwl/aors_n.asm).
    """
    asm_rel = os.path.relpath(asm_abs, top_srcdir)
    if not asm_rel.startswith("mpn" + os.sep):
        raise SystemExit(f"asm not under top_srcdir/mpn/: {asm_abs}")
    asm_path_under_mpn = asm_rel[len("mpn" + os.sep):]
    asm_subdir_under_mpn = os.path.dirname(asm_path_under_mpn)

    # Per-pair stage dir so concurrent compiles don't fight over names.
    stage = tempfile.mkdtemp(prefix=f"gmp_asm_{idx:03d}_")
    try:
        stage_mpn = os.path.join(stage, "mpn")
        stage_subdir = os.path.join(stage_mpn, asm_subdir_under_mpn)
        os.makedirs(stage_subdir, exist_ok=True)
        shutil.copy2(config_m4, os.path.join(stage, "config.m4"))
        os.symlink(asm_abs, os.path.join(stage_mpn, asm_path_under_mpn))

        # Output .o name: <op>.o (function name is unique).
        out_s = os.path.join(out_dir, f"{op}.s")
        out_o = os.path.join(out_dir, f"{op}.o")

        # m4 -DOPERATION_<op> <sub>/<name>.asm    (cwd = <stage>/mpn/)
        with open(out_s, "wb") as fout:
            r = subprocess.run(
                [m4_bin, f"-DOPERATION_{op}", asm_path_under_mpn],
                cwd=stage_mpn,
                stdout=fout,
            )
        if r.returncode != 0:
            raise SystemExit(
                f"m4 failed on {asm_rel} (op={op}): exit {r.returncode}")

        # as <asflags> <out_s> -o <out_o>
        r = subprocess.run([as_bin, *asflags, out_s, "-o", out_o])
        if r.returncode != 0:
            raise SystemExit(
                f"as failed on {asm_rel} (op={op}): exit {r.returncode}")
        return out_o
    finally:
        shutil.rmtree(stage, ignore_errors=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--asm-json", required=True,
                   help="Path to JSON output of select_mpn_asm.py.")
    p.add_argument("--config-m4", required=True,
                   help="Path to generated config.m4.")
    p.add_argument("--top-srcdir", required=True,
                   help="Path to gmp/ srcdir.")
    p.add_argument("--out-archive", required=True,
                   help="Output libgmp_asm.a path.")
    p.add_argument("--m4", default="m4", help="m4 binary path.")
    p.add_argument("--as", dest="as_bin", required=True,
                   help="Assembler path (e.g. x86_64-w64-mingw32-as).")
    p.add_argument("--ar", required=True,
                   help="ar path (e.g. x86_64-w64-mingw32-ar).")
    p.add_argument("--asflags", default="",
                   help="Extra flags for the assembler (space-separated).")
    p.add_argument("--jobs", type=int, default=os.cpu_count() or 4)
    p.add_argument("--keep-stage", action="store_true",
                   help="Keep .s/.o files for debugging (default: discard "
                        "after archive).")
    args = p.parse_args()

    with open(args.asm_json) as f:
        asm_data = json.load(f)

    top_srcdir = os.path.abspath(args.top_srcdir)
    config_m4 = os.path.abspath(args.config_m4)
    out_archive = os.path.abspath(args.out_archive)
    asflags = args.asflags.split() if args.asflags else []

    # Output directory for individual .o files.  Lives next to the archive.
    out_dir = os.path.join(os.path.dirname(out_archive), "asm_objs")
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir)

    pairs = asm_data["asm"]
    if not pairs:
        # No asm pairs -- just produce an empty archive.  ar requires at
        # least one input, so fabricate an empty .o.
        empty_o = os.path.join(out_dir, "empty.o")
        empty_s = os.path.join(out_dir, "empty.s")
        with open(empty_s, "w") as f:
            f.write("\t.text\n")
        subprocess.run([args.as_bin, *asflags, empty_s, "-o", empty_o],
                       check=True)
        subprocess.run([args.ar, "rcs", out_archive, empty_o], check=True)
        if not args.keep_stage:
            shutil.rmtree(out_dir, ignore_errors=True)
        print(f"wrote empty archive {out_archive}")
        return

    o_files: list[str] = []
    print(f"Compiling {len(pairs)} asm functions for tune={asm_data['tune']}...",
          file=sys.stderr)
    with cf.ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = []
        for i, p in enumerate(pairs):
            asm_abs = os.path.join(top_srcdir, p["asm_path"])
            futures.append(pool.submit(
                compile_one, i, asm_abs, p["operation_define"],
                top_srcdir, config_m4, args.m4, args.as_bin, asflags, out_dir,
            ))
        for fu in cf.as_completed(futures):
            o_files.append(fu.result())

    # Archive.  Use deterministic mode (`D' flag) where supported.
    o_files.sort()
    if os.path.exists(out_archive):
        os.unlink(out_archive)
    subprocess.run([args.ar, "rcsD", out_archive, *o_files], check=True)

    if not args.keep_stage:
        shutil.rmtree(out_dir, ignore_errors=True)
    print(f"wrote archive {out_archive} ({len(o_files)} objects)",
          file=sys.stderr)


if __name__ == "__main__":
    main()

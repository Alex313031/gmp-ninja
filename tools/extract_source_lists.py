#!/usr/bin/env python3
"""Extract source lists from gmp/Makefile.am and emit gmp_sources.gni.

Reads gmp/Makefile.am and produces a GN .gni file with the per-module
source lists (mpf, mpq, mpz, rand, printf, scanf, cxx) plus libgmp's
toplevel C files and the filtered mpn/generic/*.c list.  BUILD.gn imports
the generated .gni and just references the variables -- so BUILD.gn never
needs to be touched when GMP is upgraded.

Variables produced:

  gmp_toplevel_sources  -- libgmp_la_SOURCES + tal-reent.c (TAL_OBJECT)
  mpf_sources           -- MPF_OBJECTS
  mpz_sources           -- MPZ_OBJECTS
  mpq_sources           -- MPQ_OBJECTS
  rand_sources          -- RANDOM_OBJECTS
  printf_sources        -- PRINTF_OBJECTS
  scanf_sources         -- SCANF_OBJECTS
  gmpxx_core_sources    -- CXX_OBJECTS, .lo -> .cc (no $U)
  mpn_full_sources      -- gmp/mpn/generic/*.c minus the OPERATION-driven
                           multi-function files (handled in
                           missing/mpn_sec_ops.c) and udiv_w_sdiv.c (x86/
                           x64 have unsigned division).

Run via tools/extract_source_lists.py or via the toplevel regen_all.sh.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
MAKEFILE_AM = os.path.join(PROJECT, "gmp", "Makefile.am")
MPN_GENERIC_DIR = os.path.join(PROJECT, "gmp", "mpn", "generic")
OUT_GNI = os.path.join(PROJECT, "gmp_sources.gni")

# Object-list names in Makefile.am whose contents we want, mapped to the
# corresponding GN variable name and the source extension to expect after
# stripping "$U" (no-op on $U) and ".lo".  CXX uses .cc; everything else .c.
OBJECT_LISTS = [
    # (Makefile.am var, GN var, extension, src dir basename)
    ("MPF_OBJECTS",     "mpf_sources",        ".c",  "mpf"),
    ("MPZ_OBJECTS",     "mpz_sources",        ".c",  "mpz"),
    ("MPQ_OBJECTS",     "mpq_sources",        ".c",  "mpq"),
    ("PRINTF_OBJECTS",  "printf_sources",     ".c",  "printf"),
    ("SCANF_OBJECTS",   "scanf_sources",      ".c",  "scanf"),
    ("RANDOM_OBJECTS",  "rand_sources",       ".c",  "rand"),
    ("CXX_OBJECTS",     "gmpxx_core_sources", ".cc", "cxx"),
]

# mpn/generic/*.c files to skip:
#   - The five OPERATION-driven multi-function files; they're expanded
#     once each from missing/mpn_sec_ops.c with the right OPERATION_*
#     define per inclusion.
#   - udiv_w_sdiv.c is for CPUs with only signed division (m68k etc.);
#     irrelevant on x86/x64.
MPN_GENERIC_EXCLUDE = {
    "sec_aors_1.c",
    "sec_div.c",
    "sec_pi1_div.c",
    "popham.c",
    "logops_n.c",
    "udiv_w_sdiv.c",
}

# libgmp's toplevel C files come from libgmp_la_SOURCES *plus* tal-reent.c
# (which is an EXTRA_libgmp_la_SOURCES entry that the Makefile pulls in via
# @TAL_OBJECT@ when --enable-alloca=reentrant is selected).  We hard-pick
# tal-reent.c since that's the only one of {tal-debug, tal-notreent,
# tal-reent} that builds without WANT_TMP_REENTRANT/WANT_TMP_NOTREENTRANT
# clashing with gmp-impl's defaults.
EXTRA_TOPLEVEL_C = ["tal-reent.c"]


def extract_object_list(makefile_text: str, var_name: str) -> list[str]:
    """Return the list of items in a Makefile.am `var_name = ...` assignment."""
    m = re.search(rf'^{re.escape(var_name)}\s*=\s*((?:.*\\\n)*.*)\n',
                  makefile_text, re.M)
    if not m:
        sys.exit(f"failed to find {var_name} in {MAKEFILE_AM}")
    body = m.group(1).replace('\\\n', ' ')
    items = [x for x in body.split() if '/' in x]
    # Strip $U (used by automake's ansi2knr feature, irrelevant here).
    items = [re.sub(r'\$U', '', x) for x in items]
    # Sort + dedupe; Makefile.am lists are mostly already sorted but not
    # always strictly.  We always emit sorted output for determinism.
    return sorted(set(items))


def list_mpn_generic_sources() -> list[str]:
    """All gmp/mpn/generic/*.c files minus MPN_GENERIC_EXCLUDE."""
    if not os.path.isdir(MPN_GENERIC_DIR):
        sys.exit(f"missing dir: {MPN_GENERIC_DIR}")
    keep = []
    for name in sorted(os.listdir(MPN_GENERIC_DIR)):
        if not name.endswith(".c"):
            continue
        if name in MPN_GENERIC_EXCLUDE:
            continue
        keep.append(f"mpn/generic/{name}")
    return keep


def extract_libgmp_la_sources(makefile_text: str) -> list[str]:
    """libgmp_la_SOURCES, restricted to actual .c files (drop headers)."""
    raw = extract_object_list_loose(makefile_text, "libgmp_la_SOURCES")
    return sorted(x for x in raw if x.endswith(".c"))


def extract_object_list_loose(makefile_text: str, var_name: str) -> list[str]:
    """Like extract_object_list but accepts items without a `/` (for
    libgmp_la_SOURCES, which lists bare basenames)."""
    m = re.search(rf'^{re.escape(var_name)}\s*=\s*((?:.*\\\n)*.*)\n',
                  makefile_text, re.M)
    if not m:
        sys.exit(f"failed to find {var_name} in {MAKEFILE_AM}")
    body = m.group(1).replace('\\\n', ' ')
    return [x for x in body.split() if x]


def gn_list(items: list[str], indent: str = "  ") -> str:
    if not items:
        return "[]"
    inner = ",\n".join(f'{indent}"{x}"' for x in items)
    return f"[\n{inner},\n]"


def render(out_path: str, makefile_text: str):
    parts = []
    parts.append("# AUTO-GENERATED by tools/extract_source_lists.py from")
    parts.append("# gmp/Makefile.am.  Do NOT edit by hand -- changes will")
    parts.append("# be lost on the next ./regen_all.sh.")
    parts.append("#")
    parts.append("# All paths are relative to src/gmp-ninja/.  Source roots:")
    parts.append("#   gmp/<sub>/<file>           -- upstream GMP sources")
    parts.append("#   missing/<file>             -- our hand-maintained shim")
    parts.append("#   missing/{x86,x64}/<file>   -- our generated tables")
    parts.append("")

    # Per-module lists: prefix each item with `gmp/<dir>/`.
    for am_var, gn_var, ext, subdir in OBJECT_LISTS:
        raw = extract_object_list(makefile_text, am_var)
        # Items look like "mpf/init$U.lo" -> "mpf/init.lo" after $U strip.
        # Convert to "gmp/mpf/init.c" (or .cc for cxx).
        files = []
        for item in raw:
            if not item.startswith(f"{subdir}/"):
                sys.exit(f"unexpected item in {am_var}: {item}")
            base = item[len(subdir) + 1:]
            base = re.sub(r"\.lo$", ext, base)
            files.append(f"gmp/{subdir}/{base}")
        parts.append(f"# {am_var}: {len(files)} files")
        parts.append(f"{gn_var} = {gn_list(files)}")
        parts.append("")

    # libgmp toplevel sources (libgmp_la_SOURCES + EXTRA_TOPLEVEL_C).
    top = extract_libgmp_la_sources(makefile_text)
    top_files = sorted({f"gmp/{x}" for x in top + EXTRA_TOPLEVEL_C})
    parts.append(f"# libgmp_la_SOURCES (+ tal-reent.c): {len(top_files)} files")
    parts.append(f"gmp_toplevel_sources = {gn_list(top_files)}")
    parts.append("")

    # mpn/generic *.c, excluding the OPERATION-multiplexed and m68k bits.
    mpn_files = [f"gmp/{x}" for x in list_mpn_generic_sources()]
    parts.append(f"# mpn/generic/*.c (minus OPERATION-multiplexed files): "
                 f"{len(mpn_files)} files")
    parts.append(f"mpn_full_sources = {gn_list(mpn_files)}")
    parts.append("")

    body = "\n".join(parts)
    with open(out_path, "w") as f:
        f.write(body)
    print(f"wrote {out_path} ({body.count(chr(10))} lines)")
    print(f"  per-module counts:")
    for am_var, gn_var, _, _ in OBJECT_LISTS:
        n = len(extract_object_list(makefile_text, am_var))
        print(f"    {gn_var:24s} {n:4d}")
    print(f"    {'gmp_toplevel_sources':24s} {len(top_files):4d}")
    print(f"    {'mpn_full_sources':24s} {len(mpn_files):4d}")


def main():
    if not os.path.isfile(MAKEFILE_AM):
        sys.exit(f"can't find {MAKEFILE_AM}")
    with open(MAKEFILE_AM) as f:
        text = f.read()
    render(OUT_GNI, text)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Substitute autoconf-style @VAR@ placeholders in gmp/gmp-h.in.

The generated gmp.h is target-agnostic: it picks GMP_LIMB_BITS at preprocess
time from __x86_64__ / _WIN64 so the same header serves x86 and x86_64 builds
on both Linux and Windows (MinGW).
"""
import re
import sys

if len(sys.argv) != 3:
    sys.exit("usage: gen_gmp_h.py <gmp-h.in> <gmp.h>")

src, dst = sys.argv[1], sys.argv[2]

# Multi-line replacements need block insertion -- handle these line-by-line.
GMP_LIMB_BITS_BLOCK = """\
#if defined(__x86_64__) || defined(_M_X64) || defined(_WIN64)
#define GMP_LIMB_BITS                      64
#else
#define GMP_LIMB_BITS                      32
#endif"""

DEFN_LONG_LONG_LIMB_BLOCK = """\
#if defined(_WIN64) || (defined(__x86_64__) && (defined(_WIN32) || defined(__MINGW32__)))
#define _LONG_LONG_LIMB 1
#endif"""

# __GMP_LIBGMP_DLL is wrapped in #ifndef so that a build-time -D__GMP_LIBGMP_DLL=1
# (used for shared-library builds) wins over the default.
LIBGMP_DLL_BLOCK = """\
#ifndef __GMP_LIBGMP_DLL
#define __GMP_LIBGMP_DLL  0
#endif"""

SCALAR_SUBS = {
    "@HAVE_HOST_CPU_FAMILY_power@": "0",
    "@HAVE_HOST_CPU_FAMILY_powerpc@": "0",
    "@GMP_NAIL_BITS@": "0",
    "@CC@": "gcc",
    "@CFLAGS@": "-O2",
}

with open(src) as f:
    lines = f.readlines()

out = []
for line in lines:
    stripped = line.rstrip("\n")
    if "@GMP_LIMB_BITS@" in stripped:
        out.append(GMP_LIMB_BITS_BLOCK + "\n")
        continue
    if stripped == "@DEFN_LONG_LONG_LIMB@":
        out.append(DEFN_LONG_LONG_LIMB_BLOCK + "\n")
        continue
    if "@LIBGMP_DLL@" in stripped:
        out.append(LIBGMP_DLL_BLOCK + "\n")
        continue
    for k, v in SCALAR_SUBS.items():
        stripped = stripped.replace(k, v)
    # Sanity: any unreplaced @VAR@ is a bug.
    leftover = re.search(r"@[A-Za-z_]+@", stripped)
    if leftover:
        sys.exit(f"unhandled placeholder: {leftover.group(0)} in line: {line!r}")
    out.append(stripped + "\n")

with open(dst, "w") as f:
    f.writelines(out)

print(f"wrote {dst} ({len(out)} lines)")

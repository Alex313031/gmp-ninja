#!/bin/bash
# Regenerate every artifact derived from the upstream GMP sources.
#
# Run this after editing anything under gmp/ (e.g. dropping in a newer
# GMP tarball), or after modifying gmp/Makefile.am / gmp/configure.ac.
#
# Outputs touched:
#   gmp.h, gmpxx.h               (repo root)
#   missing/gmp.h                (substituted from gmp/gmp-h.in)
#   missing/jacobitab.h          (ABI-independent)
#   missing/x64/*                (8 generated tables for LIMB_BITS=64)
#   missing/x86/*                (8 generated tables for LIMB_BITS=32)
#   gmp_sources.gni              (per-module C source lists)
#
# Outputs NOT touched (hand-maintained -- edit directly when needed):
#   missing/config.h             target-detection #ifs
#   missing/gmp-mparam.h         per-CPU tuning dispatcher
#   missing/mpn_sec_ops.c        OPERATION-multi stub
#   missing/unistd.h             Windows POSIX shim
#   tools/select_mpn_asm.py      CPU search-path table
#                                 (update if upstream adds a new CPU)
#
# Requires: a host C compiler (uses $CC, default gcc) with libm,
#           and python3.  Both are needed at gn-gen time too.

set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"

echo "== [1/2] Regenerating headers and tables..."
"$HERE/tools/regen.sh"

echo
echo "== [2/2] Regenerating gmp_sources.gni from gmp/Makefile.am..."
python3 "$HERE/tools/extract_source_lists.py"

echo
echo "All regen complete.  Summary:"
echo "  gmp.h, gmpxx.h         repo root"
echo "  missing/gmp.h          target-agnostic (#if guarded)"
echo "  missing/jacobitab.h    ABI-independent"
echo "  missing/x64/*          $(ls "$HERE"/missing/x64/ 2>/dev/null | wc -l) files"
echo "  missing/x86/*          $(ls "$HERE"/missing/x86/ 2>/dev/null | wc -l) files"
echo "  gmp_sources.gni        $(wc -l < "$HERE"/gmp_sources.gni) lines"
echo
echo "Next: 'gn gen out/Release && ninja -C out/Release gmp_all'"

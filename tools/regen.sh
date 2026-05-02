#!/bin/bash
# Regenerate the headers/tables under missing/ from gmp/.
#
# Layout produced:
#   missing/gmp.h            <- target-agnostic, generated from gmp-h.in
#   missing/jacobitab.h      <- ABI-independent (no LIMB_BITS dependency)
#   missing/x64/*.{h,c}      <- LIMB_BITS=64 set (Linux x86_64, MinGW x64)
#   missing/x86/*.{h,c}      <- LIMB_BITS=32 set (i686 MinGW)
#
# Default behavior is to regenerate BOTH ABI sets (and gmp.h once).  Pass
# --abi=32 or --abi=64 to refresh just one.
set -euo pipefail

ABIS="32 64"
for arg in "$@"; do
  case "$arg" in
    --abi=32) ABIS="32" ;;
    --abi=64) ABIS="64" ;;
    --abi=both) ABIS="32 64" ;;
    *) echo "unknown arg: $arg" >&2; exit 2 ;;
  esac
done

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
GMP="$ROOT/gmp"
BUILD="$(mktemp -d)"
trap "rm -rf '$BUILD'" EXIT

CC=${CC:-gcc}
CFLAGS=${CFLAGS:--O2}

echo "== Building gen-* host tools in $BUILD"
ln -s "$GMP/mini-gmp" "$BUILD/mini-gmp"
cp "$GMP/bootstrap.c" "$BUILD/bootstrap.c"
for prog in gen-bases gen-fac gen-fib gen-jacobitab gen-psqr gen-sieve gen-trialdivtab; do
  cp "$GMP/$prog.c" "$BUILD/$prog.c"
  $CC $CFLAGS "$BUILD/$prog.c" -o "$BUILD/$prog" -lm
done

# ABI-independent: gen-jacobitab takes no args.
echo "== Generating jacobitab.h -> $ROOT/missing/jacobitab.h"
"$BUILD/gen-jacobitab" >"$ROOT/missing/jacobitab.h"

for ABI in $ABIS; do
  if [ "$ABI" = "32" ]; then
    OUT="$ROOT/missing/x86"
  else
    OUT="$ROOT/missing/x64"
  fi
  mkdir -p "$OUT"
  LIMB=$ABI
  NAIL=0
  echo "== Generating ABI=$ABI tables (LIMB_BITS=$LIMB NAIL_BITS=$NAIL) into $OUT"
  "$BUILD/gen-fac"         "$LIMB" "$NAIL" >"$OUT/fac_table.h"
  "$BUILD/gen-fib"  header "$LIMB" "$NAIL" >"$OUT/fib_table.h"
  "$BUILD/gen-fib"  table  "$LIMB" "$NAIL" >"$OUT/fib_table.c"
  "$BUILD/gen-bases" header "$LIMB" "$NAIL" >"$OUT/mp_bases.h"
  "$BUILD/gen-bases" table  "$LIMB" "$NAIL" >"$OUT/mp_bases.c"
  "$BUILD/gen-psqr"        "$LIMB" "$NAIL" >"$OUT/perfsqr.h"
  "$BUILD/gen-sieve"       "$LIMB"         >"$OUT/sieve_table.h"
  "$BUILD/gen-trialdivtab" "$LIMB" 8000    >"$OUT/trialdivtab.h"
done

# gmp.h is target-agnostic (uses #if on __x86_64__/_WIN64), so generate it
# once regardless of which ABI(s) were requested.
GMP_H="$ROOT/missing/gmp.h"
echo "== Generating gmp.h -> $GMP_H"
python3 "$ROOT/tools/gen_gmp_h.py" "$GMP/gmp-h.in" "$GMP_H"
cp -af "$GMP_H" "$ROOT/gmp.h"
cp -af "$GMP/gmpxx.h" "$ROOT/gmpxx.h"

echo "== Done."
ls -la "$ROOT/missing"
[ -d "$ROOT/missing/x64" ] && ls -la "$ROOT/missing/x64"
[ -d "$ROOT/missing/x86" ] && ls -la "$ROOT/missing/x86"

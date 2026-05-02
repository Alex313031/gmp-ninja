#!/usr/bin/env python3
"""Resolve mpn function -> asm file mappings, replacing GMP's autoconf logic.

GMP's `configure` walks a CPU-specific search path (e.g. for Haswell:
`x86_64/coreihwl x86_64/coreisbr x86_64/coreinhm x86_64/core2 x86_64`) and
for each function in `gmp_mpn_functions` looks for an asm implementation,
falling back to the generic-C version when no asm is available.  Several
asm files are "multi-function" -- e.g. `aors_n.asm` provides both
`mpn_add_n` and `mpn_sub_n`, dispatching at m4 time on `OPERATION_<name>`.

This script reproduces that resolution.  Inputs:

  --gmp-srcdir   the gmp/ tree (the one with mpn/x86_64/ etc inside).
  --cpu          x86 | x64
  --tune         one of the supported leaves: k8, k10, ..., haswell, zen.

Output (printed JSON to stdout) describes:

  {
    "asm": [
      {"function": "add_n", "asm_path": "mpn/x86_64/aors_n.asm",
       "operation_define": "add_n"},
      ...
    ],
    "drop_c": ["mpn/generic/add_n.c", "mpn/generic/sub_n.c", ...]
  }

The "asm" list tells the build which asm TU's to compile and with what
OPERATION_<name> macro.  The "drop_c" list tells the build which generic
C files to *skip* (because they're now provided by asm), preventing
duplicate symbols at link time.
"""
import argparse
import json
import os
import sys


# ---------------------------------------------------------------------------
# Function lists, derived from gmp/configure.ac.

# Always-built functions (the union of `extra_functions` for the platform
# and `gmp_mpn_functions` from the configure.ac base list at line 3056).
# x86 / x86_64 do not contribute extra arch-specific functions to this list.
GMP_MPN_FUNCTIONS = """
add add_1 add_n sub sub_1 sub_n cnd_add_n cnd_sub_n cnd_swap neg com
mul_1 addmul_1 submul_1
add_err1_n add_err2_n add_err3_n sub_err1_n sub_err2_n sub_err3_n
lshift rshift dive_1 diveby3 divis divrem divrem_1 divrem_2
fib2_ui fib2m mod_1 mod_34lsub1 mode1o pre_divrem_1 pre_mod_1 dump
mod_1_1 mod_1_2 mod_1_3 mod_1_4 lshiftc
mul mul_fft mul_n sqr mul_basecase sqr_basecase nussbaumer_mul
mulmid_basecase toom42_mulmid mulmid_n mulmid
random random2 pow_1
rootrem sqrtrem sizeinbase get_str set_str compute_powtab
scan0 scan1 popcount hamdist cmp zero_p
perfsqr perfpow strongfibo
gcd_11 gcd_22 gcd_1 gcd gcdext_1 gcdext gcd_subdiv_step
gcdext_lehmer
div_q tdiv_qr jacbase jacobi_2 jacobi get_d
matrix22_mul matrix22_mul1_inverse_vector
hgcd_matrix hgcd2 hgcd_step hgcd_reduce hgcd hgcd_appr
hgcd2_jacobi hgcd_jacobi
mullo_n mullo_basecase sqrlo sqrlo_basecase
toom22_mul toom32_mul toom42_mul toom52_mul toom62_mul
toom33_mul toom43_mul toom53_mul toom54_mul toom63_mul
toom44_mul
toom6h_mul toom6_sqr toom8h_mul toom8_sqr
toom_couple_handling
toom2_sqr toom3_sqr toom4_sqr
toom_eval_dgr3_pm1 toom_eval_dgr3_pm2
toom_eval_pm1 toom_eval_pm2 toom_eval_pm2exp toom_eval_pm2rexp
toom_interpolate_5pts toom_interpolate_6pts toom_interpolate_7pts
toom_interpolate_8pts toom_interpolate_12pts toom_interpolate_16pts
invertappr invert binvert mulmod_bnm1 sqrmod_bnm1 mulmod_bknp1
div_qr_1 div_qr_1n_pi1
div_qr_2 div_qr_2n_pi1 div_qr_2u_pi1
sbpi1_div_q sbpi1_div_qr sbpi1_divappr_q
dcpi1_div_q dcpi1_div_qr dcpi1_divappr_q
mu_div_qr mu_divappr_q mu_div_q
bdiv_q_1
sbpi1_bdiv_q sbpi1_bdiv_qr sbpi1_bdiv_r
dcpi1_bdiv_q dcpi1_bdiv_qr
mu_bdiv_q mu_bdiv_qr
bdiv_q bdiv_qr broot brootinv bsqrt bsqrtinv
divexact bdiv_dbm1c redc_1 redc_2 redc_n powm powlo sec_powm
sec_mul sec_sqr sec_div_qr sec_div_r sec_pi1_div_qr sec_pi1_div_r
sec_add_1 sec_sub_1 sec_invert
trialdiv remove
and_n andn_n nand_n ior_n iorn_n nior_n xor_n xnor_n
copyi copyd zero sec_tabselect
comb_tables
""".split()

# Optional asm-only functions: built only when an asm file provides them.
# (configure.ac line 3047: gmp_mpn_functions_optional)
GMP_MPN_FUNCTIONS_OPTIONAL = """
umul udiv
invert_limb sqr_diagonal sqr_diag_addlsh1
mul_2 mul_3 mul_4 mul_5 mul_6
addmul_2 addmul_3 addmul_4 addmul_5 addmul_6 addmul_7 addmul_8
addlsh1_n sublsh1_n rsblsh1_n rsh1add_n rsh1sub_n
addlsh2_n sublsh2_n rsblsh2_n
addlsh_n sublsh_n rsblsh_n
add_n_sub_n addaddmul_1msb0
""".split()


# ---------------------------------------------------------------------------
# Multi-function asm files.  Each entry maps an asm filename (without `.asm`)
# to the set of OPERATION_<name> values it can be compiled with.
#
# Source: configure.ac GMP_MULFUNC_CHOICES.  Only the entries that actually
# appear under x86/ or x86_64/ are listed.
MULTIFUNC = {
    "aors_n":       ["add_n", "sub_n"],
    "aors_err1_n":  ["add_err1_n", "sub_err1_n"],
    "aors_err2_n":  ["add_err2_n", "sub_err2_n"],
    "aors_err3_n":  ["add_err3_n", "sub_err3_n"],
    "cnd_aors_n":   ["cnd_add_n", "cnd_sub_n"],
    "sec_aors_1":   ["sec_add_1", "sec_sub_1"],
    "aorsmul_1":    ["addmul_1", "submul_1"],
    "aormul_2":     ["mul_2", "addmul_2"],
    "aormul_3":     ["mul_3", "addmul_3"],
    "aormul_4":     ["mul_4", "addmul_4"],
    "popham":       ["popcount", "hamdist"],
    "logops_n":     ["and_n", "andn_n", "nand_n",
                     "ior_n", "iorn_n", "nior_n",
                     "xor_n", "xnor_n"],
    "lorrshift":    ["lshift", "rshift"],
    # The lsh-family are 3-way (addlsh1_n / sublsh1_n / rsblsh1_n) split
    # across three different asm filenames per upstream configure.ac.
    # NOTE: The "*C_n.asm" files (aorrlshC_n, aorslshC_n, sorrlshC_n,
    # aorsorrlshC_n) are m4 templates included by the lsh1/lsh2/lsh_n
    # variants below -- they parameterise on a `LSH` macro and are not
    # standalone TUs.  They must NOT appear here.
    "aorslsh1_n":   ["addlsh1_n", "sublsh1_n"],
    "aorrlsh1_n":   ["addlsh1_n", "rsblsh1_n"],
    "sorrlsh1_n":   ["sublsh1_n", "rsblsh1_n"],
    "aorsorrlsh1_n":["addlsh1_n", "sublsh1_n", "rsblsh1_n"],
    "aorslsh2_n":   ["addlsh2_n", "sublsh2_n"],
    "aorrlsh2_n":   ["addlsh2_n", "rsblsh2_n"],
    "sorrlsh2_n":   ["sublsh2_n", "rsblsh2_n"],
    "aorsorrlsh2_n":["addlsh2_n", "sublsh2_n", "rsblsh2_n"],
    "aorslsh_n":    ["addlsh_n", "sublsh_n"],
    "aorrlsh_n":    ["addlsh_n", "rsblsh_n"],
    "sorrlsh_n":    ["sublsh_n", "rsblsh_n"],
    "aorsorrlsh_n": ["addlsh_n", "sublsh_n", "rsblsh_n"],
    "rsh1aors_n":   ["rsh1add_n", "rsh1sub_n"],
}

# Reverse index: function name -> list of multifunc parents that can provide it.
_FUNC_TO_PARENTS = {}
for parent, funcs in MULTIFUNC.items():
    for f in funcs:
        _FUNC_TO_PARENTS.setdefault(f, []).append(parent)


# ---------------------------------------------------------------------------
# CPU search paths.  Source: gmp/configure.ac lines ~1775-2030.
# Maps a "tune" leaf (the name a user picks) to an ordered list of
# subdirectories of mpn/, searched left-to-right for asm files.
CPU_PATHS = {
    "x64": {
        "k8":         ["x86_64/k8", "x86_64"],
        "k10":        ["x86_64/k10", "x86_64/k8", "x86_64"],
        "bd1":        ["x86_64/bd1", "x86_64/k10", "x86_64/k8", "x86_64"],
        "bd2":        ["x86_64/bd2", "x86_64/bd1", "x86_64/k10", "x86_64/k8", "x86_64"],
        "bd3":        ["x86_64/bd3", "x86_64/bd2", "x86_64/bd1", "x86_64/k10", "x86_64/k8", "x86_64"],
        "bd4":        ["x86_64/bd4", "x86_64/bd3", "x86_64/bd2", "x86_64/bd1", "x86_64/k10", "x86_64/k8", "x86_64"],
        "bt1":        ["x86_64/bt1", "x86_64/k10", "x86_64/k8", "x86_64"],
        "bt2":        ["x86_64/bt2", "x86_64/bt1", "x86_64/k10", "x86_64/k8", "x86_64"],
        "zen":        ["x86_64/zen", "x86_64"],
        "zen2":       ["x86_64/zen2", "x86_64/zen", "x86_64"],
        "zen3":       ["x86_64/zen3", "x86_64/zen2", "x86_64/zen", "x86_64"],
        "core2":      ["x86_64/core2", "x86_64"],
        "nehalem":    ["x86_64/coreinhm", "x86_64/core2", "x86_64"],
        "sandybridge":["x86_64/coreisbr", "x86_64/coreinhm", "x86_64/core2", "x86_64"],
        "haswell":    ["x86_64/coreihwl", "x86_64/coreisbr", "x86_64/coreinhm", "x86_64/core2", "x86_64"],
        "broadwell":  ["x86_64/coreibwl", "x86_64/coreihwl", "x86_64/coreisbr", "x86_64/coreinhm", "x86_64/core2", "x86_64"],
        "skylake":    ["x86_64/skylake", "x86_64/coreibwl", "x86_64/coreihwl", "x86_64/coreisbr", "x86_64/coreinhm", "x86_64/core2", "x86_64"],
        "icelake":    ["x86_64/icelake", "x86_64/skylake", "x86_64/coreibwl", "x86_64/coreihwl", "x86_64/coreisbr", "x86_64/coreinhm", "x86_64/core2", "x86_64"],
        "alderlake":  ["x86_64/alderlake", "x86_64/icelake", "x86_64/skylake", "x86_64/coreibwl", "x86_64/coreihwl", "x86_64/coreisbr", "x86_64/coreinhm", "x86_64/core2", "x86_64"],
        "atom":       ["x86_64/atom", "x86_64"],
        "silvermont": ["x86_64/silvermont", "x86_64/atom", "x86_64"],
        "goldmont":   ["x86_64/goldmont", "x86_64/silvermont", "x86_64/atom", "x86_64"],
        "tremont":    ["x86_64/tremont", "x86_64/goldmont", "x86_64/silvermont", "x86_64/atom", "x86_64"],
        "nano":       ["x86_64/nano", "x86_64"],
        "pentium4":   ["x86_64/pentium4", "x86_64"],
        # Plain "x86_64" leaf -- just the baseline directory.
        "generic":    ["x86_64"],
    },
    "x86": {
        "i486":       ["x86/i486", "x86"],
        "pentium":    ["x86/pentium", "x86"],
        "pentiummmx": ["x86/pentium/mmx", "x86/pentium", "x86/mmx", "x86"],
        "i686":       ["x86/p6", "x86"],
        "pentium2":   ["x86/p6/mmx", "x86/p6", "x86/mmx", "x86"],
        "pentium3":   ["x86/p6/p3mmx", "x86/p6/mmx", "x86/p6", "x86/mmx", "x86"],
        "pentiumm":   ["x86/p6/sse2", "x86/p6/p3mmx", "x86/p6/mmx", "x86/p6", "x86/mmx", "x86"],
        "k6":         ["x86/k6/mmx", "x86/k6", "x86/mmx", "x86"],
        "k62":        ["x86/k6/k62mmx", "x86/k6/mmx", "x86/k6", "x86/mmx", "x86"],
        "k63":        ["x86/k6/k62mmx", "x86/k6/mmx", "x86/k6", "x86/mmx", "x86"],
        "geode":      ["x86/geode", "x86/k6/k62mmx", "x86/k6/mmx", "x86/k6", "x86/mmx", "x86"],
        "athlon":     ["x86/k7/mmx", "x86/k7", "x86/mmx", "x86"],
        "k8":         ["x86/k8", "x86/k7/mmx", "x86/k7", "x86/mmx", "x86"],
        "k10":        ["x86/k10", "x86/k8", "x86/k7/mmx", "x86/k7", "x86/mmx", "x86"],
        "bobcat":     ["x86/bt1", "x86/k7/mmx", "x86/k7", "x86/mmx", "x86"],
        "pentium4":   ["x86/pentium4/sse2", "x86/pentium4/mmx", "x86/pentium4", "x86/mmx", "x86"],
        "atom":       ["x86/atom/sse2", "x86/atom/mmx", "x86/atom", "x86/mmx", "x86"],
        "core2":      ["x86/core2", "x86/p6/sse2", "x86/p6/p3mmx", "x86/p6/mmx", "x86/p6", "x86/mmx", "x86"],
        "nehalem":    ["x86/coreinhm", "x86/core2", "x86/p6/sse2", "x86/p6/p3mmx", "x86/p6/mmx", "x86/p6", "x86/mmx", "x86"],
        "sandybridge":["x86/coreisbr", "x86/coreinhm", "x86/core2", "x86/p6/sse2", "x86/p6/p3mmx", "x86/p6/mmx", "x86/p6", "x86/mmx", "x86"],
        "haswell":    ["x86/coreisbr", "x86/coreinhm", "x86/core2", "x86/p6/sse2", "x86/p6/p3mmx", "x86/p6/mmx", "x86/p6", "x86/mmx", "x86"],
        "silvermont": ["x86/silvermont", "x86/atom/sse2", "x86/atom/mmx", "x86/atom", "x86/mmx", "x86"],
        "goldmont":   ["x86/goldmont", "x86/silvermont", "x86/atom/sse2", "x86/atom/mmx", "x86/atom", "x86/mmx", "x86"],
        # Bare-baseline (i486-or-better, no MMX).
        "generic":    ["x86"],
    },
}


# ---------------------------------------------------------------------------
# Resolution.

def find_asm_for_function(gmp_mpn_dir: str, search_path: list[str], func: str):
    """Return (relpath_under_mpn, operation_define) for first asm file in
    `search_path` providing `func`, or None if not found.

    Lookup order in each directory:
      1. <dir>/<func>.asm                  (single-function file)
      2. <dir>/<parent>.asm for any parent in MULTIFUNC where `func` is
         in MULTIFUNC[parent].
    """
    for d in search_path:
        # 1. direct match.
        direct = os.path.join(d, f"{func}.asm")
        if os.path.exists(os.path.join(gmp_mpn_dir, direct)):
            return (f"mpn/{direct}", func)
        # 2. multifunc parents.
        for parent in _FUNC_TO_PARENTS.get(func, ()):
            cand = os.path.join(d, f"{parent}.asm")
            if os.path.exists(os.path.join(gmp_mpn_dir, cand)):
                return (f"mpn/{cand}", func)
    return None


def resolve(gmp_srcdir: str, cpu: str, tune: str):
    if cpu not in CPU_PATHS:
        sys.exit(f"unknown cpu: {cpu}")
    if tune not in CPU_PATHS[cpu]:
        sys.exit(f"unknown {cpu} tune: {tune}; "
                 f"available: {', '.join(sorted(CPU_PATHS[cpu]))}")
    search_path = CPU_PATHS[cpu][tune]
    gmp_mpn_dir = os.path.join(gmp_srcdir, "mpn")

    asm_results = []
    used_funcs = set()

    # Mandatory functions: pick asm if available, else leave to generic-C.
    for func in GMP_MPN_FUNCTIONS:
        hit = find_asm_for_function(gmp_mpn_dir, search_path, func)
        if hit:
            asm_path, op = hit
            asm_results.append({
                "function": func,
                "asm_path": asm_path,
                "operation_define": op,
            })
            used_funcs.add(func)

    # Optional functions: include only if asm exists.
    for func in GMP_MPN_FUNCTIONS_OPTIONAL:
        hit = find_asm_for_function(gmp_mpn_dir, search_path, func)
        if hit:
            asm_path, op = hit
            asm_results.append({
                "function": func,
                "asm_path": asm_path,
                "operation_define": op,
            })
            used_funcs.add(func)

    # Determine which mpn/generic/*.c files must be dropped to avoid
    # duplicate-symbol link failures.  Mapping is 1:1 by name -- if an asm
    # provides `add_n`, we must drop mpn/generic/add_n.c.
    drop_c = sorted(
        f"gmp/mpn/generic/{f}.c" for f in used_funcs
        if os.path.exists(os.path.join(gmp_srcdir, "mpn", "generic", f"{f}.c"))
    )

    return {
        "cpu": cpu,
        "tune": tune,
        "search_path": search_path,
        "asm": sorted(asm_results, key=lambda r: r["function"]),
        "drop_c": drop_c,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--gmp-srcdir", required=True)
    p.add_argument("--cpu", required=True, choices=("x86", "x64"))
    p.add_argument("--tune", required=True)
    p.add_argument("--list-tunes", action="store_true")
    args = p.parse_args()

    if args.list_tunes:
        for cpu in sorted(CPU_PATHS):
            print(f"{cpu}: {' '.join(sorted(CPU_PATHS[cpu]))}")
        return

    out = resolve(args.gmp_srcdir, args.cpu, args.tune)
    json.dump(out, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()

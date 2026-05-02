/* config.h.  Hand-curated for the gmp-ninja GN/Ninja port.

   Unlike a proper autoconf-generated config.h, this single header serves all
   four supported targets:

     - Linux   x86      (i686-linux-gnu)
     - Linux   x86_64   (x86_64-linux-gnu)
     - Windows x86      (i686-w64-mingw32)
     - Windows x86_64   (x86_64-w64-mingw32)

   Target detection happens at preprocess time via the standard GCC/Clang
   built-in macros (__x86_64__ / _WIN32 / _WIN64 / __linux__ / __MINGW32__).
   To regenerate after upgrading the upstream GMP source, see tools/regen.sh.
*/

#ifndef GMP_NINJA_CONFIG_H
#define GMP_NINJA_CONFIG_H

/* ------------------------------------------------------------------------- */
/* Host CPU family.                                                          */
/* ------------------------------------------------------------------------- */
#if defined(__x86_64__) || defined(_M_X64) || defined(_WIN64)
# define HAVE_HOST_CPU_FAMILY_x86_64 1
#else
# define HAVE_HOST_CPU_FAMILY_x86 1
#endif

/* ------------------------------------------------------------------------- */
/* Limb size.  Matches GMP_LIMB_BITS in gmp.h.                               */
/* ------------------------------------------------------------------------- */
#if defined(__x86_64__) || defined(_M_X64) || defined(_WIN64)
# define SIZEOF_MP_LIMB_T 8
# define SIZEOF_VOID_P    8
#else
# define SIZEOF_MP_LIMB_T 4
# define SIZEOF_VOID_P    4
#endif

/* MinGW + MSVC use ILP32 for `long` even on x64; Linux x64 uses LP64.       */
#if defined(_WIN32) || defined(_WIN64)
# define SIZEOF_UNSIGNED_LONG 4
#else
# if defined(__x86_64__)
#  define SIZEOF_UNSIGNED_LONG 8
# else
#  define SIZEOF_UNSIGNED_LONG 4
# endif
#endif
#define SIZEOF_UNSIGNED       4
#define SIZEOF_UNSIGNED_SHORT 2

/* ------------------------------------------------------------------------- */
/* Endianness.  All four targets are little-endian.                          */
/* ------------------------------------------------------------------------- */
#define HAVE_DOUBLE_IEEE_LITTLE_ENDIAN 1
#define HAVE_LIMB_LITTLE_ENDIAN 1

/* ------------------------------------------------------------------------- */
/* Compiler features.                                                        */
/* ------------------------------------------------------------------------- */
#if defined(__GNUC__)
# define HAVE_ATTRIBUTE_CONST     1
# define HAVE_ATTRIBUTE_MALLOC    1
# define HAVE_ATTRIBUTE_MODE      1
# define HAVE_ATTRIBUTE_NORETURN  1
# define HAVE_HIDDEN_ALIAS        1
#else
# define HAVE_ATTRIBUTE_CONST     0
# define HAVE_ATTRIBUTE_MALLOC    0
# define HAVE_ATTRIBUTE_MODE      0
# define HAVE_ATTRIBUTE_NORETURN  0
# define HAVE_HIDDEN_ALIAS        0
#endif

/* ------------------------------------------------------------------------- */
/* Standard headers.                                                         */
/* ------------------------------------------------------------------------- */
#define HAVE_FCNTL_H     1
#define HAVE_FLOAT_H     1
#define HAVE_INTTYPES_H  1
#define HAVE_LOCALE_H    1
#define HAVE_MEMORY_H    1
#define HAVE_STDINT_H    1
#define HAVE_STDLIB_H    1
#define HAVE_STRINGS_H   1
#define HAVE_STRING_H    1
#define HAVE_SYS_PARAM_H 1
#define HAVE_SYS_STAT_H  1
#define HAVE_SYS_TYPES_H 1
#define HAVE_SSTREAM     1
#define STDC_HEADERS     1

#if defined(_WIN32) || defined(_WIN64)
# define HAVE_UNISTD_H        0  /* shimmed via missing/unistd.h */
# define HAVE_SYS_TIME_H      0  /* gettimeofday emulated via WinSock2 */
# define HAVE_SYS_RESOURCE_H  0
# define HAVE_ALLOCA_H        0  /* alloca via malloc.h */
# define HAVE_LANGINFO_H      0
# define HAVE_NL_TYPES_H      0
# define HAVE_SYS_MMAN_H      0
# define HAVE_DLFCN_H         0
#else
# define HAVE_UNISTD_H        1
# define HAVE_SYS_TIME_H      1
# define HAVE_SYS_RESOURCE_H  1
# define HAVE_ALLOCA_H        1
# define HAVE_LANGINFO_H      1
# define HAVE_NL_TYPES_H      1
# define HAVE_SYS_MMAN_H      1
# define HAVE_DLFCN_H         1
#endif

/* alloca() is available everywhere we care about. */
#define HAVE_ALLOCA 1

/* ------------------------------------------------------------------------- */
/* Standard libc functions.                                                  */
/* ------------------------------------------------------------------------- */
#define HAVE_CLOCK         1
#define HAVE_LOCALECONV    1
#define HAVE_MEMSET        1
#define HAVE_POPEN         1
#define HAVE_RAISE         1
#define HAVE_STRCHR        1
#define HAVE_STRERROR      1
#define HAVE_STRNLEN       1
#define HAVE_STRTOL        1
#define HAVE_STRTOUL       1
#define HAVE_VSNPRINTF     1

#define HAVE_DECL_FGETC    1
#define HAVE_DECL_FSCANF   1
#define HAVE_DECL_OPTARG   1
#define HAVE_DECL_UNGETC   1
#define HAVE_DECL_VFPRINTF 1
#define HAVE_DECL_SYS_ERRLIST 0
#define HAVE_DECL_SYS_NERR    0

/* Posix-only functions. */
#if defined(_WIN32) || defined(_WIN64)
# define HAVE_ALARM            0
# define HAVE_GETPAGESIZE      0
# define HAVE_GETRUSAGE        0
# define HAVE_GETTIMEOFDAY     1  /* MinGW's <sys/time.h> provides it */
# define HAVE_MMAP             0
# define HAVE_MPROTECT         0
# define HAVE_NL_LANGINFO      0
# define HAVE_SIGACTION        0
# define HAVE_SIGALTSTACK      0
# define HAVE_SIGSTACK         0
# define HAVE_SYSCONF          0
# define HAVE_OBSTACK_VPRINTF  0
# define HAVE_CLOCK_GETTIME    0
#else
# define HAVE_ALARM            1
# define HAVE_GETPAGESIZE      1
# define HAVE_GETRUSAGE        1
# define HAVE_GETTIMEOFDAY     1
# define HAVE_MMAP             1
# define HAVE_MPROTECT         1
# define HAVE_NL_LANGINFO      1
# define HAVE_SIGACTION        1
# define HAVE_SIGALTSTACK      1
# define HAVE_SYSCONF          1
# define HAVE_OBSTACK_VPRINTF  1
# define HAVE_CLOCK_GETTIME    1
#endif

/* ------------------------------------------------------------------------- */
/* Type availability.                                                        */
/* ------------------------------------------------------------------------- */
#define HAVE_INTMAX_T       1
#define HAVE_INTPTR_T       1
#define HAVE_LONG_DOUBLE    1
#define HAVE_LONG_LONG      1
#define HAVE_PTRDIFF_T      1
#define HAVE_UINT_LEAST32_T 1
#define HAVE_STD__LOCALE    1

/* ------------------------------------------------------------------------- */
/* Cycle counter / tune support.  Both x86 and x86_64 have rdtsc.            */
/* ------------------------------------------------------------------------- */
#if defined(__x86_64__) || defined(_M_X64) || defined(_WIN64)
# define HAVE_SPEED_CYCLECOUNTER 2
#else
# define HAVE_SPEED_CYCLECOUNTER 1
#endif

/* ------------------------------------------------------------------------- */
/* Windows DOS-mode markers (used by some CRT-specific code paths).          */
/* ------------------------------------------------------------------------- */
#if defined(_WIN64)
# define HOST_DOS64 1
#endif

/* ------------------------------------------------------------------------- */
/* Memory model and assembler.                                               */
/* ------------------------------------------------------------------------- */
#define LSYM_PREFIX "L"
#define LT_OBJDIR ".libs/"

/* NO_ASM controls TWO independent things:
     1. The mpn .asm pipeline (per-CPU asm files in gmp/mpn/x86_64/, x86/...)
        -- driven by the GN args gmp_use_asm + gmp_x64_tune in BUILD.gn,
        unrelated to this define.
     2. The inline-asm helpers in longlong.h (umul_ppmm, count_leading_zeros,
        invert_limb, etc.) which gcc inlines into the C functions.  This is
        what NO_ASM gates.
   The two layers are complementary and both can be on at once.  Default is
   to leave NO_ASM undefined so longlong.h's inline asm gets used.  Define
   NO_ASM=1 in your build args to force fully-portable C even for the
   inline helpers (mpn .asm pipeline is gated separately). */
/* #undef NO_ASM */

/* ------------------------------------------------------------------------- */
/* Package metadata.                                                         */
/* ------------------------------------------------------------------------- */
#define PACKAGE         "gmp"
#define PACKAGE_NAME    "GNU MP"
#define PACKAGE_STRING  "GNU MP 6.3.0"
#define PACKAGE_TARNAME "gmp"
#define PACKAGE_URL     "http://www.gnu.org/software/gmp/"
#define PACKAGE_VERSION "6.3.0"
#define PACKAGE_BUGREPORT \
    "gmp-bugs@gmplib.org (see https://gmplib.org/manual/Reporting-Bugs.html)"
#define VERSION         "6.3.0"
#define GMP_MPARAM_H_SUGGEST "./mpn/generic/gmp-mparam.h"

/* ------------------------------------------------------------------------- */
/* Knobs.                                                                    */
/* ------------------------------------------------------------------------- */
#define WANT_TMP_ALLOCA 1
#define WANT_FFT 1
#define TUNE_SQR_TOOM2_MAX SQR_TOOM2_MAX_GENERIC

/* `restrict' keyword.  GCC/Clang/MSVC all accept __restrict. */
#define restrict __restrict

#define RETSIGTYPE void

#endif /* GMP_NINJA_CONFIG_H */

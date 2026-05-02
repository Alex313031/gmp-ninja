/* gmp-mparam.h -- target tuning parameters for the gmp-ninja build.

   This header forwards to the appropriate per-CPU tuning header in
   gmp/mpn/<cpu>/gmp-mparam.h.  The defaults here are conservative
   baseline tunings (K8/K10 for x86_64, P6 for x86) that work on every
   supported chip from that family.

   To target a specific microarchitecture, define one of the GMP_TUNE_*
   macros via the build (e.g. -DGMP_TUNE_skylake).  See gmp/mpn/x86_64/
   and gmp/mpn/x86/ for the complete list of available CPUs.
*/

#ifndef GMP_NINJA_GMP_MPARAM_H
#define GMP_NINJA_GMP_MPARAM_H

#if defined(__x86_64__) || defined(_M_X64) || defined(_WIN64)
# if defined(GMP_TUNE_zen)
#   include "../gmp/mpn/x86_64/zen/gmp-mparam.h"
# elif defined(GMP_TUNE_skylake)
#   include "../gmp/mpn/x86_64/skylake/gmp-mparam.h"
# elif defined(GMP_TUNE_coreibwl)
#   include "../gmp/mpn/x86_64/coreibwl/gmp-mparam.h"
# elif defined(GMP_TUNE_coreihwl)
#   include "../gmp/mpn/x86_64/coreihwl/gmp-mparam.h"
# elif defined(GMP_TUNE_coreisbr)
#   include "../gmp/mpn/x86_64/coreisbr/gmp-mparam.h"
# elif defined(GMP_TUNE_core2)
#   include "../gmp/mpn/x86_64/core2/gmp-mparam.h"
# elif defined(GMP_TUNE_atom)
#   include "../gmp/mpn/x86_64/atom/gmp-mparam.h"
# elif defined(GMP_TUNE_silvermont)
#   include "../gmp/mpn/x86_64/silvermont/gmp-mparam.h"
# elif defined(GMP_TUNE_goldmont)
#   include "../gmp/mpn/x86_64/goldmont/gmp-mparam.h"
# else
   /* K8/K10 baseline -- works on every x86_64 chip. */
#   include "../gmp/mpn/x86_64/gmp-mparam.h"
# endif
#else
# if defined(GMP_TUNE_skylake)
#   include "../gmp/mpn/x86/skylake/gmp-mparam.h"
# elif defined(GMP_TUNE_coreibwl)
#   include "../gmp/mpn/x86/coreibwl/gmp-mparam.h"
# elif defined(GMP_TUNE_coreihwl)
#   include "../gmp/mpn/x86/coreihwl/gmp-mparam.h"
# elif defined(GMP_TUNE_coreisbr)
#   include "../gmp/mpn/x86/coreisbr/gmp-mparam.h"
# elif defined(GMP_TUNE_core2)
#   include "../gmp/mpn/x86/core2/gmp-mparam.h"
# elif defined(GMP_TUNE_atom)
#   include "../gmp/mpn/x86/atom/gmp-mparam.h"
# elif defined(GMP_TUNE_silvermont)
#   include "../gmp/mpn/x86/silvermont/gmp-mparam.h"
# elif defined(GMP_TUNE_goldmont)
#   include "../gmp/mpn/x86/goldmont/gmp-mparam.h"
# elif defined(GMP_TUNE_pentium4)
#   include "../gmp/mpn/x86/pentium4/gmp-mparam.h"
# else
   /* P6/Pentium-Pro baseline -- works on every i686+ x86 chip. */
#   include "../gmp/mpn/x86/p6/gmp-mparam.h"
# endif
#endif

#endif /* GMP_NINJA_GMP_MPARAM_H */

// Copyright (c) 2026 Alex313031
//
// Tests GMP by computing pi to 1000 decimal digits via Chudnovsky and
// timing the calculation.  This binary links against libgmp.so +
// libgmpxx.so dynamically.  RPATH is set to $ORIGIN so the shared libs
// can sit beside the executable and be hot-swapped without rebuild.
//
// Missing-library handling: dynamic linker prints
//   "error while loading shared libraries: libgmpxx.so: cannot open
//    shared object file: No such file or directory"
// to stderr and exits before main() runs -- no custom probe needed.

#include "pi/pi_chudnovsky.h"

int main() {
  const int retval = RunPiBenchmark("Linux, dynamically linked");
  return retval;
}

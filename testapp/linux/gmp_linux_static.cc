// Copyright (c) 2026 Alex313031
//
// Tests GMP by computing pi to 1000 decimal digits via Chudnovsky and
// timing the calculation.  This binary uses libgmp_static.a +
// libgmpxx_static.a -- no shared libraries needed at runtime.

#include "pi/pi_chudnovsky.h"

int main() {
  const int retval = RunPiBenchmark("Linux, statically linked");
  return retval;
}

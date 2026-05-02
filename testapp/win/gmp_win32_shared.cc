// Copyright (c) 2026 Alex313031
//
// Tests GMP by computing pi to 1000 decimal digits via Chudnovsky and
// timing the calculation.  This binary links against libgmp.dll +
// libgmpxx.dll via the import library.  Drop the .dll's in the same
// directory as the .exe (Windows searches the app dir first) and they
// can be hot-swapped without rebuilding the binary.
//
// Missing-DLL handling: Windows pops a system dialog
//   "The code execution cannot proceed because libgmpxx.dll was not
//    found.  Reinstalling the program may fix this problem."
// before main() runs -- the OS does its own logging, no probe needed.

#include "pi/pi_chudnovsky.h"

int main() {
  const int retval = RunPiBenchmark("Windows, dynamically linked");
  system("pause");
  return retval;
}

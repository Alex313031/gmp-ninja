// Copyright (c) 2026 Alex313031
//
// Compute pi to ~1000 decimal digits via the Chudnovsky algorithm and
// time the calculation in microseconds.  Compiled once into a small
// static lib (//src/gmp-ninja/testapp/pi:pi_chudnovsky) that all four
// testapp executables (linux/win x static/shared) link against -- the
// .cc wrappers do nothing but call RunPiBenchmark with a label.
//
// Chudnovsky converges at ~14.181 decimal digits per term, so 34000
// bits (~10235 decimal digits) is reached in ~715 terms.  Roughly
// 50-200 ms on a modern x86_64; the timing is dominated by mpn-level
// multiplication/division, so a build with use_avx2=true should
// noticeably outpace one with only sse2 thanks to BMI2/AVX2-tuned asm
// in mpn/x86_64/coreihwl/.

#ifndef GMP_NINJA_TESTAPP_PI_PI_CHUDNOVSKY_H_
#define GMP_NINJA_TESTAPP_PI_PI_CHUDNOVSKY_H_

#if defined(_WIN32) || defined(_WIN64)
 #define WIN32_LEAN_AND_MEAN
 #include <windows.h>
 #include <tchar.h>
#endif

#include <string>

#include <gmp.h>
#include <gmpxx.h>

// 34000 bits ≈ 10235 decimal digits -- comfortably above the
// 10000-digit target (10000 * log2(10) ≈ 33219 bits) with headroom
// for accumulated rounding in the series sum.
inline constexpr unsigned int kPrecisionBits = 34000;

inline constexpr unsigned int kDigitsToPrint = 10000;

// Compute pi to the precision currently set as mpf default.  Caller is
// expected to have called mpf_set_default_prec(kPrecisionBits) first
// (RunPiBenchmark below does that).
mpf_class ChudnovskyPi();

// Format an mpf_class as a fixed-point decimal string with `digits`
// digits after the decimal point.
std::string FormatPi(const mpf_class& pi, unsigned int digits);

// Set precision, time ChudnovskyPi(), print result + elapsed micros,
// validate the first 50 digits against a known-good prefix.  Returns
// 0 on success, 1 if the validation fails.  `link_mode_label` is a
// short string identifying the link mode (e.g. "Linux ... static") --
// printed in the header so the four executables produce distinguishable
// output.
int RunPiBenchmark(const char* link_mode_label);

#endif  // GMP_NINJA_TESTAPP_PI_PI_CHUDNOVSKY_H_

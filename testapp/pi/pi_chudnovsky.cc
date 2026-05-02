// Copyright (c) 2026 Alex313031
//
// See pi_chudnovsky.h.

#include "pi_chudnovsky.h"

#include <chrono>
#include <cstdio>
#include <cstring>
#include <iostream>

mpf_class ChudnovskyPi() {
  // Each Chudnovsky term contributes ~14.181 decimal digits.  We pick
  // n_terms slightly above kDigitsToPrint/14 to guarantee convergence.
  const unsigned int n_terms = (kDigitsToPrint / 14) + 4;

  // M_0 = 1, L_0 = 13591409, X_0 = 1, S_0 = L_0.  All exact integers
  // initially; M and X grow rapidly so we keep them as mpf_class.
  mpf_class M(1);
  mpf_class L(13591409);
  mpf_class X(1);
  mpf_class S = L;

  // -640320^3 = -262537412640768000.  Doesn't fit in a 32-bit int, so
  // initialise via string.
  mpf_class neg_C3;
  mpf_set_str(neg_C3.get_mpf_t(), "-262537412640768000", 10);

  for (unsigned int k = 1; k < n_terms; ++k) {
    // M_k / M_{k-1} = (6k-5)(6k-4)(6k-3)(6k-2)(6k-1)(6k)
    //                / ((3k-2)(3k-1)(3k) * k^3)
    //
    // For 10000 digits we need k up to ~715, so the largest single
    // factor is 6*715 = 4290 -- still well within unsigned int.  We
    // multiply factor-by-factor into mpf_class to avoid overflowing
    // intermediate products (six such factors cubed could otherwise
    // exceed 2^64 at this k range).
    mpf_class num(6 * k - 5);
    num *= 6 * k - 4;
    num *= 6 * k - 3;
    num *= 6 * k - 2;
    num *= 6 * k - 1;
    num *= 6 * k;

    mpf_class denom(3 * k - 2);
    denom *= 3 * k - 1;
    denom *= 3 * k;
    denom *= k;
    denom *= k;
    denom *= k;

    M = M * num / denom;
    L += 545140134;
    X *= neg_C3;
    S += (M * L) / X;
  }

  // pi = 426880 * sqrt(10005) / S
  mpf_class sqrt10005;
  mpf_sqrt_ui(sqrt10005.get_mpf_t(), 10005);
  mpf_class pi = mpf_class(426880) * sqrt10005 / S;
  return pi;
}

std::string FormatPi(const mpf_class& pi, unsigned int digits) {
  mp_exp_t exp;
  // n_digits = digits+1 so we get the leading "3" plus `digits` past
  // the decimal point.
  char* raw = mpf_get_str(nullptr, &exp, 10, digits + 1, pi.get_mpf_t());
  std::string s(raw);
  // Free GMP-allocated buffer via the same allocator GMP used.
  void (*free_fn)(void*, size_t);
  mp_get_memory_functions(nullptr, nullptr, &free_fn);
  free_fn(raw, std::strlen(raw) + 1);
  // exp is the position of the decimal point in `s` (with leading
  // zeros stripped).  For pi (~3.14...), exp == 1 and s[0] == '3';
  // insert "." after position exp.
  if (static_cast<size_t>(exp) >= s.size()) {
    s.append(static_cast<size_t>(exp) - s.size(), '0');
  }
  if (exp <= 0) {
    s.insert(0, std::string(-exp, '0'));
    s.insert(0, "0.");
  } else {
    s.insert(static_cast<size_t>(exp), ".");
  }
  return s;
}

int RunPiBenchmark(const char* link_mode_label) {
  using clock = std::chrono::high_resolution_clock;

  mpf_set_default_prec(kPrecisionBits);

  std::cout << "\nGMP " << gmp_version << " (" << link_mode_label << ")\n"
            << "Computing Pi to " << kDigitsToPrint
            << " decimal digits at " << kPrecisionBits
            << " bits of internal precision via Chudnovsky algorithm...\n"
            << std::flush;

  const auto t0 = clock::now();
  const mpf_class pi = ChudnovskyPi();
  const auto t1 = clock::now();

  const auto micros =
      std::chrono::duration_cast<std::chrono::microseconds>(t1 - t0).count();
  std::cout << "\nElapsed execution time: " << micros << " microseconds"
            << std::endl;

  // Validate against the well-known value.  We format at the full
  // requested precision and check the prefix rather than re-formatting
  // at 50 digits, because mpf_get_str rounds at the requested
  // precision and the 50-digit-rounded form differs from the
  // 10000-digit truncated form ("...37511" vs. "...37510") in the
  // last position.  The full string isn't printed -- 10000 digits
  // overwhelms a console -- but it IS computed and a specific
  // 50-digit prefix must match for the run to be considered correct.
  const std::string s = FormatPi(pi, kDigitsToPrint);
  static constexpr const char* kExpectedPrefix =
      "3.14159265358979323846264338327950288419716939937510";
  if (s.compare(0, std::strlen(kExpectedPrefix), kExpectedPrefix) != 0) {
    std::cerr << "Result: INCORRECT (computed value does not match the "
                 "first 50 digits of pi)\n"
              << "  got:      " << s.substr(0, 52) << "\n"
              << "  expected: " << kExpectedPrefix << std::endl;
    return 1;
  }
  std::cout << "Result: CORRECT (verified against the first 50 digits "
               "of pi)" << std::endl;
  return 0;
}

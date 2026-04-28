# GNU Multi-Precision Library - GN/Ninja Build

A port of the [GMP](https://gmplib.org/) library to [GN](https://gn.googlesource.com/gn/+/refs/heads/main/README.md), [Ninja](https://ninja-build.org/) and [LLVM](https://llvm.org/),
specifically for making static/shared builds, primarily targeting Windows, but also Linux x64.

This library supports Windows 2000 - 11, another unique aspect of this repo: It can be used in legacy Win32 Projects (of which I have many, hence this port).

## Motivation
Stuff I tried that didn't work for building for 2000/XP/Vista, or didn't provide both static and dynamic libraries in a format I could use for my [PiCalc-Win](https://github.com/Alex313031/PiCalc-Win) project:  

The [make or CMAKE](https://gmplib.org/manual/Installing-GMP) steps via official MINGW [build instructions](https://gmplib.org/manual/Notes-for-Particular-Systems#Notes-for-Particular-Systems) or [these instructions](https://web.archive.org/web/20241107180606/https://rstudio-pubs-static.s3.amazonaws.com/493124_a46782f9253a4b8193595b6b2a037d58.html).  
The [vcpkg](https://vcpkg.io) package > https://vcpkg.io/en/package/gmp.  
This port to Visual Studio's CMAKE > https://github.com/gx/gmp.  
Even [this port](https://github.com/apotocki/gmp-win) to Visual Studio by [Alexander Pototskiy](https://github.com/apotocki) (I made a fork [here](https://github.com/Alex313031/gmp-win) too with changes for XP) was good but still not what I wanted.  

## Building

I have made a minimal, modified version configured specifically for compiling Win32 programs
for legacy Windows called [gn-legacy](https://github.com/Alex313031/gn-legacy).  
It can be used on Windows 7+ or Linux.

Really, it is a meta-build system. GN stands for "Generate Ninja" and can use __BUILD.gn__ files to
generate `.ninja` files. These are used by Ninja (the actual build system), to run the commands to compile it.  
The compiler itself is dependant on the host platform:  
On Linux, a special MinGW build I compiled on Ubuntu 24.04 to support legacy Windows and use static linkage is used.
On Windows, it simply uses an extracted toolchain from win32-devkit mentioned above.

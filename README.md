A port of the [GMP]](https://gmplib.org/) library to [GN](https://gn.googlesource.com/gn/+/refs/heads/main/README.md), [Ninja](https://ninja-build.org/) and [LLVM](https://llvm.org/), specifically for making static .libs and .dlls for Windows that work on Windows XP and above.

Stuff I tried that didn't work for building for XP/Vista, or didn't provide both static and dynamic libraries in a format I could use for my [PiCalc-Win](https://github.com/Alex313031/PiCalc-Win) project:  

make or CMAKE via official MINGW [build instructions](https://rstudio-pubs-static.s3.amazonaws.com/493124_a46782f9253a4b8193595b6b2a037d58.html) or [these instructions](https://web.archive.org/web/20241107180606/https://rstudio-pubs-static.s3.amazonaws.com/493124_a46782f9253a4b8193595b6b2a037d58.html).  
The [vcpkg](https://vcpkg.io) package > https://vcpkg.io/en/package/gmp.  
This port to Visual Studio's CMAKE > https://github.com/gx/gmp.  
Even [this port](https://github.com/apotocki/gmp-win) to Visual Studio by [Alexander Pototskiy](https://github.com/apotocki) (I made a fork [here](https://github.com/Alex313031/gmp-win) too with changes for XP) was good but still not what I wanted.  

## Building

### Version

6.3.0
Built with Ninja 1.14 and LLVM 19

#ifndef __UNISTD_H_17CD2BD1_839A_4E25_97C7_DE9544B8B59C__
#define __UNISTD_H_17CD2BD1_839A_4E25_97C7_DE9544B8B59C__

#ifndef _WIN32

#pragma message("This unistd.h implementation is for Windows only!")

#else /* _WIN32 */

#ifndef _UNISTD_H
#define _UNISTD_H    1

/* This file intended to serve as a drop-in replacement for
 *  unistd.h on Windows.
 *  Please add functionality as neeeded.
 *  Original file from: http://stackoverflow.com/a/826027
 *  and https://gist.github.com/mbikovitsky/39224cf521bfea7eabe9
 *  and https://github.com/Haivision/srt/blob/5138f37d45b5724e379e27760dc7e30bcfa110f1/common/win/unistd.h
 */

#include <stdlib.h>
#include <stdint.h>
#include <io.h>
//#include <getopt.h> /* getopt at: https://gist.github.com/ashelly/7776712 */ https://gist.github.com/bikerm16/1b75e2dd20d839dcea58
#include <process.h> /* for getpid() and the exec..() family */
#include <direct.h> /* for _getcwd() and _chdir() */

#ifndef srandom
#define srandom srand
#endif // srandom

#ifndef random
#define random rand
#endif // random

/* Values for the second argument to access.
   These may be OR'd together.  */
#ifndef R_OK
#define R_OK    4       /* Test for read permission.  */
#endif // R_OK

#ifndef W_OK
#define W_OK    2       /* Test for write permission.  */
#endif // W_OK

#ifndef X_OK
#define X_OK    R_OK    /* execute permission - unsupported in Windows,
                           use R_OK instead. */
#endif // X_OK

#ifndef F_OK
#define F_OK    0       /* Test for existence.  */
#endif // F_OK

#ifndef access
#define access _access
#endif // 

#ifndef dup2
#define dup2 _dup2
#endif // dup2

#ifndef execve
#define execve _execve
#endif // execve

#ifndef ftruncate
#define ftruncate _chsize
#endif // ftruncate

#ifndef unlink
#define unlink _unlink
#endif // unlink

#ifndef fileno
#define fileno _fileno
#endif // fileno

#ifndef getcwd
#define getcwd _getcwd
#endif // getcwd

#ifndef chdir
#define chdir _chdir
#endif // chdir

#ifndef isatty
#define isatty _isatty
#endif // isatty

#ifndef lseek
#define lseek _lseek
#endif // lseek

/* read, write, and close are NOT being #defined here,
 * because while there are file handle specific versions for Windows,
 * they probably don't work for sockets.
 * You need to look at your app and consider whether
 * to call e.g. closesocket().
 */

#ifndef ssize_t
#define ssize_t int
#endif // ssize_t

#ifndef STDIN_FILENO
#define STDIN_FILENO 0
#endif // STDIN_FILENO

#ifndef STDOUT_FILENO
#define STDOUT_FILENO 1
#endif // STDOUT_FILENO

#ifndef STDERR_FILENO
#define STDERR_FILENO 2
#endif // STDERR_FILENO

/* should be in some equivalent to <sys/types.h> */
#ifndef int8_t
#ifndef __int8
typedef signed char int8_t;
#else
typedef __int8 int8_t;
#endif // __int8
#endif // int8_t

#if !defined(uint8_t)
typedef unsigned __int8 uint8_t;
#endif // uint8_t

#if !defined(int16_t)
typedef __int16 int16_t;
#endif // int16_t

#if !defined(uint16_t)
typedef unsigned __int16 uint16_t;
#endif // uint16_t

#if !defined(int32_t)
typedef __int32 int32_t;
#endif // int32_t

#if !defined(uint32_t)
typedef unsigned __int32 uint32_t;
#endif // uint32_t

#if !defined(int64_t)
typedef __int64 int64_t;
#endif // int64_t

#if !defined(uint64_t)
typedef unsigned __int64 uint64_t;
#endif // uint64_t

#endif /* _UNISTD_H  */

#endif /* _WIN32 */

#endif /* __UNISTD_H_17CD2BD1_839A_4E25_97C7_DE9544B8B59C__ */

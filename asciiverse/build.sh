#!/bin/sh
# Builds nsnake into out/ with upstream's Makefile. The compiler and the
# curses library come from the environment, so one script serves every
# target (see .github/workflows/release.yml):
#
#   asciiverse/build.sh                                        # Linux, macOS
#   LDFLAGS_PLATFORM="-static -s" asciiverse/build.sh          # Alpine, static
#   CXX=x86_64-w64-mingw32-g++ CC=x86_64-w64-mingw32-gcc \
#     PDCURSES=/path/to/PDCurses-3.9 EXE=.exe asciiverse/build.sh  # Windows
#
# For Windows the sources' <ncurses.h> becomes PDCurses' <curses.h>
# through a one-line header in out/pdshim.
set -eu
cd "$(dirname "$0")/.."
CXX="${CXX:-c++}"
CC="${CC:-cc}"
EXE="${EXE:-}"
CFLAGS_PLATFORM="${CFLAGS_PLATFORM:--O2}"
LDFLAGS_PLATFORM="${LDFLAGS_PLATFORM:-}"
mkdir -p out
find src deps -name '*.o' -exec rm -f {} +
if [ -n "${PDCURSES:-}" ]; then
  mkdir -p out/pdshim
  printf '#include <curses.h>\n' > out/pdshim/ncurses.h
  make -j"$(getconf _NPROCESSORS_ONLN 2>/dev/null || echo 2)" CXX="$CXX" CC="$CC" \
    CFLAGS_PLATFORM="$CFLAGS_PLATFORM -I$PDCURSES -I$PWD/out/pdshim" \
    LDFLAGS="$PDCURSES/wincon/pdcurses.a -static -s"
else
  make -j"$(getconf _NPROCESSORS_ONLN 2>/dev/null || echo 2)" CXX="$CXX" CC="$CC" \
    CFLAGS_PLATFORM="$CFLAGS_PLATFORM" LDFLAGS_PLATFORM="$LDFLAGS_PLATFORM"
fi
cp "bin/nsnake$EXE" "out/nsnake$EXE"
# the man page, with the date and version the Makefile's install fills in
sed -e "s|DATE|$(date +%b%Y)|g" -e "s|VERSION|$(sed -n 's/^VERSION *= *//p' Makefile)|g" \
  doc/man/nsnake.6 > out/nsnake.6
echo "built nsnake$EXE"

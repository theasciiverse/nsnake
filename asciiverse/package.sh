#!/bin/sh
# Packs the build into dist/nsnake-<target>.tar.gz (.zip for Windows) for
# av: the binary at the top, the bundled levels beside it in levels/ (av
# starts a title in its install folder, where nsnake looks for them), the
# man page, COPYING and README.md.
#
#   asciiverse/package.sh x86_64-unknown-linux-musl
set -eu
cd "$(dirname "$0")/.."
target="$1"
case "$target" in *windows*) exe=.exe ;; *) exe= ;; esac
stage=stage/nsnake
rm -rf "$stage" && mkdir -p "$stage" dist
cp "out/nsnake$exe" out/nsnake.6 COPYING README.md "$stage/"
cp -r levels "$stage/levels"
if [ -n "$exe" ]; then
  (cd "$stage" && zip -qr "../../dist/nsnake-$target.zip" .)
else
  tar -czf "dist/nsnake-$target.tar.gz" -C "$stage" .
fi
ls dist

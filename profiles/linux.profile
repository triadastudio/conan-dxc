[settings]
os=Linux
arch=x86_64
build_type=Release
compiler=clang
compiler.version=16
compiler.libcxx=libstdc++11
compiler.cppstd=17

[buildenv]
CC=/usr/bin/clang-16
CXX=/usr/bin/clang++-16

[conf]
tools.build:jobs=4

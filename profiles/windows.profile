[settings]
os=Windows
arch=x86_64
build_type=Release
compiler=clang
compiler.version=17
compiler.runtime=dynamic
compiler.cppstd=17

[conf]
tools.build:compiler_executables={"c": "clang-cl", "cpp": "clang-cl"}
tools.build:jobs=4

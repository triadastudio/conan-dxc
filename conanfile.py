from conan import ConanFile
from conan.tools import files, scm
from conan.errors import ConanInvalidConfiguration

import os


class DXCConan(ConanFile):
    name = "dxc"
    version = "1.8.2502"
    description = "DirectX Shader Compiler"
    license = "NCSA"
    topics = ("hlsl", "dxc", "compiler", "shader", "spirv")
    homepage = "https://github.com/microsoft/DirectXShaderCompiler"
    url = "https://github.com/triadastudio/conan-dxc"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True

    @property
    def _source_commit_or_tag(self):
        return "v1.8.2502"

    @property
    def _source_subfolder(self):
        return "source_subfolder"

    @property
    def _build_type(self):
        return "Release"

    @property
    def _source_dir(self):
        return os.path.join(self.source_folder, self._source_subfolder)

    def source(self):
        self.run(f"git clone https://github.com/microsoft/DirectXShaderCompiler.git {self._source_subfolder}")
        with files.chdir(self, self._source_subfolder):
            self.run(f"git checkout {self._source_commit_or_tag}")
            self.run("git submodule update --init --recursive")

    @property
    def _predefined_cmake_params_path(self):
        return os.path.join(self._source_dir, "cmake/caches/PredefinedParams.cmake")

    def build_windows(self):
        self.run("cmake . -B%s -A x64 -DCMAKE_BUILD_TYPE=%s -C %s" %
                 (self.build_folder, self._build_type, self._predefined_cmake_params_path), cwd=self._source_dir)
        self.run("cmake --build %s --target \"dxc\" --config Release" % self.build_folder )

    def build_linux(self):
        self.run("cmake . -B%s -GNinja -DCMAKE_BUILD_TYPE=%s -DCMAKE_C_COMPILER=clang-16 -DCMAKE_CXX_COMPILER=clang++-16 -C %s" %
                 (self.build_folder, self._build_type, self._predefined_cmake_params_path), cwd=self._source_dir)
        self.run("ninja -j 4")

    def build_macos(self):
        if self.settings.arch == "x86_64":
            self.run("cmake . -B%s -GNinja -DCMAKE_BUILD_TYPE=%s -DCMAKE_SYSTEM_PROCESSOR=x86_64 -C %s" %
                    (self.build_folder, self._build_type, self._predefined_cmake_params_path), cwd=self._source_dir)
        else:
            self.run("cmake . -B%s -GNinja -DCMAKE_BUILD_TYPE=%s -C %s" %
                    (self.build_folder, self._build_type, self._predefined_cmake_params_path), cwd=self._source_dir)
        self.run("ninja")

    def build(self):
        if self.settings.os == "Windows":
            self.build_windows()
        elif self.settings.os == "Linux":
            self.build_linux()
        elif self.settings.os == "Macos":
            self.build_macos()
        else:
            raise ConanInvalidConfiguration("Unsupported OS: %s" % self.settings.os)

    def package_copy(self, pattern, dst_dir, keep_path=False, src_path = None):
        if src_path is None:
           src_path = self.build_folder

        dst = os.path.join(self.package_folder, dst_dir)
        files.copy(self, pattern, src=src_path, dst=dst, keep_path=keep_path)

    def package(self):
        self.package_copy("*.h", "include", src_path=os.path.join(
            self._source_dir, "include", "dxc"), keep_path=True)

        if self.settings.os == "Windows":
            self.package_copy("Release/lib/dxcompiler.lib", "lib")
            self.package_copy("Release/bin/dxcompiler.dll", "bin")
            self.package_copy("Release/bin/dxc.exe", "bin")
        elif self.settings.os == "Linux":
            self.package_copy("lib/libdxcompiler.so*", "lib")
            self.package_copy("bin/dxc*", "bin")
        elif self.settings.os == "Macos":
            self.package_copy("lib/libdxcompiler.dylib*", "lib")
            self.package_copy("bin/dxc*", "bin")
        else:
            raise ConanInvalidConfiguration("Unsupported OS: %s" % self.settings.os)

    def package_info(self):
        self.cpp_info.libs = ["dxcompiler"]
        self.cpp_info.includedirs = ["include"]

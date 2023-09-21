from conan import ConanFile
from conan.tools import files, scm
from conan.errors import ConanInvalidConfiguration

import os


class DXCConan(ConanFile):
    name = "dxc"
    version = "1.7.2308"
    description = "DirectX Shader Compiler"
    license = "NCSA"
    topics = ("hlsl", "dxc", "compiler", "shader", "spirv")
    homepage = "https://github.com/microsoft/DirectXShaderCompiler"
    url = "https://github.com/triadastudio/conan-dxc"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True

    @property
    def _source_commit_or_tag(self):
        return "v1.7.2308"

    @property
    def _source_subfolder(self):
        return "source_subfolder"

    @property
    def _build_type(self):
        return "release"

    @property
    def _source_dir(self):
        return os.path.join(self.source_folder, self._source_subfolder)

    def source(self):
        git = scm.Git(self)
        clone_args = ['--depth', '1', '--recursive', '--branch', self._source_commit_or_tag]
        git.clone("https://github.com/microsoft/DirectXShaderCompiler.git", self._source_subfolder, args=clone_args )

    def build_windows(self):
        win_sdk_ver = "10.0.20348.0"

        self.run("call utils/hct/hctstart.cmd . %s && "
                 "call utils/hct/hctbuild.cmd -x64 -%s -dxc-cmake-system-version %s -spirv -show-cmake-log"
                 % (self.build_folder, self._build_type, win_sdk_ver), cwd=self._source_dir)

    @property
    def _predefined_cmake_params_path(self):
        return os.path.join(self._source_dir, "cmake/caches/PredefinedParams.cmake")

    def build_linux(self):
        self.run("cmake . -B%s -GNinja -DCMAKE_BUILD_TYPE=%s -DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++ -C %s" %
                 (self.build_folder, self._build_type, self._predefined_cmake_params_path), cwd=self._source_dir)
        self.run("ninja -j 4")

    def build_macos(self):
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
            self.package_copy("bin/dxc", "bin")
        elif self.settings.os == "Macos":
            self.package_copy("lib/libdxcompiler.dylib*", "lib")
            self.package_copy("bin/dxc", "bin")
        else:
            raise ConanInvalidConfiguration("Unsupported OS: %s" % self.settings.os)

    def package_info(self):
        self.cpp_info.libs = ["dxcompiler"]
        self.cpp_info.includedirs = ["include"]

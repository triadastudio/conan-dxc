from conans import ConanFile, CMake, tools
from conans.errors import ConanInvalidConfiguration
import os


class DXCConan(ConanFile):
    name = "dxc"
    version = "1.6.2112"
    description = "DirectX Shader Compiler"
    license = "NCSA"
    topics = ("hlsl", "dxc", "compiler", "shader", "spirv")
    homepage = "https://github.com/microsoft/DirectXShaderCompiler"
    url = "https://github.com/triadastudio/conan-dxc"
    settings = "os", "arch", "compiler", "build_type"
    generators = "cmake"
    no_copy_source = True

    @property
    def _source_commit_or_tag(self):
        return "v1.6.2112"

    @property
    def _source_subfolder(self):
        return "source_subfolder"

    @property
    def _source_dir(self):
        return os.path.join(self.source_folder, self._source_subfolder)

    def build_requirements(self):
        self.build_requires("ninja/1.10.2")

    def configure(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def source(self):
        git = tools.Git(folder=self._source_subfolder)
        git.clone("https://github.com/microsoft/DirectXShaderCompiler.git",
                  self._source_commit_or_tag, shallow=True)
        git.checkout_submodules("recursive")

    def build_windows(self):
        win_sdk_ver = "10.0.20348.0"
        self.run("call utils/hct/hctstart.cmd . %s && "
                 "call utils/hct/hctbuild.cmd -x64 -%s -dxc-cmake-system-version %s -spirv -show-cmake-log"
                 % (self.build_folder, self.settings.build_type, win_sdk_ver), cwd=self._source_dir)

    @property
    def _predefined_cmake_params_path(self):
        return os.path.join(self._source_dir, "cmake/caches/PredefinedParams.cmake")

    def build_linux(self):
        self.run("cmake . -B%s -GNinja -DCMAKE_BUILD_TYPE=%s -DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++ -C %s" %
                 (self.build_folder, self.settings.build_type, self._predefined_cmake_params_path), cwd=self._source_dir)
        self.run("ninja -j 4")

    def build_macos(self):
        self.run("cmake . -B%s -GNinja -DCMAKE_BUILD_TYPE=%s -C %s" %
                 (self.build_folder, self.settings.build_type, self._predefined_cmake_params_path), cwd=self._source_dir)
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

    def package(self):
        self.copy("*.h", dst="include",
                  src=os.path.join(self._source_dir, "include", "dxc"))

        if self.settings.os == "Windows":
            self.copy("Release/lib/dxcompiler.lib", dst="lib", keep_path=False)
            self.copy("Release/bin/dxcompiler.dll", dst="bin", keep_path=False)
            self.copy("Release/bin/dxc.exe", dst="bin", keep_path=False)
        elif self.settings.os == "Linux":
            self.copy("lib/libdxcompiler.so*", dst="lib", keep_path=False)
            self.copy("bin/dxc", dst="bin", keep_path=False)
        elif self.settings.os == "Macos":
            self.copy("lib/libdxcompiler.dylib*", dst="lib", keep_path=False)
            self.copy("bin/dxc", dst="bin", keep_path=False)
        else:
            raise ConanInvalidConfiguration("Unsupported OS: %s" % self.settings.os)

    def package_info(self):
        self.cpp_info.names["cmake_find_package"] = "dxc"
        self.cpp_info.names["cmake_find_package_multi"] = "dxc"
        self.cpp_info.names["pkg_config"] = "dxc"
        self.cpp_info.libs = ["dxcompiler"]
        self.cpp_info.includedirs = ["include"]

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import copy
from conan.tools.scm import Git

import os

required_conan_version = ">=2.0.9"


class DXCConan(ConanFile):
    name = "dxc"
    version = "1.9.2602"
    description = "DirectX Shader Compiler"
    license = "NCSA"
    topics = ("hlsl", "dxc", "compiler", "shader", "spirv")
    homepage = "https://github.com/microsoft/DirectXShaderCompiler"
    url = "https://github.com/triadastudio/conan-dxc"
    package_type = "shared-library"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True

    def layout(self):
        cmake_layout(self, generator="Ninja", src_folder="src")

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.27 <4]")
        self.tool_requires("ninja/[>=1.11 <2]")

    def validate(self):
        if str(self.settings.os) not in ("Windows", "Linux", "Macos"):
            raise ConanInvalidConfiguration(f"Unsupported OS: {self.settings.os}")

    def package_id(self):
        # dxcompiler exposes COM-style vtable interfaces with no std:: types crossing the ABI,
        # so C++ standard doesn't matter to consumers
        self.info.settings.rm_safe("compiler.cppstd")

    def source(self):
        git = Git(self)
        git.clone(url="https://github.com/microsoft/DirectXShaderCompiler.git",
                  target=".",
                  args=["--depth", "1", "--branch", f"v{self.version}",
                        "--recurse-submodules", "--shallow-submodules"])

    def generate(self):
        tc = CMakeToolchain(self, generator="Ninja")
        if self.settings.os == "Windows":
            # LLVM-3.7-era code is extremely warning-noisy under clang-cl
            tc.extra_cflags.append("-w")
            tc.extra_cxxflags.append("-w")
            tc.cache_variables["CMAKE_INTERPROCEDURAL_OPTIMIZATION"] = True
        tc.generate()

    def build(self):
        cmake = CMake(self)
        predefined_params = os.path.join(self.source_folder, "cmake", "caches", "PredefinedParams.cmake")
        cmake.configure(cli_args=["-Wno-dev", f'-C "{predefined_params}"'])
        # dxc depends on dxcompiler, so this single target builds everything package() needs
        cmake.build(target="dxc")

    def package(self):
        copy(self, "LICENSE.TXT", src=self.source_folder,
             dst=os.path.join(self.package_folder, "licenses"))
        copy(self, "*.h",
             src=os.path.join(self.source_folder, "include", "dxc"),
             dst=os.path.join(self.package_folder, "include"), keep_path=True)

        lib_dst = os.path.join(self.package_folder, "lib")
        bin_dst = os.path.join(self.package_folder, "bin")
        if self.settings.os == "Windows":
            copy(self, "lib/dxcompiler.lib", src=self.build_folder, dst=lib_dst, keep_path=False)
            copy(self, "bin/dxcompiler.dll", src=self.build_folder, dst=bin_dst, keep_path=False)
            copy(self, "bin/dxc.exe", src=self.build_folder, dst=bin_dst, keep_path=False)
        elif self.settings.os == "Linux":
            copy(self, "lib/libdxcompiler.so*", src=self.build_folder, dst=lib_dst, keep_path=False)
            copy(self, "bin/dxc*", src=self.build_folder, dst=bin_dst, keep_path=False)
        else:  # Macos, guaranteed by validate()
            copy(self, "lib/libdxcompiler.dylib*", src=self.build_folder, dst=lib_dst, keep_path=False)
            copy(self, "bin/dxc*", src=self.build_folder, dst=bin_dst, keep_path=False)

    def package_info(self):
        self.cpp_info.libs = ["dxcompiler"]

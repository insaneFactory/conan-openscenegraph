from conans import ConanFile, CMake, tools
import os


class OpenscenegraphConan(ConanFile):
    name = "openscenegraph"
    version = "3.6.4"
    description = "OpenSceneGraph is an open source high performance 3D graphics toolkit"
    topics = ("conan", "openscenegraph", "graphics")
    url = "https://github.com/bincrafters/conan-openscenegraph"
    homepage = "https://github.com/openscenegraph/OpenSceneGraph"
    author = "Bincrafters <bincrafters@gmail.com>"
    license = "MIT"
    exports = ["LICENSE.md"]
    exports_sources = ["CMakeLists.txt"]
    short_paths = True
    generators = "cmake"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "build_osg_applications": [True, False],
        "build_osg_plugins_by_default": [True, False],
        "build_osg_examples": [True, False],
        "dynamic_openthreads": [True, False]
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "build_osg_applications": False,
        "build_osg_plugins_by_default": False,
        "build_osg_examples": False,
        "dynamic_openthreads": True
    }
    _source_subfolder = "source_subfolder"
    _build_subfolder = "build_subfolder"

    requires = (
        "zlib/1.2.11",
        "freetype/2.10.1",
        "libjpeg/9c",
        "libxml2/2.9.9",
        "libcurl/7.66.0@bincrafters/stable",
        "libpng/1.6.37",
        "libtiff/4.0.9",
        "sdl2/2.0.10@bincrafters/stable",
        "jasper/2.0.14",
        "cairo/1.17.2@bincrafters/stable",
        # "openblas/0.2.20@conan/stable", Removed until openblas is in conan center
    )

    def requirements(self):
        if self.settings.os != "Windows":
            self.requires("asio/1.12.0@bincrafters/stable")

    def system_requirements(self):
        if tools.os_info.is_linux:
            if tools.os_info.with_apt:
                installer = tools.SystemPackageTool()
                if self.settings.arch == "x86" and tools.detected_architecture() == "x86_64":
                    installer.install("gcc-multilib")
                    installer.install("libx11-dev:i386")
                    installer.install("libgl1-mesa-dev:i386")
                    installer.install("libglu1-mesa-dev:i386")
                    installer.install("libegl1-mesa-dev:i386")
                    installer.install("libgtk2.0-dev:i386")
                    installer.install("libpoppler-glib-dev:i386")
                else:
                    installer.install("libx11-dev")
                    installer.install("libgl1-mesa-dev")
                    installer.install("libglu1-mesa-dev")
                    installer.install("libegl1-mesa-dev")
                    installer.install("libgtk2.0-dev")
                    installer.install("libpoppler-glib-dev")
            elif tools.os_info.with_yum:
                installer = tools.SystemPackageTool()
                if self.settings.arch == "x86" and tools.detected_architecture() == "x86_64":
                    installer.install("glibmm24.i686")
                    installer.install("glibc-devel.i686")
                    installer.install("libGLU-devel.i686")
                else:
                    installer.install("libGLU-devel")
            else:
                self.output.warn("Could not determine Linux package manager, skipping system requirements installation.")


    def config_options(self):
        if self.settings.os == 'Windows':
            del self.options.fPIC

    def source(self):
        prefix = "OpenSceneGraph"
        sha256 = "81394d1b484c631028b85d21c5535280c21bbd911cb058e8746c87e93e7b9d33"
        tools.get("{0}/archive/{1}-{2}.tar.gz".format(self.homepage, prefix,self.version), sha256=sha256)
        extracted_dir = "{}-{}-".format(prefix, prefix) + self.version
        os.rename(extracted_dir, self._source_subfolder)

    def _configure_cmake(self):
        cmake = CMake(self)
        cmake.definitions["BUILD_OSG_APPLICATIONS"] = self.options.build_osg_applications
        cmake.definitions["DYNAMIC_OPENSCENEGRAPH"] = self.options.shared
        cmake.definitions["BUILD_OSG_PLUGINS_BY_DEFAULT"] = self.options.build_osg_plugins_by_default
        cmake.definitions['BUILD_OSG_EXAMPLES'] = self.options.build_osg_examples
        cmake.definitions["DYNAMIC_OPENTHREADS"] = self.options.dynamic_openthreads

        # Freetype
        freetypeLibs = self.deps_cpp_info["freetype"].libs
        if self.options["freetype"].with_png:
            freetypeLibs.extend(self.deps_cpp_info["libpng"].libs)
        if self.options["freetype"].with_zlib:
            freetypeLibs.extend(self.deps_cpp_info["zlib"].libs)
        if self.options["freetype"].with_bzip2:
            freetypeLibs.extend(self.deps_cpp_info["bzip2"].libs)
        self.output.info("Freetype libs: " + str(freetypeLibs))
        cmake.definitions["FREETYPE_LIBRARY"] = ";".join(freetypeLibs)
        
        # Jasper
        jasperLibs = self.deps_cpp_info["jasper"].libs
        if self.options["jasper"].jpegturbo:
            jasperLibs.extend(self.deps_cpp_info["libjpeg-turbo"].libs)
        else:
            jasperLibs.extend(self.deps_cpp_info["libjpeg"].libs)
        self.output.info("Jasper libs: " + str(jasperLibs))
        cmake.definitions["JASPER_LIBRARY"] = ";".join(jasperLibs)
        cmake.definitions["JASPER_INCLUDE_DIR"] = ";".join(self.deps_cpp_info["jasper"].includedirs)
        cmake.definitions["JASPER_FOUND"] = True
        
        # Cairo
        cmake.definitions["CAIRO_INCLUDE_DIRS"] = ";".join(self.deps_cpp_info["cairo"].includedirs)
        cmake.definitions["CAIRO_LIBRARY_DIRS"] = ";".join(self.deps_cpp_info["cairo"].libdirs)
        cmake.definitions["CAIRO_LIBRARIES"] = ";".join(self.deps_cpp_info["cairo"].libs)

        if self.settings.compiler == "Visual Studio":
            cmake.definitions['BUILD_WITH_STATIC_CRT']= "MT" in str(self.settings.compiler.runtime)

        cmake.configure()
        return cmake

    def build(self):
        cmake = self._configure_cmake()
        cmake.build()
        cmake.install()

    def package(self):
        self.copy(pattern="LICENSE*", dst="licenses", src=self._source_subfolder)

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
        if self.settings.os == "Linux":
            self.cpp_info.libs.append("rt")
        if not self.options.shared:
            self.cpp_info.defines.append("OSG_LIBRARY_STATIC=1")

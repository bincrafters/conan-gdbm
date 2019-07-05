# -*- coding: utf-8 -*-

import glob
import os

from conans import ConanFile, AutoToolsBuildEnvironment, tools
from conans.errors import ConanInvalidConfiguration


class GdbmConan(ConanFile):
    name = "gdbm"
    version = "1.18.1"
    description = ("gdbm is a library of database functions that uses "
                   "extensible hashing and work similar to "
                   "the standard UNIX dbm. "
                   "These routines are provided to a programmer needing "
                   "to create and manipulate a hashed database.")
    topics = ("conan", "gdbm", "dbm", "hash", "database")
    url = "https://github.com/bincrafters/conan-gdbm"
    homepage = "https://www.gnu.org.ua/software/gdbm/gdbm.html"
    author = "Bincrafters <bincrafters@gmail.com>"
    license = "GPL-3.0"
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "libiconv": [True, False],
        "readline": [True, False],
        "libgdbm_compat": [True, False],
        "gdbmtool_debug": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "libiconv": True,
        "readline": True,
        "libgdbm_compat": True,
        "gdbmtool_debug": True,
    }
    _autotools = None

    @property
    def _source_subfolder(self):
        return "source_subfolder"

    def configure(self):
        if self.settings.os == "Windows":
            raise ConanInvalidConfiguration("gdbm is not supported on Windows.")
        del self.settings.compiler.libcxx

    def requirements(self):
        if self.options.libiconv:
            self.requires("libiconv/1.15@bincrafters/stable")
        if self.options.readline:
            self.requires("readline/7.0@bincrafters/stable")

    def build_requirements(self):
        self.build_requires("bison_installer/3.3.2@bincrafters/stable")
        self.build_requires("flex_installer/2.6.4@bincrafters/stable")

    def source(self):
        filename = "{}-{}.tar.gz".format(self.name, self.version)
        url = "https://mirrors.tripadvisor.com/gnu/{}/{}".format(self.name, filename)
        sha256 = "86e613527e5dba544e73208f42b78b7c022d4fa5a6d5498bf18c8d6f745b91dc"
        tools.get(url, sha256=sha256)
        extracted_dir = "{}-{}".format(self.name, self.version)
        os.rename(extracted_dir, self._source_subfolder)

    def _configure_autotools(self):
        if not self._autotools:
            conf_args = [
                "--enable-debug" if self.settings.build_type == "Debug" else "--disable-debug",
                "--with-readline" if self.options.readline else "--without-readline",
                "--with-libintl-prefix"
            ]

            if self.options.libiconv:
                conf_args.append("--with-libiconv-prefix={}".format(self.deps_cpp_info["libiconv"].lib_paths[0]))

            if self.options.shared:
                conf_args.append("--disable-static")
                conf_args.append("--enable-shared")
                conf_args.append("--disable-rpaths")
            else:
                conf_args.append("--enable-static")
                conf_args.append("--disable-shared")
                conf_args.append("--with-pic" if self.options.fPIC
                                else "--without-pic")

            if self.options.libgdbm_compat:
                conf_args.append("--enable-libgdbm-compat")

            if self.options.gdbmtool_debug:
                conf_args.append("--enable-gdbmtool-debug")

            self._autotools = AutoToolsBuildEnvironment(self)
            self._autotools.configure(args=conf_args)
        return self._autotools

    def build(self):
        with tools.chdir(self._source_subfolder):
            autotools = self._configure_autotools()
            with tools.chdir("src"):
                autotools.make(args=["maintainer-clean-generic"])
            autotools.make()

    def package(self):
        self.copy("COPYING", src=self._source_subfolder, dst="licenses")
        with tools.chdir(self._source_subfolder):
            autotools = self._configure_autotools()
            autotools.install()
        with tools.chdir(os.path.join(self.package_folder, "lib")):
            for filename in glob.glob("*.la"):
                os.unlink(filename)
        tools.rmdir(os.path.join(self.package_folder, "share"))

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)

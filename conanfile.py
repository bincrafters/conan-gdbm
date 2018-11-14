# -*- coding: utf-8 -*-

from conans import ConanFile, AutoToolsBuildEnvironment, tools
from conans.tools import get_env
import os
import tempfile


class GdbmConan(ConanFile):
    name = "gdbm"
    version = "1.18.1"
    description = "gdbm is a library of database functions that uses extensible hashing and work similar to the standard UNIX dbm. These routines are provided to a programmer needing to create and manipulate a hashed database."
    topics = ("conan", "gdbm", "dbm", "hash", "database")
    url = "https://github.com/bincrafters/conan-gdbm"
    homepage = "https://www.gnu.org.ua/software/gdbm/gdbm.html"
    author = "Bincrafters <bincrafters@gmail.com>"
    license = "GPL-3.0"
    settings = "os", "compiler", "build_type", "arch"
    no_copy_source = True
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "libiconv": [True, False],
        "readline": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "libiconv": True,
        "readline": True,
    }
    _source_subfolder = "sources"

    def config_options(self):
        del self.settings.compiler.libcxx
        if self.options.shared:
            del self.options.fPIC

    def requirements(self):
        if self.options.libiconv:
            self.requires("libiconv/1.15@bincrafters/stable")
        if self.options.readline:
            self.requires("readline/7.0@bincrafters/stable")

    def build_requirements(self):
        # requirements for gdbmtool-debug
        self.build_requires("bison_installer/3.3.2@bincrafters/stable")
        self.build_requires("flex_installer/2.6.4@bincrafters/stable")

    def source(self):
        filename = "{}-{}.tar.gz".format(self.name, self.version)
        url = "https://mirrors.tripadvisor.com/gnu/{}/{}".format(self.name, filename)
        sha256 = "86e613527e5dba544e73208f42b78b7c022d4fa5a6d5498bf18c8d6f745b91dc"

        dlfilepath = os.path.join(tempfile.gettempdir(), filename)
        if os.path.exists(dlfilepath) and not get_env("GDBM_FORCE_DOWNLOAD", False):
            self.output.info("Skipping download. Using cached {}".format(dlfilepath))
        else:
            self.output.info("Downloading {} from {}".format(self.name, url))
            tools.download(url, dlfilepath)
        tools.check_sha256(dlfilepath, sha256)
        tools.untargz(dlfilepath)

        extracted_dir = "{}-{}".format(self.name, self.version)
        os.rename(extracted_dir, self._source_subfolder)

        os.remove(os.path.join(self._source_subfolder, "src", "gram.c"))

    def build(self):
        conf_args = [
            "--enable-debug" if self.settings.build_type == "Debug" else "--disable-debug",
            "--enable-gdbmtool-debug",
            "--disable-static" if self.options.shared else "--enable-static",
            "--enable-shared" if self.options.shared else "--disable-shared",
            "--disable-static" if self.options.shared else "--enable-static",
            "--with-libiconv-prefix" if self.options.libiconv else "--libiconv-prefix",
            "--with-libintl-prefix",  # if self.options.libintl else "--libintl-prefix",
            "--with-readline" if self.options.readline else "--without-readline",
        ]
        if not self.options.shared:
            conf_args.append("--with-pic" if self.options.fPIC else "--without-pic")

        autotools = AutoToolsBuildEnvironment(self)
        autotools.configure(configure_dir=os.path.join(self.source_folder, self._source_subfolder), args=conf_args)
        autotools.make(args=["V=1", "-j1", ])

    def package(self):
        with tools.chdir(self.build_folder):
            autotools = AutoToolsBuildEnvironment(self)
            autotools.install()
        self.copy("COPYING",
                  src=os.path.join(os.path.join(self.source_folder, self._source_subfolder)),
                  dst="licenses")

    def package_info(self):
        self.cpp_info.includedirs = ["include"]
        self.cpp_info.libs = ["gdbm"]

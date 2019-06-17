# -*- coding: utf-8 -*-

from conans import ConanFile, AutoToolsBuildEnvironment, tools
import os


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
    no_copy_source = True
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

    # Custom attributes for Bincrafters recipe conventions
    _source_subfolder = "source_subfolder"
    _build_subfolder = "build_subfolder"

    def config_options(self):
        del self.settings.compiler.libcxx
        # TODO: probably has to remove fPIC if MSVC too (which currently won't
        # work due to readline)
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
        tools.get(url, sha256=sha256)

        extracted_dir = "{}-{}".format(self.name, self.version)
        os.rename(extracted_dir, self._source_subfolder)

        if self.options.gdbmtool_debug:
            self.output.warn("Removing files similar to calling "
                             "`make -C src maintainer-clean-generic` "
                             " for enable-gdbmtool-debug to take effect")
            # Equivalent to `make -C src maintainer-clean-generic` needed
            _del_files = ['gram.c', 'lex.c', 'gdbm.h', 'gram.h']
            for _f in _del_files:
                try:
                    os.remove(os.path.join(self._source_subfolder, "src", _f))
                except FileNotFoundError:
                    pass

    def build(self):
        conf_args = [
            "--disable-dependency-tracking",  # Speeds up one-time builds
            "--enable-debug" if self.settings.build_type == "Debug" else "--disable-debug",
            "--with-libiconv-prefix" if self.options.libiconv else "--libiconv-prefix",
            "--with-libintl-prefix",  # if self.options.libintl else "--libintl-prefix",
            "--with-readline" if self.options.readline else "--without-readline",
        ]

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

        conf_dir = os.path.join(self.source_folder, self._source_subfolder)
        autotools = AutoToolsBuildEnvironment(self)
        autotools.configure(configure_dir=conf_dir, args=conf_args)
        autotools.make(args=["V=1"])

    def package(self):
        with tools.chdir(self.build_folder):
            autotools = AutoToolsBuildEnvironment(self)
            autotools.install()
        self.copy("COPYING",
                  src=os.path.join(os.path.join(self.source_folder,
                                                self._source_subfolder)),
                  dst="licenses")

    def package_info(self):
        self.cpp_info.includedirs = ["include"]
        self.cpp_info.libs = tools.collect_libs(self)

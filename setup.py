#!/usr/bin/env python

import os.path
import subprocess
import sys

import setuptools


class BuildVirtualEnvironment(setuptools.Command):
    """Custom setup.py command which builds the virtual environment."""

    description = "Build a venv containing `stacktester` dependencies."
    base_dir = os.path.abspath(os.path.normpath(os.path.join(__file__, "..")))
    user_options = []

    def _create_venv(self):
        """Actually create the environment, using `virtualenv`."""
        import virtualenv
        virtualenv.logger = virtualenv.Logger([])

        print "creating venv in %s" % self.venv_path

        virtualenv.create_environment(
            self.venv_path,
            site_packages=False,
            clear=True,
        )

    def _install_deps(self):
        """Install `stacktester` dependencies into the virtual environment."""
        print "installing required dependencies into %s" % self.venv_path
        subprocess.call([
            "pip",
            "install",
            "--upgrade",
            "-E",
            self.venv_path,
            "-r",
            self.pip_req_path,
        ])

    def _install_stacktester(self):
        """Install `stacktester` itself into the virtual environment."""
        print "installing Stacktester into %s" % self.venv_path
        subprocess.call([
            "pip",
            "install",
            "-E",
            self.venv_path,
            self.base_dir,
        ])

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        """Build the virtual environment."""
        self.venv_path = os.path.join(self.base_dir, ".venv")
        self.pip_req_path = os.path.join(self.base_dir, ".pip-requires")
        self._create_venv()
        self._install_deps()
        self._install_stacktester()


setuptools.setup(
    name="stacktester",
    version="0.1",
    description="Testing suite for OpenStack software suite.",
    author="Rackspace Titan",
    packages=setuptools.find_packages(),
    setup_requires=["nose", "virtualenv", "pip", "glance"],
    scripts=["bin/stacktester"],
    test_suite="nose.collector",
    cmdclass={
        "venv": BuildVirtualEnvironment,
    },
)

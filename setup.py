'''
Build and distribute the Refactored Telegram!
'''

# core libraries
from codecs import open as c_open
import importlib.util
import logging
import os
import re
import subprocess
import sys

# third parties libraries
from setuptools import setup, find_packages
from distutils.command.sdist import sdist


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')
SETUP_LOGGER = logging.getLogger("refactored-telegram")

# classifications for this project - see
# https://pypi.python.org/pypi?%3Aaction=list_classifiers
CLASSIFIERS = [
    # project is in the alpha stage
    'Development Status :: 3 - Alpha',

    # MIT license
    'License :: OSI Approved :: MIT License',

    # python 3 supported
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.0',
    'Programming Language :: Python :: 3.1',
    'Programming Language :: Python :: 3.2',
    'Programming Language :: Python :: 3.3',
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',

    # palm trees are for entertainment
    'Topic :: Communications'
]

# prevent publishing - remove this for non-proprietary, non-example packages
BLACKLIST = ["register", "upload", "upload_docs"]
INTERSECTION = [val for val in sys.argv if val in BLACKLIST]
if INTERSECTION:
    message = f"Command(s) {INTERSECTION} are not allowed!"
    SETUP_LOGGER.critical(message)
    raise SystemExit(message)

# packages
PACKAGE_DIR = {"": "src"}
PACKAGE_DATA = {"": ["media/*"]}

# scripts
SCRIPTS = []

# the directory of this setup file
SETUP_DIR = os.path.abspath(os.path.dirname(__file__))

# source directory
SRC_DIR = os.path.join(SETUP_DIR, "src")

# where to find the version file, and where to write it if it does not exist
VERSION_FILE = os.path.join(SRC_DIR, "telegram", "version.py")
VERSION_DESCRIPTION = "Version of Refactored Telegram"

# installation dependencies
INSTALL_REQUIRES = c_open(os.path.join(SETUP_DIR, "requirements.txt")).readlines()


class DynamicVersionSDist(sdist):
    '''
    Custom sdist subclass which accepts optional arguments: version (string), or
    version bump (one of major, minor, or update). `--new-version` will use the
    whole string provided as the new version. `--version-bump` will cause a
    check on the latest annotated tag in the repository (using git describe) and
    attempt to increment the correct portion of the version. Both will
    write/overwrite the version.py file. If neither are provided, the existing
    version.py file will be used. And in the scenario where neither arguments
    were given AND no version.py file exists (or if the --dev flag is explicitly
    used), the repository will be checked for the latest annotated tag and
    create a "dev" version (ex. 1.0.0.dev8, which is 8 commits past the 1.0.0.
    version).
    '''

    # add our custom options
    user_options = sdist.user_options + [
        ("new-version=", None, "the value to be used when setting the version of the distribution package"),
        ("version-bump=", None, "one of 'major', 'minor', or 'update', defining the portion of the current version (as "
            "established by the latest git tag) to increment when setting the version of the distribution package"),
        ("dev-version", None, "flag this distribution to be versioned using a \"dev\" version (ex. 1.0.0.dev8 is 8 "
            "commits past the 1.0.0 version)")
    ]

    # add dev-version to the boolean options
    boolean_options = sdist.boolean_options + [
        "dev-version"
    ]

    # markdown is ok too
    READMES = sdist.READMES + ("README.md",)

    def initialize_options(self):
        '''
        Initialize our additional options.
        '''
        super().initialize_options()
        self.new_version = None
        self.version_bump = None
        self.dev_version = False

    def run(self):
        '''
        Override the version metadata before running the sdist.
        '''
        # --new-version takes top precedence
        if self.new_version:
            self.distribution.metadata.version = self.new_version
            self.write_version_file()
            super().run()
            return

        # --dev-version takes next precedence, when explicitly given
        if self.dev_version:
            self.create_dev_version()
            self.write_version_file()
            super().run()
            return

        # if --version-bump was provided, make sure it is one of the three
        # possible options and then kick off the process of attempting to
        # increment based on the git tag
        if self.version_bump:
            # check for valid value
            if self.version_bump.lower() not in ["major", "minor", "update"]:
                err_msg = f"The value provided to --version-bump ('{self.version_bump}') is invalid. It must be one " \
                           "of: 'major', 'minor', or 'update'"
                raise SystemExit(err_msg)

            # increment and run
            self.increment_version()
            self.write_version_file()
            super().run()
            return

        # if none of these options were provided, check if there is a version.py
        # file to read from
        if os.path.exists(VERSION_FILE):
            self.read_version_file()
            super().run()
            return

        # and lastly, by default, create a "dev" version - "dev" plus the number
        # of commits past the most recent tag
        self.create_dev_version()
        self.write_version_file()
        super().run()

    def create_dev_version(self):
        '''
        Read the current version from the latest annotated tag (long form) and
        create a "development" version representing a number of commits
        *forward* from the latest released/tagged version.

        However, there is a caveat to this one (especially since it is the fail
        over from *none* of our new options being provided). If the *current*
        tag represents the current commit (git describe returns 0 commits
        forward from the tag), then the version will be set as the current
        version. This means `python setup.py sdist` run on a commit that is the
        current tag will yield the package that represents *that* version.
        '''
        # get the git describe value
        SETUP_LOGGER.info("Determining the current version through git describe")
        proc = subprocess.Popen(["git", "describe", "--long"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate()

        # exit if we had trouble running the git describe
        if err:
            raise SystemExit(err)

        # parse the current version from the git descrbe
        git_desc = out.decode().strip()
        version_match = re.search(r"^(\d+)\.(\d+)\.(\d+)-(\d+)-.*", git_desc)
        version_list = list(map(int, version_match.groups()))
        SETUP_LOGGER.info("Current version: %d.%d.%d, with %d additional commits", *version_list)

        # if there are no commits forward of the tag, set the version as the
        # version from the tag
        if version_list[3] == 0:
            SETUP_LOGGER.info("Version for this distribution will be set to the value of the tag: %d.%d.%d",
                version_list[0], version_list[1], version_list[2])
            self.distribution.metadata.version = f"{version_list[0]}.{version_list[1]}.{version_list[2]}"
            return

        # otherwise, we need the number of commits since the last time a MAJOR
        # release was made
        proc = subprocess.Popen(["git", "rev-list", f"{version_list[0]}.0.0..HEAD", "--count"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate()

        # exit if we had trouble running the git rev-list
        if err:
            raise SystemExit(err)

        # assemble the dev version
        commit_count = int(out.decode().strip())
        dev_version = f"{version_list[0] + 1}.0.0.dev{commit_count}"
        self.distribution.metadata.version = dev_version


    def increment_version(self):
        '''
        Read the version from the latest annotated tag and attempt to incrememt
        the configured portion of the version. Then set that version in the
        metadata.
        '''
        # get the git describe value
        SETUP_LOGGER.info("Determining the current version through git describe")
        proc = subprocess.Popen(["git", "describe"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate()

        # error generally means there is no at least one annotated tag
        if err:
            raise SystemExit(err)

        # parse the current version from the git descrbe
        git_desc = out.decode().strip()
        version_match = re.search(r"^(\d+)\.(\d+)\.(\d+).*", git_desc)
        version_list = list(map(int, version_match.groups()))
        SETUP_LOGGER.info("Current version: %d.%d.%d, incrementing the %s portion", *version_list, self.version_bump)

        # incrememt the correct portion
        if self.version_bump == "major":
            version = (version_list[0] + 1, 0, 0)

        elif self.version_bump == "minor":
            version = (version_list[0], version_list[1] + 1, 0)

        else:
            version = (version_list[0], version_list[1], version_list[2] + 1)
        self.distribution.metadata.version = f"{version[0]}.{version[1]}.{version[2]}"

    def read_version_file(self):
        '''
        Read the version file and set the metadata to the value provided.
        '''
        spec = spec = importlib.util.spec_from_file_location("version_file", VERSION_FILE)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        SETUP_LOGGER.info("Version read from existing file: %s", mod.__version__)
        self.distribution.metadata.version = mod.__version__

    def write_version_file(self):
        '''
        Write (or overwrite) the version.py file in the top level package to
        reflect the version currently being packaged.
        '''
        SETUP_LOGGER.info("Opening %s and writing out version %s", VERSION_FILE, self.distribution.metadata.version)
        with open(VERSION_FILE, "w") as version_fd:
            version_fd.write(f"'''\n{VERSION_DESCRIPTION}\n'''\n\n__version__ = \"{self.distribution.metadata.version}\"\n")


# call setup with our project-specific values
setup(name='refactored-telegram',
      version=None,
      description='Program aimed at bringing back the telegram',
      author='Edward Petersen',
      author_email="edward.petersen@gmail.com",
      url='https://github.com/timepieces141/refactored-telegram',
      classifiers=CLASSIFIERS,
      license='MIT',
      package_dir=PACKAGE_DIR,
      packages=find_packages(SRC_DIR),
      package_data=PACKAGE_DATA,
      scripts=SCRIPTS,
      install_requires=INSTALL_REQUIRES,
      cmdclass={"sdist": DynamicVersionSDist}
      )

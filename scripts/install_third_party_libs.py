# Copyright 2019 The Oppia Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS-IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Installation script for Oppia third-party libraries."""
from __future__ import absolute_import  # pylint: disable=import-only-modules
from __future__ import unicode_literals  # pylint: disable=import-only-modules

import argparse
import fileinput
import os
import shutil
import subprocess

# These libraries need to be installed before running or importing any script.
TOOLS_DIR = os.path.join('..', 'oppia_tools')
# Download and install pyyaml.
if not os.path.exists(os.path.join(TOOLS_DIR, 'pyyaml-5.1.2')):
    subprocess.call([
        'pip', 'install', 'pyyaml==5.1.2', '--target',
        os.path.join(TOOLS_DIR, 'pyyaml-5.1.2')])

# Download and install future.
if not os.path.exists(os.path.join('third_party', 'future-0.17.1')):
    subprocess.call([
        'pip', 'install', 'future==0.17.1', '--target',
        os.path.join('third_party', 'future-0.17.1')])

# pylint: disable=wrong-import-position
# pylint: disable=wrong-import-order
import python_utils  # isort:skip

from . import build  # isort:skip
from . import common  # isort:skip
from . import install_third_party  # isort:skip
from . import pre_commit_hook  # isort:skip
from . import pre_push_hook  # isort:skip
from . import setup  # isort:skip
from . import setup_gae  # isort:skip
# pylint: enable=wrong-import-order
# pylint: enable=wrong-import-position

_PARSER = argparse.ArgumentParser(description="""
Installation script for Oppia third-party libraries.
""")

_PARSER.add_argument(
    '--nojsrepl',
    help='optional; if specified, skips installation of skulpt.',
    action='store_true')
_PARSER.add_argument(
    '--noskulpt',
    help='optional; if specified, skips installation of skulpt.',
    action='store_true')


def pip_install(package, version, install_path):
    """Installs third party libraries with pip.

    Args:
        package: str. The package name.
        version: str. The package version.
        install_path: str. The installation path for the package.
    """
    try:
        python_utils.PRINT('Checking if pip is installed on the local machine')
        # Importing pip just to check if its installed.
        import pip  #pylint: disable=unused-variable
    except ImportError:
        common.print_each_string_after_two_new_lines([
            'Pip is required to install Oppia dependencies, but pip wasn\'t '
            'found on your local machine.',
            'Please see \'Installing Oppia\' on the Oppia developers\' wiki '
            'page:'])

        os_info = os.uname()
        if os_info[0] == 'Darwin':
            python_utils.PRINT(
                'https://github.com/oppia/oppia/wiki/Installing-Oppia-%28Mac-'
                'OS%29')
        elif os_info[0] == 'Linux':
            python_utils.PRINT(
                'https://github.com/oppia/oppia/wiki/Installing-Oppia-%28Linux'
                '%29')
        else:
            python_utils.PRINT(
                'https://github.com/oppia/oppia/wiki/Installing-Oppia-%28'
                'Windows%29')
        raise Exception

    subprocess.check_call([
        'pip', 'install', '%s==%s' % (package, version), '--target',
        install_path])


def install_skulpt(parsed_args):
    """Download and install Skulpt. Skulpt is built using a Python script
    included within the Skulpt repository (skulpt.py). This script normally
    requires GitPython, however the patches to it below
    (with the fileinput.replace) lead to it no longer being required. The Python
    script is used to avoid having to manually recreate the Skulpt dist build
    process in install_third_party.py. Note that skulpt.py will issue a
    warning saying its dist command will not work properly without GitPython,
    but it does actually work due to the patches.
    """
    no_skulpt = parsed_args.nojsrepl or parsed_args.noskulpt

    python_utils.PRINT('Checking whether Skulpt is installed in third_party')
    if not os.path.exists(
            os.path.join(
                common.THIRD_PARTY_DIR,
                'static/skulpt-0.10.0')) and not no_skulpt:
        if not os.path.exists(
                os.path.join(common.OPPIA_TOOLS_DIR, 'skulpt-0.10.0')):
            python_utils.PRINT('Downloading Skulpt')
            skulpt_filepath = os.path.join(
                common.OPPIA_TOOLS_DIR, 'skulpt-0.10.0', 'skulpt', 'skulpt.py')
            os.chdir(common.OPPIA_TOOLS_DIR)
            os.mkdir('skulpt-0.10.0')
            os.chdir('skulpt-0.10.0')
            subprocess.call([
                'git', 'clone', 'https://github.com/skulpt/skulpt'])
            os.chdir('skulpt')

            # Use a specific Skulpt release.
            subprocess.call(['git', 'checkout', '0.10.0'])

            python_utils.PRINT('Compiling Skulpt')
            # The Skulpt setup function needs to be tweaked. It fails without
            # certain third party commands. These are only used for unit tests
            # and generating documentation and are not necessary when building
            # Skulpt.
            for line in fileinput.input(
                    files=[skulpt_filepath], inplace=True):
                # Inside this loop the STDOUT will be redirected to the file,
                # skulpt.py. The end='' is needed to avoid double line breaks.
                python_utils.PRINT(
                    line.replace('ret = test()', 'ret = 0'),
                    end='')

            for line in fileinput.input(
                    files=[skulpt_filepath], inplace=True):
                # Inside this loop the STDOUT will be redirected to the file,
                # skulpt.py. The end='' is needed to avoid double line breaks.
                python_utils.PRINT(
                    line.replace('  doc()', '  pass#doc()'),
                    end='')

            for line in fileinput.input(
                    files=[skulpt_filepath], inplace=True):
                # This and the next command disable unit and compressed unit
                # tests for the compressed distribution of Skulpt. These
                # tests don't work on some Ubuntu environments and cause a
                # libreadline dependency issue.
                python_utils.PRINT(
                    line.replace(
                        'ret = os.system(\'{0}',
                        'ret = 0 #os.system(\'{0}'),
                    end='')

            for line in fileinput.input(
                    files=[skulpt_filepath], inplace=True):
                python_utils.PRINT(
                    line.replace('ret = rununits(opt=True)', 'ret = 0'),
                    end='')

            subprocess.call(['python', skulpt_filepath, 'dist'])

            # Return to the Oppia root folder.
            os.chdir(common.CURR_DIR)

        # Move the build directory to the static resources folder.
        shutil.copytree(
            os.path.join(
                common.OPPIA_TOOLS_DIR, 'skulpt-0.10.0/skulpt/dist/'),
            os.path.join(common.THIRD_PARTY_DIR, 'static/skulpt-0.10.0'))


def maybe_install_dependencies(
        skip_installing_third_party_libs, run_minified_tests):
    """Parse additional command line arguments."""
    if skip_installing_third_party_libs is False:
        # Install third party dependencies.
        main(args=[])
        # Ensure that generated JS and CSS files are in place before running the
        # tests.
        python_utils.PRINT('Running build task with concatenation only')
        build.main(args=[])

    if run_minified_tests is True:
        python_utils.PRINT(
            'Running build task with concatenation and minification')
        build.main(args=['--prod_env'])


def ensure_pip_library_is_installed(package, version, path):
    """Installs the pip library after ensuring its not already installed.

    Args:
        package: str. The package name.
        version: str. The package version.
        path: str. The installation path for the package.
    """
    python_utils.PRINT(
        'Checking if %s is installed in %s' % (package, path))

    exact_lib_path = os.path.join(path, '%s-%s' % (package, version))
    if not os.path.exists(exact_lib_path):
        python_utils.PRINT('Installing %s' % package)
        pip_install(package, version, exact_lib_path)


def main(args=None):
    """Install third-party libraries for Oppia."""
    parsed_args = _PARSER.parse_args(args=args)

    setup.main(args=[])
    setup_gae.main(args=[])
    pip_dependencies = [
        ('pylint', '1.9.4', common.OPPIA_TOOLS_DIR),
        ('Pillow', '6.0.0', common.OPPIA_TOOLS_DIR),
        ('pylint-quotes', '0.1.8', common.OPPIA_TOOLS_DIR),
        ('webtest', '2.0.33', common.OPPIA_TOOLS_DIR),
        ('isort', '4.3.20', common.OPPIA_TOOLS_DIR),
        ('pycodestyle', '2.5.0', common.OPPIA_TOOLS_DIR),
        ('esprima', '4.0.1', common.OPPIA_TOOLS_DIR),
        ('browsermob-proxy', '0.8.0', common.OPPIA_TOOLS_DIR),
        ('selenium', '3.13.0', common.OPPIA_TOOLS_DIR),
        ('PyGithub', '1.43.7', common.OPPIA_TOOLS_DIR),
    ]

    for package, version, path in pip_dependencies:
        ensure_pip_library_is_installed(package, version, path)

    # Do a little surgery on configparser in pylint-1.9.4 to remove dependency
    # on ConverterMapping, which is not implemented in some Python
    # distributions.
    pylint_configparser_filepath = os.path.join(
        common.OPPIA_TOOLS_DIR, 'pylint-1.9.4', 'configparser.py')
    pylint_newlines = []
    with python_utils.open_file(pylint_configparser_filepath, 'r') as f:
        for line in f.readlines():
            if line.strip() == 'ConverterMapping,':
                continue
            if line.strip().endswith('"ConverterMapping",'):
                pylint_newlines.append(
                    line[:line.find('"ConverterMapping"')] + '\n')
            else:
                pylint_newlines.append(line)
    with python_utils.open_file(pylint_configparser_filepath, 'w+') as f:
        f.writelines(pylint_newlines)

    # Do similar surgery on configparser in pylint-quotes-0.1.8 to remove
    # dependency on ConverterMapping.
    pq_configparser_filepath = os.path.join(
        common.OPPIA_TOOLS_DIR, 'pylint-quotes-0.1.8', 'configparser.py')
    pq_newlines = []
    with python_utils.open_file(pq_configparser_filepath, 'r') as f:
        for line in f.readlines():
            if line.strip() == 'ConverterMapping,':
                continue
            if line.strip() == '"ConverterMapping",':
                continue
            pq_newlines.append(line)
    with python_utils.open_file(pq_configparser_filepath, 'w+') as f:
        f.writelines(pq_newlines)

    # Download and install required JS and zip files.
    python_utils.PRINT('Installing third-party JS libraries and zip files.')
    install_third_party.main(args=[])

    # Install third-party node modules needed for the build process.
    subprocess.call(['yarn'])

    install_skulpt(parsed_args)

    # Install pre-commit script.
    python_utils.PRINT('Installing pre-commit hook for git')
    pre_commit_hook.main(args=['--install'])

    # Install pre-push script.
    python_utils.PRINT('Installing pre-push hook for git')
    pre_push_hook.main(args=['--install'])


if __name__ == '__main__':
    main()

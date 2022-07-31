# ******************************************************************************
# Copyright (c) 2022 Julian Rüth <julian.rueth@fsfe.org>
#
# ipymuvue is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ipymuvue is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ipymuvue. If not, see <https://www.gnu.org/licenses/>.
# ******************************************************************************

from ipymuvue.version import version_info, __version__


def _jupyter_labextension_paths():
    r"""
    Called by JupyterLab to find out which JavaScript assets need to be copied.
    """
    # The command `jupyter labextension build` creates a package in
    # labextension/, see jupyterlab.outputDir in js/package.json
    # These files are copied to extensions/ipymuvue/ in
    # JupyterLab when this package is pip-installed.
    return [
        {
            "src": "labextension",
            "dest": "ipymuvue",
        }
    ]


def _jupyter_nbextension_paths():
    r"""
    Called by Jupyter Notebook to find out which JavaScript assets need to be copied.
    """
    # The command `yarn build:prod` creates JavaScript assets in nbextension/.
    # These files need to be copied to the nbextensions/ipymuvue/
    # directory in Jupyter Notebook. The entrypoint in these files is
    # extension.js.
    return [
        {
            "section": "notebook",
            "src": "nbextension",
            "dest": "ipymuvue",
            "require": "ipymuvue/extension",
        }
    ]

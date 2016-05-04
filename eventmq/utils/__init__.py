# This file is part of eventmq.
#
# eventmq is free software: you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 2.1 of the License, or (at your option)
# any later version.
#
# eventmq is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with eventmq.  If not, see <http://www.gnu.org/licenses/>.
"""
:mod:`utils` -- Utilities
=========================
This module contains a handful of utility classes to make dealing with things
like creating message more simple.

.. toctree ::
   :maxdepth: 2

   classes
   devices
   messages
   settings
   timeutils
"""


def random_characters():
    """
    Returns:
        str: some random characters of a specified length
    """
    import uuid

    # TODO: Pull out the random_chars function from eb.io code
    return str(uuid.uuid4())


def zero_index_cmp(a, b):
    """
    same as ``cmp`` but using the 0-index in a list as the compare value. Used
    when sorting the values in :attr:`router.Router.queues`.
    """
    return cmp(a[0], b[0])
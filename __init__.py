#!/usr/bin/env python
# vim:fileencoding=utf-8


__license__ = 'GPL v3'
__copyright__ = '2022, Nir Tzachar, <nir.tzachar@gmail.com>'

from calibre.customize import EditBookToolPlugin


class FSReadPlugin(EditBookToolPlugin):

    name = 'FSRead plugin'
    version = (1, 0, 0)
    author = 'Nir Tzachar'
    supported_platforms = ['windows', 'osx', 'linux']
    description = 'Flow State Read'
    minimum_calibre_version = (6, 0, 0)

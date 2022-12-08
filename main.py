#!/usr/bin/env python
# vim:fileencoding=utf-8


__license__ = 'GPL v3'
__copyright__ = '2022, Nir Tzachar, <nir.tzachar@gmail.com>'

from calibre import prepare_string_for_xml

# import re
from qt.core import QAction
# from css_parser.css import CSSRule

# The base class that all tools must inherit from
from calibre.gui2.tweak_book.plugin import Tool

# from calibre import force_unicode
from calibre.gui2 import error_dialog
# from calibre.ebooks.oeb.polish.container import OEB_DOCS, OEB_STYLES, serialize
from calibre.ebooks.oeb.base import etree

import math
import re


class FSRead(Tool):

    #: Set this to a unique name it will be used as a key
    name = 'fsread'

    #: If True the user can choose to place this tool in the plugins toolbar
    allowed_in_toolbar = True

    #: If True the user can choose to place this tool in the plugins menu
    allowed_in_menu = True

    allowed_tags = set([
        'div', 'p', 'i', 'span', 'li', 'dd', 'big', 'small', 'strong', 'samp', 'textarea', 'caption',
    ])

    disallowed_tags = set(['html', 'body', 'head', 'link', 'meta'])

    def create_action(self, for_toolbar=True):
        # Create an action, this will be added to the plugins toolbar and
        # the plugins menu
        ac = QAction(get_icons('images/icon.png'), 'FSRead', self.gui)  # noqa
        if not for_toolbar:
            # Register a keyboard shortcut for this toolbar action. We only
            # register it for the action created for the menu, not the toolbar,
            # to avoid a double trigger
            self.register_shortcut(ac, 'fsread-tool', default_keys=('Ctrl+Shift+Alt+F',))
        ac.triggered.connect(self.ask_user)
        return ac

    def ask_user(self):
        # Ensure any in progress editing the user is doing is present in the container
        self.boss.commit_all_editors_to_container()
        try:
            self.work()
        except Exception as e:
            # Something bad happened report the error to the user
            import traceback
            error_dialog(
                self.gui,
                'Failed to fsread fonts',
                'Failed to fsread fonts, click "Show details" for more info',
                det_msg=traceback.format_exc(),
                show=True,
            )
            # Revert to the saved restore point
            self.boss.revert_requested(self.boss.global_undo.previous_container)
        else:
            # Show the user what changes we have made, allowing her to
            # revert them if necessary
            self.boss.show_current_diff()
            # Update the editor UI to take into account all the changes we
            # have made
            self.boss.apply_container_update_to_gui()

    def work(self):
        self.boss.add_savepoint('Before: FSRead')

        container = self.current_container  # The book being edited as a container object
        files = list(container.manifest_items_of_type('application/xhtml+xml'))
        for page in files:
            parsed = container.parsed(page)
            replacements = []
            for element in parsed.iter(tag=etree.Element):
                text = element.text
                tag = element.tag
                if tag:
                    tag = tag.replace('{http://www.w3.org/1999/xhtml}', '')
                # if tag and tag in self.allowed_tags and text and len(text) > 0:
                if tag and tag not in self.disallowed_tags and text and len(text) > 0:
                    if tag != 'b':
                        text = self.fsread(text, 0.5)
                    # print(f'<{tag}>{text}</{tag}>')
                    new_element = etree.fromstring(f'<{tag}>{text}</{tag}>')
                    tail = get_tail(element)
                    if len(tail) > 0:
                        tail = etree.fromstring(f'<div>{self.fsread(tail, 0.5)}</div>')
                        new_element.append(tail)
                    replacements.append((element, new_element))
            for element, new_element in replacements:
                element = replace_with(
                    element,
                    new_element,
                )
            container.replace(page, parsed)

    def fsread(self, text, intensity):
        ans = text
        ans = re.sub(r'[\w`’]+', lambda t: self.style_word(t, intensity), ans)
        return replace_amp(ans)

    def style_word(self, word, intensity):
        # intensity should be between 0 and 1
        word = word.group(0)
        mid_point = math.ceil(len(word) * intensity)
        return f'<b>{prepare_string_for_xml(word[:mid_point])}</b>{prepare_string_for_xml(word[mid_point:])}'


def replace_with(item, replacement):
    '''
    Unlike BeautifulSoup, this only works for elements not text or tail
    '''
    parent = item.getparent()
    idx = parent.index(item)
    if etree.iselement(replacement):
        parent[idx] = replacement
        return replacement
    elif isinstance(replacement, str):
        new_tag = etree.fromstring(replacement)
        parent[idx] = new_tag
        return new_tag


def get_tail(element, ignore_whitespace=False):
    tail = element.tail or ''
    if ignore_whitespace:
        tail = tail.strip()
    return tail


def replace_amp(raw):
    return raw.replace('&', '&amp;')

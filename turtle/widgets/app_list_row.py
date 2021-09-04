# app_list_row.py
#
# Copyright 2021 Andrey Maksimov
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE X CONSORTIUM BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# Except as contained in this notice, the name(s) of the above copyright
# holders shall not be used in advertising or otherwise to promote the sale,
# use or other dealings in this Software without prior written
# authorization.
import configparser
import os
from typing import Optional

from gi.repository import Gtk, GObject, GdkPixbuf

from turtle.config import RESOURCE_PREFIX

DESKTOP_SECTION = 'Desktop Entry'


class AppData(GObject.GObject):
    filepath: str

    def __init__(self, filepath):
        GObject.GObject.__init__(self)

        self.filepath = filepath

        self.parser = configparser.ConfigParser()
        self.parser.optionxform = str
        self.parser.read_file(open(filepath))

    def save(self):
        self.parser.write(open(self.filepath, 'w'), False)

    @property
    def name(self) -> str:
        return self.parser.get(DESKTOP_SECTION, 'Name')

    @name.setter
    def name(self, value: str) -> None:
        self.parser.set(DESKTOP_SECTION, 'Name', value)

    @property
    def hidden(self) -> bool:
        if self.parser.has_option(DESKTOP_SECTION, 'Hidden'):
            return self.parser.getboolean(DESKTOP_SECTION, 'Hidden')
        return False

    @hidden.setter
    def hidden(self, value) -> None:
        self.parser.set(DESKTOP_SECTION, 'Hidden', str(value).lower())

    @property
    def terminal(self) -> bool:
        if self.parser.has_option(DESKTOP_SECTION, 'Terminal'):
            return self.parser.getboolean(DESKTOP_SECTION, 'Terminal')
        return False

    @terminal.setter
    def terminal(self, value) -> None:
        self.parser.set(DESKTOP_SECTION, 'Terminal', str(value).lower())

    @property
    def icon(self) -> str:
        if self.parser.has_option(DESKTOP_SECTION, 'Icon'):
            return self.parser.get(DESKTOP_SECTION, 'Icon')
        return ""

    @property
    def keywords(self) -> str:
        if self.parser.has_option(DESKTOP_SECTION, 'Keywords'):
            return self.parser.get(DESKTOP_SECTION, 'Keywords')
        return ""

    @keywords.setter
    def keywords(self, value) -> None:
        self.parser.set(DESKTOP_SECTION, 'Keywords', value)

    def __repr__(self):
        return f"{self.name}"


@Gtk.Template(resource_path=f"{RESOURCE_PREFIX}/ui/widgets.ui")
class AppListRow(Gtk.ListBoxRow):
    __gtype_name__ = "AppListRow"

    app_data: AppData
    app_icon: Gtk.Image = Gtk.Template.Child()
    app_label: Gtk.Label = Gtk.Template.Child()
    app_switch: Gtk.Switch = Gtk.Template.Child()

    def __init__(self, app_data: AppData):
        super().__init__()
        self.app_data = app_data

        # Setup Icon
        icon = self.app_data.icon
        if icon.startswith('/'):
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                filename=icon,
                width=32,
                height=32,
                preserve_aspect_ratio=True)
            self.app_icon.set_from_pixbuf(pixbuf)
        elif icon:
            self.app_icon.set_from_icon_name(icon, Gtk.IconSize.BUTTON)

        self.app_label.set_label(self.app_data.name)
        self.app_switch.set_active(not self.app_data.hidden)
        self.app_switch.connect('state-set', self.app_switch_change)

    def app_switch_change(self, switch: Gtk.Switch, value: bool) -> None:
        self.app_data.hidden = not value
        self.app_data.save()

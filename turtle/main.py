# main.py
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

import sys
from typing import List

import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Granite', '1.0')
gi.require_version('Handy', '1')

from gi.repository import Gtk, Gio, Granite, GLib, Gdk

from .window import TurtleWindow


class Application(Gtk.Application):
    granite_settings: Granite.Settings
    gtk_settings: Gtk.Settings

    # App vars to handle command line
    app_path: str
    app_name: str
    app_terminal: bool = False
    app_icon: str

    def __init__(self):
        super().__init__(application_id='com.github.tenderowl.turtle',
                         flags=Gio.ApplicationFlags.HANDLES_OPEN)

        self.window: TurtleWindow = None

        self.add_main_option("name", b"n",
                             GLib.OptionFlags.NONE, GLib.OptionArg.STRING,
                             "app name in the AppMenu", None)
        self.add_main_option("icon", b"i",
                             GLib.OptionFlags.NONE, GLib.OptionArg.STRING,
                             "icon name or path", None)
        self.add_main_option("terminal", b"t",
                             GLib.OptionFlags.NONE, GLib.OptionArg.NONE,
                             "open in terminal", None)

    def do_activate(self):
        self.granite_settings = Granite.Settings.get_default()
        self.gtk_settings = Gtk.Settings.get_default()

        # Then, we check if the user's preference is for the dark style and set it if it is
        self.gtk_settings.props.gtk_application_prefer_dark_theme = \
            self.granite_settings.props.prefers_color_scheme == Granite.SettingsColorScheme.DARK

        # Finally, we listen to changes in Granite.Settings and update our app if the user changes their preference
        self.granite_settings.connect("notify::prefers-color-scheme",
                                      self.color_scheme_changed)

        self.window = self.props.active_window
        if not self.window:
            self.window = TurtleWindow(application=self)
        self.window.present()

    def do_handle_local_options(self, options: GLib.VariantDict) -> int:
        _app_name = options.lookup_value("name", GLib.VariantType("s"))
        self.app_name = _app_name.get_string() if _app_name else ""
        _app_icon = options.lookup_value("icon", GLib.VariantType("s"))
        self.app_icon = _app_icon.get_string() if _app_icon else ""
        self.app_terminal = options.contains("terminal")

        return Gtk.Application.do_handle_local_options(self, options)

    def do_open(self, files: List[Gio.File], _n_files: int, _hint):
        self.activate()
        if _n_files > 0:
            self.app_path = files[0].get_path()
            self.open_file()

    def open_file(self):
        self.window.exec_path = self.app_path
        self.window.app_name = self.app_name
        self.window.app_icon = self.app_icon
        self.window.app_terminal = self.app_terminal
        self.window.switch_to_setup()

    def color_scheme_changed(self, _old, _new):
        self.gtk_settings.props.gtk_application_prefer_dark_theme = \
            self.granite_settings.props.prefers_color_scheme == Granite.SettingsColorScheme.DARK


def main(version):
    app = Application()
    return app.run(sys.argv)

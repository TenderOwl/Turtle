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
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Granite', '1.0')
gi.require_version('Handy', '1')

from gi.repository import Gtk, Gio, Granite

from .window import TurtleWindow


class Application(Gtk.Application):
    granite_settings: Granite.Settings
    gtk_settings: Gtk.Settings

    def __init__(self):
        super().__init__(application_id='com.github.tenderowl.turtle',
                         flags=Gio.ApplicationFlags.FLAGS_NONE)

    def do_activate(self):
        self.granite_settings = Granite.Settings.get_default()
        self.gtk_settings = Gtk.Settings.get_default()

        # Then, we check if the user's preference is for the dark style and set it if it is
        self.gtk_settings.props.gtk_application_prefer_dark_theme = \
            self.granite_settings.props.prefers_color_scheme == Granite.SettingsColorScheme.DARK

        # Finally, we listen to changes in Granite.Settings and update our app if the user changes their preference
        self.granite_settings.connect("notify::prefers-color-scheme",
                                      self.color_scheme_changed)

        win = self.props.active_window
        if not win:
            win = TurtleWindow(application=self)
        win.present()

    def color_scheme_changed(self, _old, _new):
        self.gtk_settings.props.gtk_application_prefer_dark_theme = \
            self.granite_settings.props.prefers_color_scheme == Granite.SettingsColorScheme.DARK


def main(version):
    app = Application()
    return app.run(sys.argv)

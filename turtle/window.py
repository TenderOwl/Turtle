# window.py
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

import os
import stat
from typing import Optional
from urllib.parse import unquote, urlparse

from gi.overrides.GdkPixbuf import Pixbuf
from gi.repository import Gtk, Gdk, Granite, Handy, Gio

from gettext import gettext as _

from turtle.config import RESOURCE_PREFIX, APPS_PATH_PREFIX
from turtle.widgets.app_list_row import AppListRow, AppData


@Gtk.Template(resource_path="/com/github/tenderowl/turtle/ui/window.ui")
class TurtleWindow(Handy.ApplicationWindow):
    __gtype_name__ = "TurtleWindow"

    main_box: Gtk.Box = Gtk.Template.Child()
    pages_switcher: Gtk.Stack = Gtk.Template.Child()
    pages: Gtk.Stack = Gtk.Template.Child()
    screens: Gtk.Stack = Gtk.Template.Child()
    header_bar = Gtk.Template.Child()
    overlay: Gtk.Overlay = Gtk.Template.Child()
    drop_area: Gtk.Box = Gtk.Template.Child()
    back_button: Gtk.Button = Gtk.Template.Child()
    select_button: Gtk.Button = Gtk.Template.Child()
    make_button: Gtk.Button = Gtk.Template.Child()
    name_entry: Gtk.Entry = Gtk.Template.Child()
    icon_entry: Gtk.Entry = Gtk.Template.Child()
    icon_select_btn: Gtk.Button = Gtk.Template.Child()
    exec_entry: Gtk.Entry = Gtk.Template.Child()
    terminal_entry: Gtk.CheckButton = Gtk.Template.Child()
    apps_listbox: Gtk.ListBox = Gtk.Template.Child()
    appdata_revealer: Gtk.Revealer = Gtk.Template.Child()
    appdata_name: Gtk.Label = Gtk.Template.Child()
    appdata_terminal: Gtk.CheckButton = Gtk.Template.Child()
    appdata_keywords: Gtk.Entry = Gtk.Template.Child()
    toast: Granite.WidgetsToast = Granite.WidgetsToast()

    # Path to selected executable
    exec_path: str = ""
    app_name: str = ""
    app_icon: str = ""
    app_terminal: bool = False
    desktop_file_path: str = None
    appdata_current: Optional[AppData]

    def __init__(self, **kwargs):
        # Don't forget to initialize Handy!
        Handy.init()

        super().__init__(**kwargs)

        self.set_default_icon(Pixbuf.new_from_resource_at_scale(
            f'{RESOURCE_PREFIX}/icons/com.github.tenderowl.turtle.svg',
            128, 128, True
        ))

        # Setup overlay with toast
        self.overlay.add_overlay(self.toast)
        self.overlay.show_all()

        # Connect signals
        self.back_button.connect("clicked", self.back_button_clicked)
        self.select_button.connect("clicked", self.select_button_clicked)
        self.make_button.connect("clicked", self.make_button_clicked)
        self.icon_select_btn.connect("clicked", self.icon_select_clicked)

        self.apps_store = Gio.ListStore()
        self.apps_listbox.bind_model(self.apps_store, AppListRow)
        self.apps_listbox.connect('row_activated', self.apps_listbox_row_selected)
        self.pages.connect("notify::visible-child", self.page_changed)

        # Init drag-n-drop
        drop_target = Gtk.TargetEntry.new('text/uri-list', Gtk.TargetFlags.OTHER_APP, 0)
        self.drop_area.drag_dest_set(Gtk.DestDefaults.ALL, (drop_target,), Gdk.DragAction.MOVE)
        self.drop_area.connect("drag-data-received", self.drag_data_received)

    def select_button_clicked(self, button: Gtk.Button) -> None:
        self.exec_path = self.get_exec_file()

        if not self.exec_path:
            return

        self.switch_to_setup()

    def switch_to_setup(self):
        # Try to detect java apps
        if self.exec_path.endswith('.jar'):
            self.exec_path = f"java -jar {self.exec_path}"

        # Prepare Setup Screen widgets
        self.name_entry.set_text(
            self.app_name or os.path.splitext(os.path.basename(self.exec_path))[0].capitalize()
        )
        self.exec_entry.set_text(self.exec_path)
        self.icon_entry.set_text(self.app_icon)
        self.terminal_entry.set_active(self.app_terminal)
        self.name_entry.grab_focus()

        # Switch screens
        self.screens.set_visible_child_name("setup_screen")
        # Activate back button
        self.back_button.set_visible(True)
        self.pages_switcher.set_sensitive(False)

    def make_button_clicked(self, button: Gtk.Button) -> None:
        """Collect data for the .desktop and call `self.make_desktop_file`"""
        name = self.name_entry.get_text()
        icon_path = self.icon_entry.get_text()
        exec_path = self.exec_entry.get_text()
        terminal = self.terminal_entry.get_active()

        self.make_desktop_file(
            name=name, exec_path=exec_path, icon_path=icon_path, terminal=terminal
        )

    def make_desktop_file(self,
                          name: str,
                          exec_path: str,
                          app_version: str = "1.0",
                          icon_path: str = "",
                          terminal: bool = False,
                          ) -> None:
        """Generate .desktop file and place it into ~/.local/share/applications

        :params name: Specific name of the application, for example "Mozilla".
        :params exec_path: Program to execute, possibly with arguments.
            See the Exec key for details on how this key works.
            The Exec key is required if DBusActivatable is not set to true.
            Even if DBusActivatable is true, Exec should be specified for compatibility
            with implementations that do not understand DBusActivatable.
        :params terminal: Whether the program runs in a terminal window.
        :params app_version: Version of the Desktop Entry Specification that the desktop entry conforms with.
            Entries that confirm with this version of the specification should use 1.5.
            Note that the version field is not required to be present.
        """
        if not self.configure_permission(exec_path):
            return

        desktop_data = self.make_a_desktop(
            name=name,
            exec_path=exec_path,
            icon_path=icon_path,
            terminal=terminal,
            app_version=app_version,
        )

        self.desktop_file_path = os.path.expanduser(
            f"{APPS_PATH_PREFIX}{name}.desktop"
        )

        with open(self.desktop_file_path, "w") as desktop_file:
            desktop_file.writelines(desktop_data)
            desktop_file.flush()
            self.send_notification(f"{name} menu item created!")

    def configure_permission(self, path):
        success = True
        if not os.access(path, os.X_OK):
            success = False
            dlg: Granite.MessageDialog = Granite.MessageDialog.with_image_from_icon_name(
                "Configure permission to execute",
                "In order for this application to be launched from the menu, we need to set the execution permission.",
                "dialog-question",
                Gtk.ButtonsType.CANCEL
            )
            apply_btn: Gtk.Button = dlg.add_button("Set Executable", Gtk.ResponseType.APPLY)
            apply_btn.get_style_context().add_class(Gtk.STYLE_CLASS_SUGGESTED_ACTION)
            # dlg.add_button("Cancel", Gtk.ResponseType.CANCEL)

            response = dlg.run()
            if response == Gtk.ResponseType.APPLY:
                os.chmod(path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IROTH)
                success = True

            dlg.destroy()

        return success

    def back_button_clicked(self, button: Gtk.Button) -> None:
        self.screens.set_visible_child_name("select_screen")
        self.back_button.set_visible(False)
        self.pages_switcher.set_sensitive(True)
        # Reset app data
        self.app_name = ""
        self.app_icon = ""
        self.app_terminal = False

    def get_exec_file(self) -> Optional[str]:
        exec_path: str = None

        # @TODO: Wait till FileChooserNative will give real path, not /var/run/1000
        dialog = Gtk.FileChooserDialog(
            "Please choose an executable",
            self,
            Gtk.FileChooserAction.OPEN,
        )

        dialog.add_buttons(_("_Cancel"),
                           Gtk.ResponseType.CANCEL,
                           _("_Select"),
                           Gtk.ResponseType.ACCEPT)

        response = dialog.run()
        if response == Gtk.ResponseType.ACCEPT:
            exec_path = dialog.get_filename()
            print(f"Application selected: {exec_path}")
        elif response == Gtk.ResponseType.CANCEL:
            print("Cancel clicked")

        dialog.destroy()

        return exec_path

    def make_a_desktop(self,
                       name: str,
                       exec_path: str,
                       app_version: str = "1.0",
                       icon_path: str = "",
                       terminal: bool = False,
                       ) -> str:
        """Return .desktop file entry content based on given values.

        For example:

            [Desktop Entry]
            Encoding=UTF-8
            Version=1.0
            Type=Application
            Terminal=false
            Exec=/path/to/executable
            Name=Name of Application
            Icon=/path/to/icon

        """
        terminal = f"{terminal}".lower()

        return "\n".join(
            [
                "[Desktop Entry]",
                "Encoding=UTF-8",
                "Type=Application",
                f"Version={app_version}",
                f"Terminal={terminal}",
                f"Exec=\"{exec_path}\"",
                f"Name={name}",
                f"Icon={icon_path}",
            ]
        )

    def icon_select_clicked(self, button: Gtk.Button) -> None:
        dialog = Gtk.FileChooserDialog(
            title="Please choose an icon file",
            parent=self,
            action=Gtk.FileChooserAction.OPEN,
        )

        dialog.add_buttons(_("_Cancel"),
                           Gtk.ResponseType.CANCEL,
                           _("_Select"),
                           Gtk.ResponseType.ACCEPT)

        response = dialog.run()
        if response == Gtk.ResponseType.ACCEPT:
            self.icon_entry.set_text(dialog.get_filename())
        elif response == Gtk.ResponseType.CANCEL:
            print("Cancel clicked")

        dialog.destroy()

    def send_notification(self, title: str) -> None:
        self.toast.set_title(title)
        self.toast.set_default_action(_("Undo"))
        self.toast.connect("default-action", self.undo_desktop)
        self.toast.send_notification()

    def undo_desktop(self, event) -> None:
        print(f'Removing {self.desktop_file_path}')
        os.remove(self.desktop_file_path)

    def drag_data_received(self, widget, context: Gdk.DragContext,
                           x: int, y: int,
                           data: Gtk.SelectionData,
                           info: int, time: int) -> None:
        success = False
        uris = data.get_uris()
        if uris:
            exec_path = urlparse(uris[0])
            print('drop data', uris[0])
            self.exec_path = unquote(exec_path.path)
            self.switch_to_setup()
            success = True
        Gtk.drag_finish(context, success, success, time)

    def page_changed(self, stack: Gtk.Stack, arg):
        if self.pages.get_visible_child_name() == 'installed_apps':
            self.load_available_apps()
        else:
            self.appdata_close()

    def load_available_apps(self):
        apps_folder = os.path.expanduser(APPS_PATH_PREFIX)
        self.apps_store.remove_all()
        for file in sorted(os.listdir(apps_folder)):
            if file.endswith(".desktop"):
                self.apps_store.append(AppData(os.path.join(apps_folder, file)))

    def apps_listbox_row_selected(self, listbox: Gtk.ListBox, row: AppListRow):
        self.appdata_revealer.set_reveal_child(True)
        app_data = row.app_data
        self.appdata_name.set_text(app_data.name)
        self.appdata_terminal.set_active(app_data.terminal)
        self.appdata_keywords.set_text(app_data.keywords)
        self.appdata_current = app_data

    @Gtk.Template.Callback()
    def appdata_close_clicked(self, widget=None):
        self.appdata_close()

    def appdata_close(self):
        self.appdata_revealer.set_reveal_child(False)
        self.appdata_current = None

    @Gtk.Template.Callback()
    def appdata_open_clicked(self, widget):
        self.open_external(self.appdata_current)

    @Gtk.Template.Callback()
    def appdata_delete_clicked(self, widget):
        dlg: Granite.MessageDialog = Granite.MessageDialog.with_image_from_icon_name(
            f"Remove {self.appdata_current.name} from AppMenu?",
            "Be careful. This action is permanent.",
            "dialog-warning",
            Gtk.ButtonsType.CANCEL,
        )

        remove_btn = dlg.add_button("Remove", Gtk.ResponseType.ACCEPT)
        remove_btn.get_style_context().add_class(Gtk.STYLE_CLASS_DESTRUCTIVE_ACTION)

        response = dlg.run()
        dlg.destroy()
        if response == Gtk.ResponseType.ACCEPT:
            os.remove(self.appdata_current.filepath)
            self.load_available_apps()

    def open_external(self, appdata: AppData):
        file = Gio.File.new_for_path(path=appdata.filepath)
        try:
            Gtk.show_uri(None, file.get_uri(), Gtk.get_current_event_time())
        except Exception as e:
            print(e)

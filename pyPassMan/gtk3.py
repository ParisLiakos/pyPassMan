#!/usr/bin/python3

from gi.repository import Gtk, Gdk
import hashlib
import pyPassMan.models as models

class MainWindow(Gtk.Window):

    initialized = False
    COLOR_INVALID = Gdk.Color(50000, 0, 0)

    def __init__(self):
        self.settings = models.Settings()
        Gtk.Window.__init__(self, title="Password Manager")

        key = self.show_master_password_dialog()
        if key is None:
            self.close()
        else:
            self.AccountManager = models.AccountManager(self.settings.get_db_path(), models.AESCipher(key))
            self._build()
            self.initialized = True

    def show_master_password_dialog(self):
        if self.settings.master_pass is None:
            return ''

        dialog = MasterKeyInputDialog(self)
        correct = False
        master_pass = None
        while not correct:
            response = dialog.run()
            if response == Gtk.ResponseType.OK:
                master_pass = dialog.master_pass_input.get_text()
                if hashlib.sha512(master_pass.encode('utf-8')).hexdigest() == self.settings.master_pass:
                    correct = True
                    dialog.destroy()
            else:
                dialog.destroy()
                break
        return None if not correct else master_pass

    def _build(self):
        self.set_icon(self.render_icon(Gtk.STOCK_DIALOG_AUTHENTICATION, Gtk.IconSize.MENU))
        self.clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)

        self.grid = Gtk.Grid()
        self.add(self.grid)

        self._create_toolbar()
        self._create_list()

    def _create_toolbar(self):
        toolbar = Gtk.Toolbar()
        self.grid.attach(toolbar, 0, 0, 6, 1)

        button_add = Gtk.ToolButton.new_from_stock(Gtk.STOCK_ADD)
        button_add.connect('clicked', self.on_add_clicked)
        toolbar.insert(button_add, 0)

        button_preferences = Gtk.ToolButton.new_from_stock(Gtk.STOCK_PREFERENCES)
        button_preferences.connect('clicked', self.on_preferences_clicked)
        toolbar.insert(button_preferences, 1)

        button_about = Gtk.ToolButton.new_from_stock(Gtk.STOCK_ABOUT)
        button_about.connect('clicked', self.on_about_clicked)
        toolbar.insert(button_about, 2)

    def _create_list(self):
        store = Gtk.ListStore(int, str, str)

        for record in self.AccountManager.load_all():
          store.append([record.id, record.title, record.username])

        tree = Gtk.TreeView(store)

        tree.set_search_column(1)
        renderer = Gtk.CellRendererText()

        i = 0
        for label in ['id', 'title', 'username']:
            column = Gtk.TreeViewColumn(label.title(), renderer, text=i)
            tree.append_column(column)
            column.set_sort_column_id(i)
            i += 1

        select = tree.get_selection()
        select.connect('changed', self.on_tree_selection_changed)

        # Also save, to add/remove items dynamically
        self.tree = tree
        self.store = store

        copy_password = Gtk.Button('Copy password', image=Gtk.Image(stock=Gtk.STOCK_COPY))
        copy_password.connect('clicked', self.on_copy_button_clicked)
        copy_password.set_sensitive(False)
        edit_record = Gtk.Button('Edit', image=Gtk.Image(stock=Gtk.STOCK_EDIT))
        edit_record.connect('clicked', self.on_edit_clicked)
        edit_record.set_sensitive(False)
        delete_record = Gtk.Button('Delete', image=Gtk.Image(stock=Gtk.STOCK_DELETE))
        delete_record.connect('clicked', self.on_delete_button_clicked)
        delete_record.set_sensitive(False)

        # save to disable/enable at will
        self.copy_password = copy_password
        self.delete_record = delete_record
        self.edit_record = edit_record

        # Make our treelist scrollable
        swH = Gtk.ScrolledWindow()
        swH.set_hexpand(True)
        swH.set_vexpand(True)
        swH.set_min_content_height(150)
        swH.set_min_content_width(270)
        swH.add(tree)

        self.grid.attach(swH, 0, 1, 6, 1)
        self.grid.attach(copy_password, 2, 2, 2, 1)
        self.grid.attach(delete_record, 2, 3, 2, 1)
        self.grid.attach(edit_record, 2, 4, 2, 1)

    def on_add_clicked(self, widget):
        account = models.Account()
        self._create_and_run_edit_dialog(account)

    def on_edit_clicked(self, widget):
        selection = self.tree.get_selection()
        model, paths = selection.get_selected_rows()
        iter = model.get_iter(paths[0])
        if iter != None:
            id = model[iter][0]
            account = self.AccountManager.load(id)
        self._create_and_run_edit_dialog(account)

    def _create_and_run_edit_dialog(self, account):
        dialog = EditAccountDialog(self, account)
        self._run_edit_dialog(dialog, account)

    def _run_edit_dialog(self, dialog, account):
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            missing = False
            for key, part in dialog.form_parts.items():
                input_val = part.input.get_text()
                if not input_val:
                    missing = True
                    part.input.modify_bg(Gtk.StateFlags.NORMAL, self.COLOR_INVALID)
                else:
                    part.input.modify_bg(Gtk.StateFlags.NORMAL, None)
                setattr(account, key, input_val)
            if missing:
                return self._run_edit_dialog(dialog, account)

            try:
                self.AccountManager.save(account)
                self.store.append([account.id, account.title, account.username])
            except Exception as err:
                print(err)
                return self._run_edit_dialog(dialog, account)

        dialog.destroy()

    def on_about_clicked(self, widget):
        dialog = AboutDialog(self)
        response = dialog.run()
        dialog.destroy()

    def on_preferences_clicked(self, widget):
        dialog = PreferencesDialog(self)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            new_master_pass = dialog.form_parts['master_pass'].input.get_text()
            if new_master_pass and new_master_pass is not self.settings.master_pass:
                new_master_pass = hashlib.sha512(new_master_pass.encode('utf-8')).hexdigest()
                self.AccountManager.update_all(models.AESCipher(new_master_pass))
                self.settings.master_pass = new_master_pass
                self.settings.write()
        dialog.destroy()

    def on_copy_button_clicked(self, widget):
        model, treeiter = self.selected.get_selected()
        if treeiter != None:
          id = model[treeiter][0]
          account = self.AccountManager.load(id)
          self.clipboard.set_text(account.password, -1)

    def on_delete_button_clicked(self, widget):
        selection = self.tree.get_selection()
        model, paths = selection.get_selected_rows()
        for path in paths:
            iter = model.get_iter(path)
            if iter != None:
                id = model[iter][0]
                self.AccountManager.delete(id)
                model.remove(iter)

    def on_tree_selection_changed(self, widget):
        model, treeiter = widget.get_selected()
        is_sensitive = True if treeiter != None else False
        self.copy_password.set_sensitive(is_sensitive)
        self.delete_record.set_sensitive(is_sensitive)
        self.edit_record.set_sensitive(is_sensitive)
        self.selected = widget

class EditAccountDialog(Gtk.Dialog):

    form_parts = dict(title=None, username=None, password=None)
    _account = None

    def __init__(self, parent, account):
        self._account = account

        Gtk.Dialog.__init__(self, "Add" if self._account.id is not None else 'Edit', parent,
            Gtk.DialogFlags.MODAL, buttons=(
            Gtk.STOCK_SAVE, Gtk.ResponseType.OK,
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL))

        self._build()
        self.show_all()
        self.set_default_response(Gtk.ResponseType.OK)

    def _build(self):
        box = self.get_content_area()

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        labels_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        inputs_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)

        for l in ['title', 'username', 'password'] :
            part = models.Field(Gtk.Label(l.title()), Gtk.Entry())
            part.label.set_alignment(0, 0)
            part.input.set_activates_default(True)
            if l == 'title':
                part.input.set_tooltip_text('Could be the name of an app, or a domain name')
            if l == 'password':
                part.input.set_visibility(False)
            value = getattr(self._account, l)
            if value is not None:
                part.input.set_text(value)

            # Save the part for processing in submit callbacks.
            self.form_parts[l] = part

            labels_box.pack_start(part.label, False, False, 5)
            inputs_box.pack_start(part.input, False, False, 5)


        hbox.pack_start(labels_box, False, False, 20)
        hbox.pack_start(inputs_box, True, True, 20)

        box.add(hbox)

class AboutDialog(Gtk.AboutDialog):

    def __init__(self, parent):
        Gtk.Dialog.__init__(self, 'About me', parent, version=0.1, program_name='Password Manager', website='https://github.com/ParisLiakos/pyPassMan', authors=['Paris Liakos'], copyright='(c) 2014 Paris Liakos', comments='A GTK3 password manager app writen in Python3', logo=None)

class PreferencesDialog(Gtk.Dialog):

    form_parts = dict(master_pass=None)

    def __init__(self, parent):

        Gtk.Dialog.__init__(self, 'Preferences', parent,
            Gtk.DialogFlags.MODAL, buttons=(
            Gtk.STOCK_SAVE, Gtk.ResponseType.OK,
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL))

        self._build(parent.settings)
        self.show_all()
        self.set_default_response(Gtk.ResponseType.OK)

    def _build(self, settings):
        box = self.get_content_area()

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        labels_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        inputs_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)

        master_pass = models.Field(Gtk.Label('Change Master password'), Gtk.Entry())
        master_pass.label.set_alignment(0, 0)
        master_pass.input.set_activates_default(True)
        master_pass.input.set_visibility(False)
        master_pass.input.set_tooltip_text('A length of 16 characters is recommended')
        # Save the part for processing in submit callbacks.
        self.form_parts['master_pass'] = master_pass

        labels_box.pack_start(master_pass.label, False, False, 5)
        inputs_box.pack_start(master_pass.input, False, False, 5)

        hbox.pack_start(labels_box, False, False, 20)
        hbox.pack_start(inputs_box, True, True, 20)

        box.add(hbox)


class MasterKeyInputDialog(Gtk.Dialog):

    def __init__(self, parent):

        Gtk.Dialog.__init__(self, 'Enter the master password', parent,
            Gtk.DialogFlags.MODAL, buttons=(
            Gtk.STOCK_OK, Gtk.ResponseType.OK))

        self._build(parent.settings)
        self.show_all()
        self.set_default_response(Gtk.ResponseType.OK)

    def _build(self, settings):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)

        master_pass_input =  Gtk.Entry()
        master_pass_input.set_activates_default(True)
        master_pass_input.set_visibility(False)
        # Save the part for processing in submit callbacks.
        self.master_pass_input = master_pass_input

        vbox.pack_start(master_pass_input, True, True, 20)

        self.get_content_area().add(vbox)

def main ():
    win = MainWindow()
    if win.initialized:
        win.connect("delete-event", Gtk.main_quit)
        win.show_all()
        Gtk.main()

if __name__ == "__main__":
    main()

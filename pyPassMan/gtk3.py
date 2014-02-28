#!/usr/bin/python3

from gi.repository import Gtk, Gdk
import sqlite3
import pyPassMan.models as models

class MainWindow(Gtk.Window):

    def __init__(self):
        Gtk.Window.__init__(self, title="Password Manager")
        self.AccountManager = models.AccountManager(sqlite3.connect('passwords.db'), models.AESCipher('SUPERSTRONGKEY12'))
        self._build()

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

        button_about = Gtk.ToolButton.new_from_stock(Gtk.STOCK_ABOUT)
        button_about.connect('clicked', self.on_about_clicked)
        toolbar.insert(button_about, 1)

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
        delete_record = Gtk.Button('Delete', image=Gtk.Image(stock=Gtk.STOCK_DELETE))
        delete_record.connect('clicked', self.on_delete_button_clicked)
        delete_record.set_sensitive(False)

        # save to disable/enable at will
        self.copy_password = copy_password
        self.delete_record = delete_record

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

    def on_add_clicked(self, widget):
        dialog = AddAccountDialog(self)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            values = {}
            for key, part in dialog.form_parts.items():
                values[key] = part.input.get_text()
            account = models.Account(**values)

            try:
                self.AccountManager.save(account)
                self.store.append([account.id, account.title, account.username])
                dialog.destroy()
            except Exception as err:
                print(err)
        else:
            dialog.destroy()

    def on_about_clicked(self, widget):
        dialog = AboutDialog(self)
        response = dialog.run()
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
        self.copy_password.set_sensitive(True if treeiter != None else False)
        self.delete_record.set_sensitive(True if treeiter != None else False)
        self.selected = widget

class AddAccountDialog(Gtk.Dialog):

    form_parts = dict(title=None, username=None, password=None)

    def __init__(self, parent):
        Gtk.Dialog.__init__(self, "Add", parent,
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

            # Save the part for processing in submit callbacks.
            self.form_parts[l] = part

            labels_box.pack_start(part.label, False, False, 5)
            inputs_box.pack_start(part.input, False, False, 5)


        hbox.pack_start(labels_box, False, False, 20)
        hbox.pack_start(inputs_box, True, True, 20)

        box.add(hbox)

class AboutDialog(Gtk.AboutDialog):

    def __init__(self, parent):
        Gtk.Dialog.__init__(self, 'About me', parent, version=0.1, program_name='Password Manager', website='http://rootatwc.com', authors=['Paris Liakos'], copyright='(c) 2014 Paris Liakos', comments='My first GTK3 app with Python', logo=None)

def main ():
    win = MainWindow()
    win.connect("delete-event", Gtk.main_quit)
    win.show_all()
    Gtk.main()

if __name__ == "__main__":
    main()
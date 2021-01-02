import tkinter
import tkinter.ttk
import tkinter.messagebox
import tkinter.filedialog
import os
import shutil
import json
import csv

import state_container

kBaseDir = os.path.dirname(os.path.realpath(__file__))
kProjDir = os.path.join(kBaseDir, 'projects')
kFilename = 'states.db'
kHeightButton = 5
kWidthButton = 60


def get_db_path(name: str) -> str:
    return os.path.join(kProjDir, name, kFilename)


class TransitionProject(object):
    def __init__(self, name: str):
        self._name = name
        self._path_db = get_db_path(name)
        self._data = dict()
        self._widgets = dict()
        self._container = state_container.StateContainer(self._path_db)
        self._init_gui()

    def _on_failure(self, cause: str = None):
        tkinter.messagebox.showerror(
            '',
            cause if cause is not None else 'cannot execute this operation')

    def _show_items(self, selected: list, deselected: list = None):
        self._widgets['show_in'].config(state='normal')
        self._widgets['show_in'].delete('1.0', tkinter.END)
        self._widgets['show_in'].insert(
            tkinter.END, f'{len(selected)} items added\n' +
            ','.join(self._data['items']) + '\n')
        if deselected is not None:
            self._widgets['show_in'].insert(
                tkinter.END, f'{len(deselected)} items deselected\n' +
                ','.join(deselected) + '\n')
        self._widgets['show_in'].config(state='disabled')

    @classmethod
    def _get_input_list(cls, widget: tkinter.Text):
        return tuple(i.strip() for i in widget.get('1.0', tkinter.END).replace(
            '\n', '').strip().split(',') if bool(i.strip()))

    def _input(self) -> list:
        elems = self._get_input_list(self._widgets['text_in'])
        if not bool(elems):
            self._on_failure('input is empty')
            return
        done = set()
        ret = list()
        for elem in elems:
            if elem not in done:
                done.add(elem)
                ret.append(elem)
        self._data['items'] = tuple(ret)
        self._data['full'] = tuple(ret)
        self._show_items(self._data['items'])

    def _cb_add(self):
        if 'items' not in self._data:
            self._on_failure('input is empty')
            return

        states = self._get_input_list(self._widgets['text_add_state'])
        if len(states) != 1:
            self._on_failure('one state should be given')
            return
        content = {n: states[0] for n in self._data['items']}
        try:
            self._container.add_states(content=content,
                                       forced=bool(
                                           self._widgets['forced_add'].get()))
        except Exception as ex:
            self._on_failure(str(ex))

    def _split_add(self):
        if 'full' not in self._data:
            self._on_failure('no data available')
            return
        states = self._get_input_list(self._widgets['text_add_state'])
        if len(states) != 1:
            self._on_failure('one state should be given')
            return
        self._data['items'], left = self._container.select_for_addition(
            content={name: states[0]
                     for name in self._data['full']})
        self._show_items(self._data['items'], left)

    def _cb_transit(self):
        if 'items' not in self._data:
            self._on_failure('input is empty')
            return
        from_transit = self._get_input_list(self._widgets['text_from_transit'])
        to_transit = self._get_input_list(self._widgets['text_to_transit'])
        if len(from_transit) != 1 or len(to_transit) != 1:
            self._on_failure('one state should be given for from and to')
            return
        try:
            self._container.transit(names=self._data['items'],
                                    from_state=from_transit[0],
                                    to_state=to_transit[0],
                                    forced=bool(
                                        self._widgets['forced_transit'].get()))
        except Exception as ex:
            self._on_failure(str(ex))

    def _split_transit(self):
        if 'full' not in self._data:
            self._on_failure('no data available')
            return
        from_transit = self._get_input_list(self._widgets['text_from_transit'])
        if len(from_transit) != 1:
            self._on_failure('one state should be given for from')
            return
        self._data['items'], left = self._container.select_for_transition(
            names=self._data['full'], from_state=from_transit[0])
        self._show_items(self._data['items'], left)

    def _cb_remove(self):
        if 'items' not in self._data:
            self._on_failure('input is empty')
            return
        try:
            self._container.remove(names=self._data['items'],
                                   forced=bool(
                                       self._widgets['forced_remove'].get()))
        except Exception as ex:
            self._on_failure(str(ex))

    def _split_remove(self):
        if 'full' not in self._data:
            self._on_failure('no data available')
            return

        self._data['items'], left = self._container.select_for_removal(
            names=self._data['full'])
        self._show_items(self._data['items'], left)

    def _backup_db(self):
        filename = tkinter.filedialog.asksaveasfilename(
            initialdir=os.path.dirname(self._path_db),
            initialfile=kFilename + '.backup')
        assert bool(filename), 'file not selected'
        shutil.copyfile(self._path_db, filename)

    def _export_db(self, states: list = None):
        filename = tkinter.filedialog.asksaveasfilename(
            initialdir=os.path.dirname(self._path_db))
        assert bool(filename), 'file not selected'
        if states is None:
            states = self._container.get_states()
        if filename.endswith('.json'):
            state_set = set(state for _, state in states)
            text = json.dumps(
                {
                    'states':
                    tuple({
                        'name': name,
                        'state': state
                    } for name, state in states),
                    'count_names':
                    len(states),
                    'count_states':
                    len(state_set),
                    'states_in_project':
                    tuple(state_set)
                },
                indent=' ')
            with open(filename, 'w') as fs:
                fs.write(text)
        # elif filename.endswith('.yaml'):
        #     text = yaml.dump(
        #         tuple({
        #             'name': name,
        #             'state': state
        #         } for name, state in states))
        #     with open(filename, 'w') as fs:
        #         fs.write(text)
        else:
            with open(filename, 'w', newline='') as fs:
                writer = csv.DictWriter(fs, fieldnames=['name', 'state'])
                writer.writeheader()
                for name, state in states:
                    writer.writerow({'name': name, 'state': state})

    def _filter(self):
        win_filter = tkinter.Tk()
        win_filter.title(self._name)

        filtered = {'filtered': None}

        frame_in = tkinter.Frame(win_filter)
        frame_out = tkinter.Frame(win_filter)

        text_filter_names = tkinter.Text(frame_in,
                                         height=kHeightButton,
                                         width=kWidthButton)
        text_filter_states = tkinter.Text(frame_in,
                                          height=kHeightButton,
                                          width=kWidthButton)
        text_filter_names.pack(side=tkinter.TOP, fill=tkinter.X)
        text_filter_states.pack(side=tkinter.TOP, fill=tkinter.X)

        def filter():
            names = self._get_input_list(text_filter_names)
            states = self._get_input_list(text_filter_states)
            names = names if bool(names) else None
            states = states if bool(states) else None
            filtered['filtered'] = self._container.get_states(names=names,
                                                              states=states)
            text_display_names.delete('1.0', tkinter.END)
            text_display_states.delete('1.0', tkinter.END)
            if bool(filtered['filtered']):
                names, states = zip(*filtered['filtered'])
                text_display_names.insert(tkinter.END, '\n'.join(names))
                text_display_states.insert(tkinter.END, '\n'.join(states))

        def export():
            self._export_db(states=filtered['filtered'])

        tkinter.Button(frame_in,
                       text='filter',
                       height=kHeightButton,
                       width=kWidthButton,
                       command=filter).pack(side=tkinter.TOP, fill=tkinter.X)
        tkinter.Button(frame_in,
                       text='export',
                       height=kHeightButton,
                       width=kWidthButton,
                       command=export).pack(side=tkinter.TOP, fill=tkinter.X)
        text_display_names = tkinter.Text(frame_out, width=kWidthButton)
        text_display_states = tkinter.Text(frame_out, width=kWidthButton)
        text_display_names.pack(side=tkinter.LEFT, fill=tkinter.Y)
        text_display_states.pack(side=tkinter.LEFT, fill=tkinter.Y)

        frame_in.pack(side=tkinter.LEFT, fill=tkinter.Y)
        frame_out.pack(side=tkinter.RIGHT, fill=tkinter.Y)

    def _replay(self):
        logs = tkinter.filedialog.askopenfilenames(
            title='select the log files for operations to replay',
            initialdir=kBaseDir,
            filetypes=[("Log files in JSON", "*.log.json")])
        logs = sorted(list(logs))

        path_new = tkinter.filedialog.askdirectory(
            title='select/create directory for new project')
        if not os.path.isdir(path_new):
            os.makedirs(path_new)
        state_container.StateContainer(os.path.join(path_new,
                                                    kFilename)).replay(logs)

    def _init_gui(self):
        # gui preparation
        control = tkinter.Tk()
        control.title(self._name)

        # input
        self._widgets['scrollbar_in'] = tkinter.Scrollbar(control)
        self._widgets['text_in'] = tkinter.Text(self._widgets['scrollbar_in'],
                                                height=kHeightButton,
                                                width=kWidthButton)
        self._widgets['button_in'] = tkinter.Button(
            self._widgets['scrollbar_in'],
            text='input',
            height=kHeightButton,
            width=kWidthButton,
            command=self._input)
        self._widgets['show_in'] = tkinter.Text(self._widgets['scrollbar_in'],
                                                width=kWidthButton,
                                                state=tkinter.DISABLED)
        self._widgets['show_in'].bind(
            '<1>',
            lambda event: self._widgets['show_in'].focus_set())  # allow copy

        self._widgets['scrollbar_in'].pack(side=tkinter.LEFT, fill=tkinter.Y)
        self._widgets['text_in'].pack(side=tkinter.TOP, fill=tkinter.X)
        self._widgets['button_in'].pack(side=tkinter.TOP, fill=tkinter.X)
        self._widgets['show_in'].pack(side=tkinter.TOP, fill=tkinter.X)

        self._widgets['tab_container'] = tkinter.ttk.Notebook(control)
        self._widgets['frame_add'] = tkinter.Frame(
            self._widgets['tab_container'])
        self._widgets['frame_modify'] = tkinter.Frame(
            self._widgets['tab_container'])
        self._widgets['frame_delete'] = tkinter.Frame(
            self._widgets['tab_container'])
        self._widgets['frame_others'] = tkinter.Frame(
            self._widgets['tab_container'])

        # for all three operations, another split operation is added

        # parts for add_items: button, init-state and checkbox
        self._widgets['button_add_state'] = tkinter.Button(
            self._widgets['frame_add'],
            text='execute',
            height=kHeightButton,
            width=kWidthButton,
            command=self._cb_add)
        self._widgets['text_add_state'] = tkinter.Text(
            self._widgets['frame_add'],
            height=kHeightButton,
            width=kWidthButton)
        self._widgets['forced_add'] = tkinter.IntVar()
        self._widgets['check_force_add_state'] = tkinter.Checkbutton(
            self._widgets['frame_add'],
            text='force',
            height=kHeightButton,
            width=kWidthButton,
            command=lambda i=self._widgets['forced_add']: i.set(
                int(not i.get())))
        self._widgets['button_split_add_state'] = tkinter.Button(
            self._widgets['frame_add'],
            text='split',
            height=kHeightButton,
            width=kWidthButton,
            command=self._split_add)
        self._widgets['button_add_state'].pack(side=tkinter.TOP,
                                               fill=tkinter.X)
        self._widgets['text_add_state'].pack(side=tkinter.TOP, fill=tkinter.X)
        self._widgets['check_force_add_state'].pack(side=tkinter.TOP,
                                                    fill=tkinter.X)
        self._widgets['button_split_add_state'].pack(side=tkinter.TOP,
                                                     fill=tkinter.X)

        # parts for transit: button, from-text, to-text and checkbox
        self._widgets['button_transit'] = tkinter.Button(
            self._widgets['frame_modify'],
            text='execute',
            height=kHeightButton,
            width=kWidthButton,
            command=self._cb_transit)
        self._widgets['text_from_transit'] = tkinter.Text(
            self._widgets['frame_modify'],
            height=kHeightButton,
            width=kWidthButton)
        self._widgets['text_to_transit'] = tkinter.Text(
            self._widgets['frame_modify'],
            height=kHeightButton,
            width=kWidthButton)
        self._widgets['forced_transit'] = tkinter.IntVar()
        self._widgets['check_force_transit'] = tkinter.Checkbutton(
            self._widgets['frame_modify'],
            text='force',
            height=kHeightButton,
            width=kWidthButton,
            command=lambda i=self._widgets['forced_transit']: i.set(
                int(not i.get())))
        self._widgets['button_split_transit'] = tkinter.Button(
            self._widgets['frame_modify'],
            text='split',
            height=kHeightButton,
            width=kWidthButton,
            command=self._split_transit)
        self._widgets['button_transit'].pack(side=tkinter.TOP, fill=tkinter.X)
        self._widgets['text_from_transit'].pack(side=tkinter.TOP,
                                                fill=tkinter.X)
        self._widgets['text_to_transit'].pack(side=tkinter.TOP, fill=tkinter.X)
        self._widgets['check_force_transit'].pack(side=tkinter.TOP,
                                                  fill=tkinter.X)
        self._widgets['button_split_transit'].pack(side=tkinter.TOP,
                                                   fill=tkinter.X)

        # parts for remove: button and checkbox
        self._widgets['button_remove'] = tkinter.Button(
            self._widgets['frame_delete'],
            text='execute',
            height=kHeightButton,
            width=kWidthButton,
            command=self._cb_remove)
        self._widgets['forced_remove'] = tkinter.IntVar()
        self._widgets['check_force_remove'] = tkinter.Checkbutton(
            self._widgets['frame_delete'],
            text='force',
            height=kHeightButton,
            width=kWidthButton,
            command=lambda i=self._widgets['forced_remove']: i.set(
                int(not i.get())))
        self._widgets['button_split_remove'] = tkinter.Button(
            self._widgets['frame_delete'],
            text='split',
            height=kHeightButton,
            width=kWidthButton,
            command=self._split_remove)
        self._widgets['button_remove'].pack(side=tkinter.TOP, fill=tkinter.X)
        self._widgets['check_force_remove'].pack(side=tkinter.TOP,
                                                 fill=tkinter.X)
        self._widgets['button_split_remove'].pack(side=tkinter.TOP,
                                                  fill=tkinter.X)

        # others (backup, export)
        tkinter.Button(self._widgets['frame_others'],
                       text='backup',
                       height=kHeightButton,
                       width=kWidthButton,
                       command=self._backup_db).pack(side=tkinter.TOP,
                                                     fill=tkinter.X)
        tkinter.Button(self._widgets['frame_others'],
                       text='export',
                       height=kHeightButton,
                       width=kWidthButton,
                       command=self._export_db).pack(side=tkinter.TOP,
                                                     fill=tkinter.X)
        tkinter.Button(self._widgets['frame_others'],
                       text='filter',
                       height=kHeightButton,
                       width=kWidthButton,
                       command=self._filter).pack(side=tkinter.TOP,
                                                  fill=tkinter.X)
        tkinter.Button(self._widgets['frame_others'],
                       text='replay',
                       height=kHeightButton,
                       width=kWidthButton,
                       command=self._replay).pack(side=tkinter.TOP,
                                                  fill=tkinter.X)

        self._widgets['tab_container'].add(self._widgets['frame_add'],
                                           text='add')
        self._widgets['tab_container'].add(self._widgets['frame_modify'],
                                           text='transit')
        self._widgets['tab_container'].add(self._widgets['frame_delete'],
                                           text='remove')
        self._widgets['tab_container'].add(self._widgets['frame_others'],
                                           text='others')  # TODO

        self._widgets['tab_container'].pack(side=tkinter.RIGHT, fill=tkinter.Y)


def start_project(name: str):
    TransitionProject(name)


def get_project_list() -> list:
    if not os.path.isdir(kProjDir):
        os.mkdir(kProjDir)
    return tuple(proj for proj in os.listdir(kProjDir)
                 if os.path.isfile(get_db_path(proj)))


def start_new_project(_):
    name = new_project.get('1.0', tkinter.END).strip()
    new_project.delete('1.0', tkinter.END)
    assert bool(name), 'empty name'
    if not os.path.isdir(os.path.join(kProjDir, name)):
        os.mkdir(os.path.join(kProjDir, name))
    if bool(name):
        start_project(name)


root = tkinter.Tk()
root.title('transitions')

new_project = tkinter.Text(root, height=kHeightButton, width=kWidthButton)
new_project.pack(side=tkinter.TOP)
new_project.bind('<Return>', start_new_project)

for project in get_project_list()[::-1]:
    tkinter.Button(root,
                   text=project,
                   height=kHeightButton,
                   width=kWidthButton,
                   command=lambda name=project: start_project(name)).pack(
                       side=tkinter.TOP)

tkinter.mainloop()

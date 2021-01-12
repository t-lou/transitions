import tkinter
import tkinter.ttk
import tkinter.messagebox
import tkinter.filedialog
import os
import shutil
import json
import csv
import datetime

import state_container

# Base directory for the program.
kBaseDir = os.path.dirname(os.path.realpath(__file__))
# Directory for the projects.
kProjDir = os.path.join(kBaseDir, 'projects')
# Database filename in projects.
kFilename = 'states.db'
# Height of buttons and other components.
kHeightButton = 5
# Width of buttons and other components.
kWidthButton = 60


def get_db_path(name: str) -> str:
    '''
    Get the database file for one project.

    Attributes:
        name: project name.
    Returns:
        Absolute name for the database file for this project.
    '''
    return os.path.join(kProjDir, name, kFilename)


class TransitionProject(object):
    '''
    GUI for transitions.
    '''
    def __init__(self, name: str):
        '''
        Constructor.

        Attributes:
            name: project name.
        '''
        self._name = name
        self._path_db = get_db_path(name)
        self._data = dict()
        self._widgets = dict()
        self._container = state_container.StateContainer(self._path_db)
        self._init_gui()

    def _on_failure(self, cause: str = None):
        '''
        Show an error message.

        Attributes:
            cause: reason of failure.
        '''
        tkinter.messagebox.showerror(
            '',
            cause if cause is not None else 'cannot execute this operation')

    def _show_items(self, selected: list, deselected: list = None):
        '''
        Show the input items or the splitted items for one operation (acceptable and conflicting).

        Attributes:
            selected: acceptable items for one operation.
            deselected: conflicting items for one operation.
        '''
        self._widgets['show_in'].config(state='normal')
        self._widgets['show_in'].delete('1.0', tkinter.END)
        self._widgets['show_in'].insert(
            tkinter.END, f'{len(selected)} items added\n' +
            ','.join(self._data['items']) + '\n')
        if deselected is not None:
            self._widgets['show_in'].insert(
                tkinter.END,
                f'{len(deselected)} items deselected (copy and input again)\n'
                + ','.join(deselected) + '\n')
        self._widgets['show_in'].config(state='disabled')

    @classmethod
    def _get_input_list(cls, widget: tkinter.Text) -> tuple:
        '''
        Get a list of input objects (item-names or states) separated with ','.

        Attributes:
            widget: input text widget.
        Returns:
            An array of objects from input widget.
        '''
        return tuple(i.strip() for i in widget.get('1.0', tkinter.END).replace(
            '\n', ',').strip().split(',') if bool(i.strip()))

    def _input(self):
        '''
        Get the list of input item-names, save to internal data and show results.
        '''
        elems = self._get_input_list(self._widgets['text_in'])
        if not bool(elems):
            self._on_failure('input is empty')
            return
        elems = tuple(sorted(set(elems), key=elems.index))
        self._data['items'] = elems[:]
        self._data['full'] = elems[:]
        self._show_items(self._data['items'])

    def _cb_add(self):
        '''
        Callback function for addition.
        '''
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
        '''
        Callback function for splitting input items to accepted and conflicting.
        Accepted items are available for operation. Conflicting items are shown for copying and reinput.
        '''
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
        '''
        Callback function for transition.
        '''
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
        '''
        Callback function for splitting input items to accepted and conflicting.
        Accepted items are available for operation. Conflicting items are shown for copying and reinput.
        '''
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
        '''
        Callback function for removal.
        '''
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
        '''
        Callback function for splitting input items to accepted and conflicting.
        Accepted items are available for operation. Conflicting items are shown for copying and reinput.
        '''
        if 'full' not in self._data:
            self._on_failure('no data available')
            return

        self._data['items'], left = self._container.select_for_removal(
            names=self._data['full'])
        self._show_items(self._data['items'], left)

    def _backup_db(self):
        '''
        Callback function for backup database (db file only).
        A dialog for file selection is opened, type in the name and save.
        '''
        filename = tkinter.filedialog.asksaveasfilename(
            initialdir=os.path.dirname(self._path_db),
            initialfile=kFilename + '.backup')
        assert bool(filename), 'file not selected'
        shutil.copyfile(self._path_db, filename)

    def _export_db(self, states: list = None):
        '''
        Callback function for exporting the database for human and machine readable files.
        One JSON and one CSV files will be generated with given path and filename, and corresponding extension.

        Attributes:
            states: if it is given, the given states will be exported; otherwise the states in database will.
        '''
        default_name = str(datetime.datetime.now()).replace(' ', 'T').replace(
            ':', '-')
        filename = tkinter.filedialog.asksaveasfilename(
            initialdir=os.path.dirname(self._path_db),
            initialfile=default_name)
        assert bool(filename), 'file not selected'
        if states is None:
            states = self._container.get_states()
        # json file with summary
        state_list = tuple(state for _, state in states)
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
                len(set(state_list)),
                'states_in_project':
                {s: state_list.count(s)
                 for s in set(state_list)}
            },
            indent=' ')
        with open(filename + '.json', 'w') as fs:
            fs.write(text)
        # csv for Excel or Calc
        with open(filename + '.csv', 'w', newline='') as fs:
            writer = csv.DictWriter(fs, fieldnames=['name', 'state'])
            writer.writeheader()
            for name, state in states:
                writer.writerow({'name': name, 'state': state})

    def _filter(self):
        '''
        Callback function for filtering and displayment.
        It can be used for viewing the states, filtering the states and exporting.
        '''
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
            text_display_names.config(state='normal')
            text_display_states.config(state='normal')
            text_summary.config(state='normal')
            names = self._get_input_list(text_filter_names)
            states = self._get_input_list(text_filter_states)
            names = names if bool(names) else None
            states = states if bool(states) else None
            filtered['filtered'] = self._container.get_states(names=names,
                                                              states=states)
            text_display_names.delete('1.0', tkinter.END)
            text_display_states.delete('1.0', tkinter.END)
            text_summary.delete('1.0', tkinter.END)
            if bool(filtered['filtered']):
                names, states = zip(*filtered['filtered'])
                text_display_names.insert(tkinter.END, '\n'.join(names))
                text_display_states.insert(tkinter.END, '\n'.join(states))
                text_summary.insert(
                    tkinter.END,
                    f'there are {len(set(names))} items with {len(set(states))} states:\n'
                    + ','.join(sorted(set(states), key=states.index)))
            else:
                text_summary.insert(tkinter.END, f'there is no result')
            text_display_names.config(state='disabled')
            text_display_states.config(state='disabled')
            text_summary.config(state='disabled')

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
        text_display_names = tkinter.Text(frame_out,
                                          width=kWidthButton,
                                          state=tkinter.DISABLED)
        text_display_states = tkinter.Text(frame_out,
                                           width=kWidthButton,
                                           state=tkinter.DISABLED)
        text_summary = tkinter.Text(frame_in,
                                    height=kHeightButton,
                                    width=kWidthButton,
                                    state=tkinter.DISABLED)
        text_display_names.pack(side=tkinter.LEFT, fill=tkinter.Y)
        text_display_states.pack(side=tkinter.LEFT, fill=tkinter.Y)
        text_summary.pack(side=tkinter.TOP, fill=tkinter.X)

        # to allow copy
        text_display_names.bind('<1>',
                                lambda event: text_display_names.focus_set())
        text_display_states.bind('<1>',
                                 lambda event: text_display_states.focus_set())
        text_summary.bind('<1>', lambda event: text_summary.focus_set())

        frame_in.pack(side=tkinter.LEFT, fill=tkinter.Y)
        frame_out.pack(side=tkinter.RIGHT, fill=tkinter.Y)

    def _replay(self):
        '''
        Callback function for replaying, it will generate another project with selected log files.
        '''
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
        '''
        Initialize the main panel for one project.
        '''
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
    '''
    Start one existing project.

    Attributes:
        name: project name.
    '''
    TransitionProject(name)


def get_project_list() -> tuple:
    '''
    Get all created projects.

    Returns:
        The name of projects.
    '''
    if not os.path.isdir(kProjDir):
        os.mkdir(kProjDir)
    return tuple(proj for proj in os.listdir(kProjDir)
                 if os.path.isfile(get_db_path(proj)))


def start_new_project(_):
    '''
    Creat a new project.
    '''
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

import os
import sqlite3
import json
import datetime

# The name of the table for states.
kTable = 'states'


class StateContainer(object):
    '''
    The container for the state, each state contains two attributes: name and state.
    Name is the unique identifier, and state shows the stage and state.

    Attributes:
        path: path for the *.db file for sqlite3. The logs will be beside it.
    '''
    def __init__(self, path: str):
        '''
        Constructor, it initilizes the database when it is not available.

        Attributes:
            path: path for the *.db file for sqlite3. The logs will be beside it.
        '''
        self._path = path
        self._dir = os.path.dirname(os.path.realpath(path))
        self._log_dir = os.path.join(self._dir, 'logs')
        self._conn = sqlite3.connect(path)
        cursor = self._conn.cursor()
        if not self.is_table_available():
            cursor.execute(f'CREATE TABLE {kTable} (name text, state text);')
        if not os.path.isdir(self._log_dir):
            os.mkdir(self._log_dir)

    def __del__(self):
        '''
        Destructor, it just closes the connection.
        '''
        self._conn.close()

    def log_action(self, action: dict):
        '''
        Log one dictionary with the information to one action.

        Attributes:
            action: one dict which should contain all information one action brings.
        '''
        log_text = json.dumps(action, indent=' ')
        path = os.path.join(
            self._log_dir,
            str(datetime.datetime.now()).replace(' ', 'T').replace(':', '-') +
            '.log.json')
        with open(path, 'w') as fs:
            fs.write(log_text)

    def is_table_available(self) -> bool:
        '''
        Checks whether the table for this program is created.

        Now it is "states". I don't see how it can be changed because this software is for ME.
        '''
        return (kTable, ) in tuple(self._conn.cursor().execute(
            'SELECT name FROM sqlite_master WHERE type="table";'))

    def read_state(self, name: str) -> str:
        '''
        Get the state for one name.

        Attributes:
            name: one name.
        Returns:
            Its state if the name is given, or None.
        '''
        cursor = self._conn.cursor()
        result = tuple(
            cursor.execute(
                f'SELECT state FROM {kTable} WHERE name=="{name}";'))
        assert len(result) <= 1, f'duplicate result for name {name}'
        return result[0][0] if len(result) > 0 else None

    def consult(self, names: list) -> list:
        '''
        Get the states for a name list.

        Attributes:
            names: one list or array of names.
        Returns:
            The states for the names; when a name cannot be found in database, None is returned in its place.
        '''
        assert all(type(name) == str
                   for name in names), 'wrong parameter in consult'
        return tuple(self.read_state(name) for name in names)

    def get_states(self, names: list = None, states: list = None) -> list:
        '''
        Get the correspondense of names to states.

        Attributes:
            names: one list or names for filtering, if it is None, filtering skips and all names are included.
            states: one list or names for filtering, if it is None, filtering skips and all states are included.
        Returns:
            An array of pairs name-state after the given filtering.
        '''
        if not self.is_table_available():
            return None
        command = f'SELECT name, state FROM {kTable}'
        condition_name = ' or '.join([f'name="{name}" ' for name in names
                                      ]) if names is not None else ''
        condition_state = ' or '.join(
            [f'state="{state}" '
             for state in states]) if states is not None else ''
        condition = (' WHERE ' if bool(condition_name) or bool(condition_state) else '') + \
            condition_name + \
            (' or ' if bool(condition_name) and bool(condition_state) else '') + \
            condition_state
        return tuple(self._conn.cursor().execute(command + condition + ';'))

    def add_states(self, content: dict, forced: bool = False):
        '''
        Add the names with given states.
        When any key in content is available in database, it breaks.

        Attributes:
            content: a dict with name as key and state as value.
            forced: when it is true, the content will be applied without checking.
        '''
        assert all(
            type(n) == str and type(content[n]) == str
            for n in content), 'wrong parameter in add_states'
        names = tuple(content.keys())
        target_states = tuple(content[n] for n in names)
        available_states = self.consult(names)
        conflicts = tuple(e is not None and e != s
                          for s, e in zip(target_states, available_states))
        assert forced or not any(
            conflicts
        ), f'{tuple(n for n, c in zip(names, conflicts) if c)} already added with another states'
        cursor = self._conn.cursor()
        for n, s, e in zip(names, target_states, available_states):
            if e is None:
                cursor.execute(f'INSERT INTO {kTable} VALUES ("{n}" , "{s}");')
            elif e == s:
                pass
            elif forced:
                cursor.execute(
                    f'UPDATE {kTable} SET state="{s}" WHERE name="{n}";')

        action = {
            'action': 'add',
            'content': content,
            'forced': forced,
        }
        if forced:
            action['reset'] = tuple(n for n, c in zip(names, conflicts) if c)
        self.log_action(action)

        self._conn.commit()

    def select_for_addition(self, content: dict) -> (list, list):
        '''
        Separates the keys of contents to two lists: where add is possible, where it is not.
        The list impossible will break the function: add_states.

        Attributes:
            content: a dict with name as key and state as value.
        Returns:
            (accepted, denied): accepted are the names which are safe to apply to add_states;
                denied not accepted, they exist with different states.
        '''
        assert all(
            type(n) == str and type(content[n]) == str
            for n in content), 'wrong parameter in select_for_addition'
        names = tuple(content.keys())
        conflicts = tuple(e is not None and e != s
                          for s, e in zip(tuple(
                              content[n] for n in names), self.consult(names)))
        return tuple(n for n, c in zip(names, conflicts)
                     if not c), tuple(n for n, c in zip(names, conflicts) if c)

    def transit(self,
                names: list,
                from_state: str,
                to_state: str,
                forced: bool = False):
        '''
        Change the states for given names from one state to another.
        When any of names doesn't have from state, it breaks.

        Attributes:
            names: an array or list of the states to change.
            from_state: from which state to change.
            to_state: to change to which state.
            forced: when it is true, the states will be changed for the given names if they appear.
        '''
        assert all(type(name) == str
                   for name in names), 'wrong parameter in transit'
        available_states = self.consult(names)
        assert None not in available_states, \
            f'{tuple(name for name, s in zip(names, available_states) if s is None)} not initialized'
        assert forced or all(s == from_state for s in available_states), \
            f'{tuple(n for n, s in zip(names, available_states) if s != from_state)} doesn\'t have state {from_state}'
        cursor = self._conn.cursor()
        for name, available_state in zip(names, available_states):
            cursor.execute(
                f'UPDATE {kTable} SET state="{to_state}" WHERE name="{name}";')

        action = {
            'action': 'transit',
            'names': names,
            'from_state': from_state,
            'to_state': to_state,
            'forced': forced,
        }
        if forced:
            action['original_states'] = available_states
        self.log_action(action)

        self._conn.commit()

    def select_for_transition(self, names: list,
                              from_state: str) -> (list, list):
        '''
        Separates names to two lists: where transition is possible, where it is not.
        The list impossible will break the function: transit.

        Attributes:
            names: an array or list of the states to change.
            from_state: from which state to change.
        Returns:
            (accepted, denied): accepted are the names which are safe to apply to transit;
                denied not accepted, they are not in database or have different states than from_state.
        '''
        selected = tuple(n for n, s in zip(names, self.consult(names))
                         if s == from_state)
        left = tuple(n for n in names if n not in selected)
        return selected, left

    def remove(self, names: list, forced: bool = False):
        '''
        Remove the states with given names.
        When any of names is not in database, it breaks.

        Attributes:
            names: an array or list of the states to remove.
            forced: when it is true, the states with given names will be deleted anyway.
        '''
        assert all(type(name) == str
                   for name in names), 'wrong parameter in remove'
        available_states = self.consult(names)
        assert forced or None not in available_states, \
            f'{tuple(n for n, s in zip(names, available_states) if s is None)} are not available in remove'
        cursor = self._conn.cursor()
        for name, state in zip(names, available_states):
            if state is not None:
                cursor.execute(f'DELETE FROM {kTable} WHERE name="{name}";')

        action = {
            'action': 'remove',
            'names': names,
            'forced': forced,
        }
        if forced:
            action['skipped'] = tuple(n
                                      for n, s in zip(names, available_states)
                                      if s is None)
        self.log_action(action)

        self._conn.commit()

    def select_for_removal(self, names: list) -> (list, list):
        '''
        Separates names to two lists: where removal is possible, where it is not.
        The list impossible will break the function: remove.

        Attributes:
            names: an array or list of the states to delete.
        Returns:
            (accepted, denied): accepted are the names which are safe to apply to remove;
                denied not accepted, they are not in database.
        '''
        selected = tuple(n for n, s in zip(names, self.consult(names))
                         if s is not None)
        left = tuple(n for n in names if n not in selected)
        return selected, left

    def replay(self, logs: list):
        '''
        Replay the action with given logs.
        When any log is not valid in the updated databasem it breaks.

        Attributes:
            logs: a list or array of logs to replay, it should be one log file generated here.
        '''
        assert all(os.path.isfile(log) for log in logs), 'logs not available'
        example_actions = {
            'add': {
                'action': 'add',
                'content': dict(),
                'forced': False
            },
            'transit': {
                'action': 'transit',
                'names': [],
                'from_state': '',
                'to_state': '',
                'forced': False
            },
            'remove': {
                'action': 'remove',
                'names': [],
                'forced': False
            },
        }
        callbacks = {
            'add': self.add_states,
            'transit': self.transit,
            'remove': self.remove,
        }
        for log in logs:
            with open(log) as fs:
                action = json.loads(fs.read())
            assert 'action' in action and action['action'] in example_actions and \
                all(p in action and type(action[p]) == type(example_actions[action['action']][p]) \
                    for p in example_actions[action['action']]), \
                f'invalid action {action} in {log}'
            callbacks[action['action']](**{
                p: action[p]
                for p in example_actions[action['action']] if p != 'action'
            })

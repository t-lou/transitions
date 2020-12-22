import os
import sqlite3
import json
import datetime

TABLE = 'states'


class StateContainer(object):
    def __init__(self, path: str):
        self._path = path
        self._dir = os.path.dirname(os.path.realpath(path))
        self._log_dir = os.path.join(self._dir, 'logs')
        self._conn = sqlite3.connect(path)
        cursor = self._conn.cursor()
        if not self.is_table_available():
            cursor.execute(f'CREATE TABLE {TABLE} (name text, state text)')
        if not os.path.isdir(self._log_dir):
            os.mkdir(self._log_dir)

    def __del__(self):
        self._conn.close()

    def log_action(self, action: dict):
        log_text = json.dumps(action, indent=' ')
        path = os.path.join(self._log_dir,
                            str(datetime.datetime.now()) + '.log.json')
        with open(path, 'w') as fs:
            fs.write(log_text)

    def is_table_available(self) -> bool:
        return (TABLE, ) in tuple(self._conn.cursor().execute(
            'SELECT name FROM sqlite_master WHERE type="table"'))

    def read_state(self, name: str) -> str:
        cursor = self._conn.cursor()
        result = tuple(
            cursor.execute(f'SELECT state FROM {TABLE} WHERE name=="{name}";'))
        assert len(result) <= 1, f'duplicate result for name {name}'
        return result[0][0] if len(result) > 0 else None

    def consult(self, names: list) -> list:
        assert all(type(name) == str
                   for name in names), 'wrong parameter in consult'
        return tuple(self.read_state(name) for name in names)

    def get_states(self, names: list = None, states: list = None) -> list:
        if not self.is_table_available():
            return None
        command = f'SELECT name, state FROM {TABLE}'
        if names is not None or states is not None:
            command += ' WHERE '
        if names is not None:
            command += ' or '.join([f'name="{name}" ' for name in names])
        if states is not None:
            if names is not None:
                command += ' or '
            command += ' or '.join([f'state="{state}" ' for state in states])
        command += ';'
        return tuple(self._conn.cursor().execute(command))

    def add_states(self, content: list, forced: bool = False):
        assert all(
            len(elem) == 2 and type(elem[0]) == str and type(elem[1]) == str
            for elem in content), 'wrong parameter in add_states'
        available_states = self.consult(tuple(zip(*content))[0])
        assert forced or all(
            s is None or s == e[1] for e, s in zip(content, available_states)
        ), f'{tuple(e[0] for e, s in zip(content, available_states) if not (s is None or s == e[1]))} already added with another states'
        cursor = self._conn.cursor()
        for elem, available_state in zip(content, available_states):
            if available_state is None:
                cursor.execute(
                    f'INSERT INTO {TABLE} VALUES ("{elem[0]}" , "{elem[1]}")')
            elif available_state == elem[1]:
                pass
            elif forced:
                cursor.execute(
                    f'UPDATE {TABLE} SET state="{elem[1]}" WHERE name="{elem[0]}"'
                )

        action = {
            'action': 'add',
            'content': {n: s
                        for n, s in content},
            'forced': forced,
        }
        if forced:
            action['reset'] = tuple(e[0]
                                    for e, s in zip(content, available_states)
                                    if s is not None and s != e[1])
        self.log_action(action)

        self._conn.commit()

    def select_for_addition(self, content: list) -> (list, list):
        names, _ = zip(*content)
        now_states = self.consult(names)
        selected = tuple(e[0] for e, s in zip(content, now_states)
                         if s is None or s == e[1])
        left = tuple(e for e in names if e not in selected)
        return selected, left

    def transit(self,
                names: list,
                from_state: str,
                to_state: str,
                forced: bool = False):
        assert all(type(name) == str
                   for name in names), 'wrong parameter in transit'
        available_states = self.consult(names)
        assert None not in available_states, f'{tuple(name for name, s in zip(names, available_states) if s is None)} not initialized'
        assert forced or all(
            s == from_state for s in available_states
        ), f'{tuple(name for name, s in zip(names, available_states) if s != from_state)} doesn\'t have state {from_state}'
        cursor = self._conn.cursor()
        for name, available_state in zip(names, available_states):
            cursor.execute(
                f'UPDATE {TABLE} SET state="{to_state}" WHERE name="{name}"')

        action = {
            'action': 'transit',
            'names': names,
            'from': from_state,
            'to': to_state,
            'forced': forced,
        }
        if forced:
            action['original_states'] = available_states
        self.log_action(action)

        self._conn.commit()

    def select_for_transition(self, names: list,
                              from_state: str) -> (list, list):
        selected = tuple(n for n, s in zip(names, self.consult(names))
                         if s == from_state)
        left = tuple(n for n in names if n not in selected)
        return selected, left

    def remove(self, names: list, forced: bool = False):
        assert all(type(name) == str
                   for name in names), 'wrong parameter in remove'
        available_states = self.consult(names)
        assert forced or None not in available_states, f'{tuple(n for n, s in zip(names, available_states) if s is None)} are not available in remove'
        cursor = self._conn.cursor()
        for name, state in zip(names, available_states):
            if state is not None:
                cursor.execute(f'DELETE FROM {TABLE} WHERE name="{name}"')

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
        selected = tuple(n for n, s in zip(names, self.consult(names))
                         if s is not None)
        left = tuple(n for n in names if n not in selected)
        return selected, left

    def replay(self, logs: list):
        assert all(os.path.isfile(log) for log in logs), 'logs not available'
        for log in logs:
            with open(log) as fs:
                action = json.loads(fs.read())
            # print(action)
            assert 'action' in action and action['action'] in (
                'add', 'transit', 'remove'), f'invalid action in {log}'
            if action['action'] == 'add':
                assert 'content' in action and type(
                    action['content']) == dict and 'forced' in action and type(
                        action['forced']) == bool, 'invalid action add'
                self.add_states(content=tuple(
                    (n, action['content'][n]) for n in action['content']),
                                forced=action['forced'])
            elif action['action'] == 'transit':
                assert 'names' in action and type(
                    action['names']
                ) in (list, tuple) and 'from' in action and type(
                    action['from']) == str and 'to' in action and type(
                        action['to']) == str and 'forced' in action and type(
                            action['forced']) == bool, 'invalid action transit'
                self.transit(names=action['names'],
                             from_state=action['from'],
                             to_state=action['to'],
                             forced=action['forced'])
            else:
                assert 'names' in action and type(action['names']) in (
                    list, tuple) and 'forced' in action and type(
                        action['forced']) == bool, 'invalid action remove'
                self.remove(names=action['names'], forced=action['forced'])

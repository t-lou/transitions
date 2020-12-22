import os
import sqlite3

EXT = '.db'
TABLE = 'states'


def get_path(path: str):
    return path + EXT if not (len(path) > len(EXT)
                              and path.endswith(EXT)) else path


def reset(path: str):
    if os.path.isfile(get_path(path)):
        os.remove(get_path(path))


def init_db(path: str, content: list):
    assert all(
        len(elem) == 2 and type(elem[0]) == str and type(elem[1]) == str
        for elem in content)
    conn = sqlite3.connect(get_path(path))
    c = conn.cursor()
    c.execute(f'CREATE TABLE {TABLE} (name text, state text)')
    for elem in content:
        c.execute(f'INSERT INTO {TABLE} VALUES ("{elem[0]}" , "{elem[1]}")')
    conn.commit()
    conn.close()


def check_db(path: str, content: list):
    assert all(
        len(elem) == 2 and type(elem[0]) == str and type(elem[1]) == str
        for elem in content)
    conn = sqlite3.connect(get_path(path))
    is_okay = True
    c = conn.cursor()
    for elem in content:
        result = tuple(
            c.execute(f'SELECT state FROM {TABLE} WHERE name=="{elem[0]}";'))
        assert len(result) == 1, f'found non-unique match for name {elem[0]}'
        is_okay = is_okay and result[0][0] == elem[1]
    conn.commit()
    conn.close()
    return is_okay

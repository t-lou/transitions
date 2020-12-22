import unittest
import sys
import shutil
import os
import sqlite3

sys.path.append(os.getcwd() + '/..')

import state_container

FILE = './transitions.db'


def check_db(path: str, content: list):
    assert all(
        len(elem) == 2 and type(elem[0]) == str and type(elem[1]) == str
        for elem in content)
    conn = sqlite3.connect(path)
    is_okay = True
    c = conn.cursor()
    for elem in content:
        result = tuple(
            c.execute(f'SELECT state FROM states WHERE name=="{elem[0]}";'))
        assert len(result) == 1, f'found non-unique match for name {elem[0]}'
        is_okay = is_okay and result[0][0] == elem[1]
    conn.commit()
    conn.close()
    return is_okay


class TestTransitions(unittest.TestCase):
    def setUp(self):
        if os.path.isfile(FILE):
            os.remove(FILE)

    def tearDown(self):
        if os.path.isfile(FILE):
            os.remove(FILE)
        if os.path.isdir('logs'):
            shutil.rmtree('logs')

    def test1(self):
        target = state_container.StateContainer(FILE)

        # initialize states
        target.add_states((
            ('issue1', 'init'),
            ('issue2', 'done'),
        ))
        self.assertTrue(
            check_db(FILE, (
                ('issue1', 'init'),
                ('issue2', 'done'),
            )))

        self.assertEqual(target.consult(['issue1', 'issue2', 'issue3']),
                         ('init', 'done', None))

        # add more states
        target.add_states((
            ('issue4', 'init'),
            ('issue5', 'done'),
        ))
        self.assertEqual(
            target.consult(['issue1', 'issue2', 'issue3', 'issue4', 'issue5']),
            ('init', 'done', None, 'init', 'done'))

        # add existing states by replacing
        # self.assertRaises(AssertionError,
        #                   target.add_states((('issue1', 'done'), )))
        # TODO assertRaises didn't work with either AssertionError or Exception
        triggered = False
        try:
            target.add_states((('issue1', 'done'), ))
        except Exception:
            triggered = True
        self.assertTrue(triggered)
        target.add_states((('issue1', 'done'), ), forced=True)
        self.assertEqual(
            target.consult(['issue1', 'issue2', 'issue3', 'issue4', 'issue5']),
            ('done', 'done', None, 'init', 'done'))
        # add_states failure doesn't change mode
        try:
            target.add_states((
                ('issue9', 'init'),
                ('issue8', 'done'),
                ('issue7', 'init'),
                ('issue6', 'done'),
                ('issue5', 'nothing'),
            ))
        except Exception:
            pass
        self.assertEqual(target.consult(['issue5', 'issue6', 'issue7']),
                         ('done', None, None))

        # get_states and filtering
        self.assertEqual(
            set(target.get_states()),
            set([('issue1', 'done'), ('issue2', 'done'), ('issue4', 'init'),
                 ('issue5', 'done')]))
        self.assertEqual(set(target.get_states(names=('issue1', 'issue4'))),
                         set([('issue1', 'done'), ('issue4', 'init')]))
        self.assertEqual(
            set(target.get_states(states=('done', ))),
            set([('issue1', 'done'), ('issue2', 'done'), ('issue5', 'done')]))
        self.assertEqual(
            set(
                target.get_states(states=('done', ),
                                  names=('issue4', 'issue5'))),
            set([('issue1', 'done'), ('issue2', 'done'), ('issue4', 'init'),
                 ('issue5', 'done')]))

        # now the states are complex, test the selection
        self.assertEqual(
            target.select_for_addition(content=(('issue1', 'done'),
                                                ('issue2', 'restart'),
                                                ('issue3', 'init'))),
            (('issue1', 'issue3'), ('issue2', )))
        self.assertEqual(
            target.select_for_transition(names=('issue2', 'issue3', 'issue4'),
                                         from_state='done'),
            (('issue2', ), ('issue3', 'issue4')))
        self.assertEqual(
            target.select_for_removal(names=('issue1', 'issue2', 'issue3')),
            (('issue1', 'issue2'), ('issue3', )))

        # transit
        target.transit(('issue1', 'issue2', 'issue5'),
                       from_state='done',
                       to_state='failed')
        self.assertEqual(
            target.consult(['issue1', 'issue2', 'issue3', 'issue4', 'issue5']),
            ('failed', 'failed', None, 'init', 'failed'))
        # transit from wrong states
        triggered = False
        try:
            target.transit(('issue1', 'issue2'),
                           from_state='done',
                           to_state='failed')
        except Exception:
            triggered = True
        self.assertTrue(triggered)
        # transit from uninitialized
        triggered = False
        try:
            target.transit(('issue3', ), from_state='done', to_state='failed')
        except Exception:
            triggered = True
        self.assertTrue(triggered)
        # force transit
        self.assertEqual(
            target.consult(['issue1', 'issue2', 'issue3', 'issue4', 'issue5']),
            ('failed', 'failed', None, 'init', 'failed'))
        target.transit(('issue1', 'issue2', 'issue4', 'issue5'),
                       from_state='*',
                       to_state='restart',
                       forced=True)
        self.assertEqual(
            target.consult(['issue1', 'issue2', 'issue3', 'issue4', 'issue5']),
            ('restart', 'restart', None, 'restart', 'restart'))
        # force transit doesn't work for uninitialized states
        triggered = False
        try:
            target.transit(('issue1', 'issue2', 'issue3', 'issue4', 'issue5'),
                           from_state='*',
                           to_state='doomed',
                           forced=True)
        except Exception:
            triggered = True
        self.assertTrue(triggered)
        # failed transit no infuence
        self.assertEqual(
            target.consult(['issue1', 'issue2', 'issue3', 'issue4', 'issue5']),
            ('restart', 'restart', None, 'restart', 'restart'))
        target.transit(('issue5', ), from_state='restart', to_state='-')
        try:
            target.transit(('issue1', 'issue2', 'issue4', 'issue5'),
                           from_state='restart',
                           to_state='doomed')
        except Exception:
            pass
        self.assertEqual(
            target.consult(['issue1', 'issue2', 'issue3', 'issue4', 'issue5']),
            ('restart', 'restart', None, 'restart', '-'))

        # remove
        triggered = False
        try:
            target.remove(('issue3', 'issue4', 'issue5'))
        except Exception:
            triggered = True
        self.assertTrue(triggered)
        self.assertEqual(
            target.consult(['issue1', 'issue2', 'issue3', 'issue4', 'issue5']),
            ('restart', 'restart', None, 'restart', '-'))
        target.remove(('issue4', 'issue5'))
        self.assertEqual(
            target.consult(['issue1', 'issue2', 'issue3', 'issue4', 'issue5']),
            ('restart', 'restart', None, None, None))
        target.remove(('issue1', 'issue2'), forced=True)
        self.assertEqual(
            target.consult(['issue1', 'issue2', 'issue3', 'issue4', 'issue5']),
            (None, None, None, None, None))


if __name__ == '__main__':
    unittest.main()

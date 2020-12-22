import unittest
import sys
import shutil
import os

sys.path.append(os.getcwd() + '/..')

import state_container

DIR_ORIGINAL = './proj'
DIR_REPLAY = './copy'


def clean():
    if os.path.isdir(DIR_ORIGINAL):
        shutil.rmtree(DIR_ORIGINAL)
    if os.path.isdir(DIR_REPLAY):
        shutil.rmtree(DIR_REPLAY)


class TestReplay(unittest.TestCase):
    def setUp(self):
        clean()
        os.makedirs(DIR_ORIGINAL)
        os.makedirs(DIR_REPLAY)

    def tearDown(self):
        clean()

    def test(self):
        # create a dummy project
        container = state_container.StateContainer(
            os.path.join(DIR_ORIGINAL, 'states.db'))
        container.add_states((('1', 'a'), ('2', 'a'), ('3', 'a')))
        container.add_states((('4', 'b'), ('5', 'b'), ('3', 'b')), forced=True)
        container.transit(('3', '4'), from_state='b', to_state='c')
        container.transit(('1', '4'),
                          from_state='-',
                          to_state='d',
                          forced=True)
        container.remove(('2', '-'), forced=True)

        # replay in copy
        dir_log = os.path.join(DIR_ORIGINAL, 'logs')
        logs = sorted(
            [os.path.join(dir_log, fn) for fn in os.listdir(dir_log)])
        container_replay = state_container.StateContainer(
            os.path.join(DIR_REPLAY, 'states.db'))
        container_replay.replay(logs)

        self.assertEqual(container_replay.get_states(), container.get_states())


if __name__ == '__main__':
    unittest.main()

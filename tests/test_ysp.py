"""Test Ysp4000 class"""

import unittest

from ysp4000.ysp import Ysp4000

class TestYsp(unittest.TestCase):
    """Test Ysp methods"""
    def test_updates(self):
        """Test update are handled properly"""
        # pylint: disable=protected-access
        updates = {}
        def cb(**kwargs):
            nonlocal updates
            updates = kwargs

        ysp = Ysp4000(callback=cb)

        ysp.update_state(status='0', power='1')

        self.assertTrue(ysp._ready)
        self.assertTrue(ysp.on)

        self.assertEqual(updates['status'], 'OK')
        self.assertEqual(updates['power'], 'On')

        ysp.update_state(status='0', power='0')

        self.assertTrue(ysp._ready)
        self.assertFalse(ysp.on)

        self.assertEqual(updates['status'], 'OK')
        self.assertEqual(updates['power'], 'Off')

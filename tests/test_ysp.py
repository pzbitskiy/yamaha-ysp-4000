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
            updates.update(**kwargs)

        ysp = Ysp4000(callback=cb)

        ysp.update_state(status='0', power='1')

        self.assertTrue(ysp._ready)
        self.assertTrue(ysp.on)
        self.assertEqual(len(ysp._cbs), 1)

        self.assertEqual(updates['status'], 'OK')
        self.assertEqual(updates['power'], 'On')

        ysp.update_state(status='0', power='0')

        self.assertFalse(ysp._ready)
        self.assertFalse(ysp.on)

        self.assertEqual(updates['status'], 'OK')
        self.assertEqual(updates['power'], 'Off')

    def test_register_unregister(self):
        """Test callback can be registered and unregistered"""
        ysp = Ysp4000()

        updates1 = {}
        def cb1(**kwargs):
            updates1.update(kwargs)

        updates2 = {}
        def cb2(**kwargs):
            updates2.update(kwargs)

        # check it does not fail with None callback
        ysp.register_state_update_cb(None)
        ysp.update_state(status='1', power='0')

        ysp.register_state_update_cb(cb1)
        ysp.register_state_update_cb(cb2)

        ysp.update_state(status='0', power='1')

        # pylint: disable=protected-access
        self.assertTrue(ysp._ready)
        self.assertTrue(ysp.on)
        self.assertEqual(len(ysp._cbs), 2)

        for updates in [updates1, updates2]:
            self.assertEqual(updates['status'], 'OK')
            self.assertEqual(updates['power'], 'On')

        ysp.unregister_state_update_cb(cb1)

        ysp.update_state(status='0', power='0')

        self.assertFalse(ysp._ready)
        self.assertFalse(ysp.on)
        self.assertEqual(len(ysp._cbs), 1)

        # cb1 data was not changes
        self.assertEqual(updates1['status'], 'OK')
        self.assertEqual(updates1['power'], 'On')
        # cb2 data updated
        self.assertEqual(updates2['status'], 'OK')
        self.assertEqual(updates2['power'], 'Off')

"""Test HFN functions"""

import unittest

from ysp4000.hfn import VolumeMap


class TestHfnVolume(unittest.TestCase):
    """Volume tests"""

    def test_pct_to_code(self):  # pylint: disable=too-many-statements
        """Test 0-99 percents to codes"""
        self.assertEqual(VolumeMap.convert_pct(-1), '00')
        self.assertEqual(VolumeMap.convert_pct(0), '00')
        self.assertEqual(VolumeMap.convert_pct(1), '2C')
        self.assertEqual(VolumeMap.convert_pct(2), '32')
        self.assertEqual(VolumeMap.convert_pct(3), '38')
        self.assertEqual(VolumeMap.convert_pct(4), '3E')
        self.assertEqual(VolumeMap.convert_pct(5), '44')
        self.assertEqual(VolumeMap.convert_pct(6), '4A')
        self.assertEqual(VolumeMap.convert_pct(7), '50')
        self.assertEqual(VolumeMap.convert_pct(8), '56')
        self.assertEqual(VolumeMap.convert_pct(9), '5C')
        self.assertEqual(VolumeMap.convert_pct(10), '62')
        self.assertEqual(VolumeMap.convert_pct(11), '66')
        self.assertEqual(VolumeMap.convert_pct(12), '6A')
        self.assertEqual(VolumeMap.convert_pct(13), '6E')
        self.assertEqual(VolumeMap.convert_pct(14), '72')
        self.assertEqual(VolumeMap.convert_pct(15), '76')
        self.assertEqual(VolumeMap.convert_pct(16), '7A')
        self.assertEqual(VolumeMap.convert_pct(17), '7E')
        self.assertEqual(VolumeMap.convert_pct(18), '82')
        self.assertEqual(VolumeMap.convert_pct(19), '86')
        self.assertEqual(VolumeMap.convert_pct(20), '8A')
        self.assertEqual(VolumeMap.convert_pct(21), '8C')
        self.assertEqual(VolumeMap.convert_pct(22), '8E')
        self.assertEqual(VolumeMap.convert_pct(23), '90')
        self.assertEqual(VolumeMap.convert_pct(24), '92')
        self.assertEqual(VolumeMap.convert_pct(25), '94')
        self.assertEqual(VolumeMap.convert_pct(26), '96')
        self.assertEqual(VolumeMap.convert_pct(27), '98')
        self.assertEqual(VolumeMap.convert_pct(28), '9A')
        self.assertEqual(VolumeMap.convert_pct(29), '9C')
        self.assertEqual(VolumeMap.convert_pct(30), '9E')
        self.assertEqual(VolumeMap.convert_pct(39), 'B0')
        self.assertEqual(VolumeMap.convert_pct(40), 'B2')
        self.assertEqual(VolumeMap.convert_pct(41), 'B3')
        self.assertEqual(VolumeMap.convert_pct(42), 'B4')
        self.assertEqual(VolumeMap.convert_pct(43), 'B5')
        self.assertEqual(VolumeMap.convert_pct(44), 'B6')
        self.assertEqual(VolumeMap.convert_pct(45), 'B7')
        self.assertEqual(VolumeMap.convert_pct(46), 'B8')
        self.assertEqual(VolumeMap.convert_pct(47), 'B9')
        self.assertEqual(VolumeMap.convert_pct(48), 'BA')
        self.assertEqual(VolumeMap.convert_pct(49), 'BB')
        self.assertEqual(VolumeMap.convert_pct(50), 'BC')
        self.assertEqual(VolumeMap.convert_pct(60), 'C6')
        self.assertEqual(VolumeMap.convert_pct(70), 'D0')
        self.assertEqual(VolumeMap.convert_pct(80), 'DA')
        self.assertEqual(VolumeMap.convert_pct(90), 'E4')
        self.assertEqual(VolumeMap.convert_pct(99), 'ED')
        self.assertEqual(VolumeMap.convert_pct(100), 'EE')
        self.assertEqual(VolumeMap.convert_pct(101), 'EE')

    def test_code_to_pct(self):
        """Test 00-EE codes to pct"""
        convert = VolumeMap().code_to_hfn
        self.assertEqual(convert('00'), '0')
        self.assertEqual(convert('EE'), '100')
        self.assertEqual(convert('FF'), '100')

        self.assertEqual(convert('2C'), '1')
        self.assertEqual(convert('5C'), '9')
        self.assertEqual(convert('62'), '10')
        self.assertEqual(convert('66'), '11')
        self.assertEqual(convert('8A'), '20')
        self.assertEqual(convert('8C'), '21')
        self.assertEqual(convert('B2'), '40')
        self.assertEqual(convert('B3'), '41')

        back = VolumeMap().code_to_hfn
        forth = VolumeMap.convert_pct

        for i in range(101):
            self.assertEqual(str(i), back(forth(i)))

import unittest

from siphash import MASK, rotl, siphash24


class SipHashTests(unittest.TestCase):
    def test_vectors(self):
        key = bytes(range(16))
        for length, expected in [(0, 0x726fdb47dd0e0e31),
                                 (7, 0xab0200f58b01d137),
                                 (8, 0x93f5f5799a932462),
                                 (15, 0xa129ca6149be45e5),
                                 (16, 0x3f2acc7f57c29bdb),
                                 (63, 0x958a324ceb064572)]:
            with self.subTest(length=length):
                self.assertEqual(siphash24(key, bytes(range(length))), expected)

    def test_key_length_and_rotation(self):
        with self.assertRaises(ValueError):
            siphash24(b'bad', b'')
        self.assertEqual(rotl(1 << 63, 1), 1)
        self.assertEqual(rotl(MASK, 17), MASK)

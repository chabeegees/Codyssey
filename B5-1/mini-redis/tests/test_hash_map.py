import unittest

from hash_map import HashMap


class HashMapTests(unittest.TestCase):
    def test_put_update_remove_and_none(self):
        table = HashMap()
        table.put('한글', 1)
        table.put('한글', 2)
        table.put('', None)
        self.assertEqual(table.size(), 2)
        self.assertEqual(table.get('한글'), 2)
        self.assertTrue(table.contains(''))
        self.assertIsNone(table.get('missing'))
        self.assertFalse(table.contains('missing'))
        self.assertTrue(table.remove('한글'))
        self.assertFalse(table.remove('한글'))
        self.assertEqual(table.keys(), [''])

    def test_resize_preserves_all_values(self):
        table = HashMap()
        for i in range(6):
            table.put(str(i), i)
        self.assertEqual(table.capacity, 8)
        table.put('6', 6)
        self.assertEqual(table.capacity, 16)
        for i in range(7, 200):
            table.put(str(i), i)
        for i in range(200):
            self.assertEqual(table.get(str(i)), i)
        self.assertEqual(table.size(), 200)
        self.assertEqual(sorted(table.keys()), sorted(str(i) for i in range(200)))

    def test_collisions(self):
        # 같은 버킷을 강제로 사용해 체이닝 자체를 검증한다.
        class CollidingMap(HashMap):
            def _index(self, key):
                return 0
        table = CollidingMap()
        for i in range(20):
            table.put(str(i), i)
        for key in ['0', '10', '19']:
            self.assertTrue(table.remove(key))
        self.assertEqual(table.get('11'), 11)
        self.assertEqual(table.size(), 17)

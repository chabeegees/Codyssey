import unittest

from store import MiniRedis


class FakeClock:
    def __init__(self):
        self.now = 100.0

    def __call__(self):
        return self.now


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.store = MiniRedis(clock=self.clock)

    def test_memory_and_lru(self):
        s = self.store
        s.config_set_maxmemory(30)
        s.set('user:1', 'Alice')
        s.set('user:2', 'Bob')
        s.set('user:3', 'Charlie')
        self.assertIsNone(s.get('user:1'))
        self.assertEqual(s.info_memory(), 'used_memory:22\nmaxmemory:30\nevicted_keys:1')
        self.assertEqual(sorted(s.keys()), ['user:2', 'user:3'])

    def test_get_updates_lru_but_exists_and_ttl_do_not(self):
        s = self.store
        s.config_set_maxmemory(4)
        s.set('a', '1')
        s.set('b', '2')
        self.assertEqual(s.get('a'), '1')
        self.assertEqual(s.exists('b'), 1)
        self.assertEqual(s.ttl('b'), -1)
        s.set('c', '3')
        self.assertEqual(s.exists('b'), 0)
        self.assertEqual(s.exists('a'), 1)

    def test_overwrite_resets_ttl_and_memory(self):
        s = self.store
        s.set('a', 'long')
        s.expire('a', 3)
        s.set('a', 'x')
        self.assertEqual(s.ttl('a'), -1)
        self.clock.now += 3
        self.assertEqual(s.get('a'), 'x')
        self.assertEqual(s.used_memory, 2)

    def test_delete_and_recreate_ignores_heap_remnant(self):
        s = self.store
        s.set('a', 'old')
        s.expire('a', 3)
        entry = s._entries.get('a')
        self.assertEqual(s.delete('a'), 1)
        self.assertIsNone(entry.node.prev)
        self.assertIsNone(entry.node.next)
        self.assertIsNone(entry.expire_at)
        self.assertEqual(s.delete('a'), 0)
        s.set('a', 'new')
        s.expire('a', 9)
        self.clock.now += 3
        self.assertEqual(s.get('a'), 'new')
        self.assertEqual(s.ttl('a'), 6)

    def test_oom_is_atomic(self):
        s = self.store
        s.config_set_maxmemory(4)
        with self.assertRaises(MemoryError):
            s.set('large', 'value')
        self.assertEqual(s.dbsize(), 0)
        s.set('a', 'x')
        s.expire('a', 10)
        with self.assertRaises(MemoryError):
            s.set('a', 'toolong')
        self.assertEqual(s.get('a'), 'x')
        self.assertEqual(s.ttl('a'), 10)
        self.assertEqual(s.used_memory, 2)
        self.assertEqual(s.evicted_keys, 0)

    def test_unicode_byte_count_and_unlimited(self):
        s = self.store
        s.set('키', '한글')
        self.assertEqual(s.used_memory, 9)
        s.set('', '')
        self.assertEqual(s.get(''), '')
        self.assertEqual(s.dbsize(), 2)

    def test_expiry_refresh_and_boundary(self):
        s = self.store
        self.assertEqual(s.expire('missing', 1), 0)
        s.set('a', 'x')
        s.expire('a', 3)
        s.expire('a', 5)
        self.clock.now += 3
        self.assertEqual(s.get('a'), 'x')
        self.clock.now += 0.5
        self.assertEqual(s.ttl('a'), 1)
        self.clock.now += 1.5
        self.assertIsNone(s.get('a'))
        self.assertEqual(s.ttl('a'), -2)
        self.assertEqual(len(s._lru), 0)
        self.assertEqual(s.used_memory, 0)
        self.assertEqual(s.evicted_keys, 0)

    def test_active_expiry_for_global_commands(self):
        for command in ['keys', 'dbsize', 'info_memory']:
            with self.subTest(command=command):
                self.store.set('a', 'x')
                self.store.expire('a', 1)
                self.clock.now += 1
                getattr(self.store, command)()
                self.assertEqual(self.store.used_memory, 0)

    def test_immediate_expiry_and_multiple_evictions(self):
        s = self.store
        for seconds in [0, -2]:
            s.set('a', 'x')
            self.assertEqual(s.expire('a', seconds), 1)
            self.assertEqual(s.exists('a'), 0)
        for key in ['a', 'b', 'c']:
            s.set(key, '1')
        s.config_set_maxmemory(3)
        self.assertEqual(s.dbsize(), 3)
        s.set('d', '1')
        self.assertEqual(s.keys(), ['d'])
        self.assertEqual(s.evicted_keys, 3)

    def test_passive_expiry_and_eviction_heap_remnant(self):
        s = self.store
        s.set('a', 'x')
        s.expire('a', 1)
        self.clock.now += 1
        s._expire_if_needed('a')
        self.assertEqual(s.used_memory, 0)
        s.config_set_maxmemory(2)
        s.set('a', 'x')
        s.expire('a', 3)
        s.set('b', 'x')
        self.clock.now += 3
        self.assertEqual(s.get('b'), 'x')
        self.assertEqual(s.evicted_keys, 1)

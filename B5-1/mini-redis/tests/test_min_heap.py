import unittest

from min_heap import MinHeap


class MinHeapTests(unittest.TestCase):
    def test_empty_single(self):
        heap = MinHeap()
        self.assertIsNone(heap.peek())
        self.assertIsNone(heap.pop())
        heap.push((1.0, 'key'))
        self.assertEqual(heap.peek(), (1.0, 'key'))
        self.assertEqual(heap.pop(), (1.0, 'key'))
        self.assertEqual(heap.size(), 0)

    def test_order_ties_and_interleaving(self):
        heap = MinHeap()
        items = [(9.0, 'z'), (1.0, 'b'), (4.0, 'c'), (1.0, 'a'),
                 (7.0, 'd'), (2.0, 'e'), (1.0, 'a')]
        for item in items:
            heap.push(item)
        self.assertEqual(heap.size(), len(items))
        self.assertEqual(heap.pop(), (1.0, 'a'))
        heap.push((0.0, 'new'))
        self.assertEqual(heap.pop(), (0.0, 'new'))
        self.assertEqual([heap.pop() for _ in range(heap.size())], sorted(items)[1:])

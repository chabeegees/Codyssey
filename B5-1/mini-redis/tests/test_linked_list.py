import unittest

from linked_list import DoublyLinkedList, Node


class LinkedListTests(unittest.TestCase):
    def test_order_links_and_move(self):
        linked = DoublyLinkedList()
        a, b, c = Node('a'), Node('b'), Node('c')
        linked.insert_front(b)
        linked.insert_front(a)
        linked.insert_back(c)
        linked.move_to_front(c)
        self.assertEqual([node.data for node in linked], ['c', 'a', 'b'])
        self.assertEqual(len(linked), 3)
        previous = linked.head
        for node in linked:
            self.assertIs(node.prev, previous)
            self.assertIs(previous.next, node)
            previous = node
        self.assertIs(previous.next, linked.tail)
        self.assertIs(linked.tail.prev, previous)

    def test_detached_and_empty(self):
        linked = DoublyLinkedList()
        node = linked.insert_front(Node(1))
        self.assertIs(linked.remove_node(node), node)
        self.assertIsNone(node.prev)
        self.assertIsNone(node.next)
        with self.assertRaises(ValueError):
            linked.remove_node(node)
        self.assertIsNone(linked.remove_front())
        self.assertIsNone(linked.remove_back())
        linked.insert_back(node)
        self.assertIs(linked.remove_front(), node)
        linked.insert_front(node)
        self.assertIs(linked.remove_back(), node)

    def test_foreign_and_sentinel_rejected(self):
        first, second = DoublyLinkedList(), DoublyLinkedList()
        node = first.insert_front(Node())
        with self.assertRaises(ValueError):
            second.remove_node(node)
        with self.assertRaises(ValueError):
            first.insert_back(node)
        with self.assertRaises(ValueError):
            first.remove_node(first.head)

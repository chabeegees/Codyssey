"""더미 노드로 경계 삽입/삭제를 같은 포인터 연산으로 처리한다."""

from typing import Any, Iterator, Optional


class Node:
    """data와 양쪽 이웃을 보관한다. _owner는 잘못된 리스트 조작을 막는다."""

    def __init__(self, data: Any = None) -> None:
        self.prev: Optional['Node'] = None
        self.next: Optional['Node'] = None
        self.data = data
        self._owner: Optional['DoublyLinkedList'] = None


class DoublyLinkedList:
    """실제 내부 노드는 이웃과 상호 연결, 외부 노드는 prev/next가 None이다.

    head/tail sentinel 덕분에 실제 노드는 항상 양쪽 이웃을 갖는다.
    삽입·삭제·이동·길이는 O(1), 전체 순회(__iter__)는 O(n)이다.
    """

    def __init__(self) -> None:
        self.head = Node()
        self.tail = Node()
        self.head.next = self.tail
        self.tail.prev = self.head
        self._size = 0

    def _insert_between(self, node: Node, before: Node, after: Node) -> Node:
        if node._owner is not None or node.prev is not None or node.next is not None:
            raise ValueError('이미 연결된 노드입니다')
        if node is self.head or node is self.tail:
            raise ValueError('더미 노드는 삽입할 수 없습니다')
        node.prev, node.next = before, after
        before.next = after.prev = node
        node._owner = self
        self._size += 1
        return node

    def insert_front(self, node: Node) -> Node:
        return self._insert_between(node, self.head, self.head.next)

    def insert_back(self, node: Node) -> Node:
        return self._insert_between(node, self.tail.prev, self.tail)

    def remove_node(self, node: Node) -> Node:
        """탐색 없이 제거하고 연결을 끊어 중복 제거와 참조 잔존을 막는다."""
        if node._owner is not self:
            raise ValueError('이 리스트의 실제 노드가 아닙니다')
        node.prev.next = node.next
        node.next.prev = node.prev
        node.prev = node.next = None
        node._owner = None
        self._size -= 1
        return node

    def remove_front(self) -> Optional[Node]:
        return None if self._size == 0 else self.remove_node(self.head.next)

    def remove_back(self) -> Optional[Node]:
        return None if self._size == 0 else self.remove_node(self.tail.prev)

    def move_to_front(self, node: Node) -> None:
        self.remove_node(node)
        self.insert_front(node)

    def __len__(self) -> int:
        return self._size

    def __iter__(self) -> Iterator[Node]:
        node = self.head.next
        while node is not self.tail:
            yield node
            node = node.next

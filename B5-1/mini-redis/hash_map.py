"""고정 길이 버킷 배열과 이중 연결 리스트 체인으로 키를 저장한다."""

import os
from typing import Any, List, Optional

from linked_list import DoublyLinkedList, Node
from siphash import siphash24

SECRET = os.urandom(16)


class HashMap:
    """고정 해시(djb2 등)는 충돌 입력을 준비하는 HashDoS에 취약하다.

    실행마다 랜덤 키를 섞는 SipHash로 충돌 키의 사전 예측을 어렵게 한다.
    2배 확장의 이동량은 등비급수이므로 전체 삽입 n회에 O(n), 분할상환
    (amortized) O(1)이다. 조회도 평균 O(1), 충돌이 몰리면 O(n)이다.
    """

    def __init__(self) -> None:
        self.capacity = 8
        self._buckets = [DoublyLinkedList() for _ in range(self.capacity)]
        self._size = 0

    def _index(self, key: str) -> int:
        return siphash24(SECRET, key.encode('utf-8')) % self.capacity

    def _find(self, key: str) -> Optional[Node]:
        for node in self._buckets[self._index(key)]:
            if node.data[0] == key:
                return node
        return None

    def put(self, key: str, value: Any) -> None:
        node = self._find(key)
        if node is not None:
            node.data = (key, value)
            return
        self._buckets[self._index(key)].insert_back(Node((key, value)))
        self._size += 1
        if self._size / self.capacity > 0.75:
            self._resize()

    def _resize(self) -> None:
        """나머지 연산의 기준이 바뀌므로 모든 키를 새 버킷에 재배치한다."""
        old_buckets = self._buckets
        self.capacity *= 2
        self._buckets = [DoublyLinkedList() for _ in range(self.capacity)]
        for bucket in old_buckets:
            while len(bucket):
                node = bucket.remove_front()
                self._buckets[self._index(node.data[0])].insert_back(node)

    def get(self, key: str) -> Any:
        node = self._find(key)
        return None if node is None else node.data[1]

    def remove(self, key: str) -> bool:
        node = self._find(key)
        if node is None:
            return False
        self._buckets[self._index(key)].remove_node(node)
        self._size -= 1
        return True

    def contains(self, key: str) -> bool:
        # None도 값으로 저장할 수 있으므로 get 결과만으로 판단하지 않는다.
        return self._find(key) is not None

    def keys(self) -> List[str]:
        return [node.data[0] for bucket in self._buckets for node in bucket]

    def size(self) -> int:
        return self._size

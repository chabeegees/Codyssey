"""TTL 중 가장 빠른 만료를 루트에서 찾는 배열 기반 최소 힙."""

from typing import List, Optional, Tuple

HeapItem = Tuple[float, str]


class MinHeap:
    """배열 끝에서만 넣고 빼면 완전 이진 트리 모양이 유지된다.

    순서는 한 줄기(높이 log n)만 복구하므로 push/pop은 O(log n),
    peek/size는 O(1)이다. 같은 만료 시각은 튜플의 키로 비교한다.
    """

    def __init__(self) -> None:
        self._items: List[HeapItem] = []

    def push(self, item: HeapItem) -> None:
        self._items.append(item)
        self._heapify_up(len(self._items) - 1)

    def pop(self) -> Optional[HeapItem]:
        if not self._items:
            return None
        root = self._items[0]
        last = self._items.pop()
        if self._items:
            self._items[0] = last
            self._heapify_down(0)
        return root

    def peek(self) -> Optional[HeapItem]:
        return self._items[0] if self._items else None

    def size(self) -> int:
        return len(self._items)

    def _heapify_up(self, index: int) -> None:
        while index > 0:
            parent = (index - 1) // 2
            if self._items[parent] <= self._items[index]:
                break
            self._items[parent], self._items[index] = self._items[index], self._items[parent]
            index = parent

    def _heapify_down(self, index: int) -> None:
        count = len(self._items)
        while 2 * index + 1 < count:
            left = 2 * index + 1
            right = 2 * index + 2
            smaller = left
            if right < count and self._items[right] < self._items[left]:
                smaller = right
            if self._items[index] <= self._items[smaller]:
                break
            self._items[index], self._items[smaller] = self._items[smaller], self._items[index]
            index = smaller

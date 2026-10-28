"""해시맵(위치), 연결 리스트(LRU), 최소 힙(TTL)을 결합한 저장소."""

import time
from typing import Callable, List, Optional

from hash_map import HashMap
from linked_list import DoublyLinkedList, Node
from min_heap import MinHeap


class Entry:
    """자기 LRU 노드를 보관해 키 조회 후 재탐색 없이 이동/삭제한다."""

    def __init__(self, key: str, value: str, node: Node,
                 expire_at: Optional[float] = None) -> None:
        self.key = key
        self.value = value
        self.node = node
        self.expire_at = expire_at


class MiniRedis:
    """문자열만 저장한다. clock 주입으로 실제 대기 없는 TTL 테스트가 가능하다."""

    def __init__(self, clock: Optional[Callable[[], float]] = None) -> None:
        self._clock = time.time if clock is None else clock
        self._entries = HashMap()
        self._lru = DoublyLinkedList()
        self._ttl_heap = MinHeap()
        self.used_memory = 0
        self.maxmemory = 0
        self.evicted_keys = 0

    @staticmethod
    def _entry_size(key: str, value: str) -> int:
        # 따옴표와 자료구조 오버헤드 없이 실제 UTF-8 바이트만 센다.
        return len(key.encode('utf-8')) + len(value.encode('utf-8'))

    def _delete_entry(self, entry: Entry) -> None:
        """모든 삭제 경로가 같은 연산을 사용해 메모리/LRU 불일치를 막는다."""
        self._entries.remove(entry.key)
        self._lru.remove_node(entry.node)
        self.used_memory -= self._entry_size(entry.key, entry.value)
        # 힙 중간 삭제는 O(n) 탐색이 필요하므로 옛 기록은 pop 시 무시한다.
        entry.expire_at = None

    def _expire_if_needed(self, key: str) -> None:
        entry = self._entries.get(key)
        if entry is not None and entry.expire_at is not None:
            if entry.expire_at <= self._clock():
                self._delete_entry(entry)

    def _active_expire(self) -> None:
        """현재 시각까지의 루트를 꺼내되 현재 엔트리와 시각이 같을 때만 삭제한다."""
        now = self._clock()
        while self._ttl_heap.size():
            if self._ttl_heap.peek()[0] > now:
                break
            expire_at, key = self._ttl_heap.pop()
            entry = self._entries.get(key)
            if entry is not None and entry.expire_at == expire_at:
                self._delete_entry(entry)

    def _before(self, key: Optional[str] = None) -> None:
        self._active_expire()
        if key is not None:
            self._expire_if_needed(key)

    def set(self, key: str, value: str) -> str:
        self._before(key)
        new_size = self._entry_size(key, value)
        # 갱신 전에 검사하므로 OOM이면 기존 값/TTL/LRU 순서가 유지된다.
        if self.maxmemory > 0 and new_size > self.maxmemory:
            raise MemoryError("command not allowed when used_memory > 'maxmemory'")
        entry = self._entries.get(key)
        if entry is None:
            node = Node(key)
            entry = Entry(key, value, node)
            self._entries.put(key, entry)
            self._lru.insert_front(node)
        else:
            self.used_memory -= self._entry_size(key, entry.value)
            entry.value = value
            entry.expire_at = None
            self._lru.move_to_front(entry.node)
        self.used_memory += new_size
        while self.maxmemory > 0 and self.used_memory > self.maxmemory:
            oldest_key = self._lru.tail.prev.data
            self._delete_entry(self._entries.get(oldest_key))
            self.evicted_keys += 1
        return 'OK'

    def get(self, key: str) -> Optional[str]:
        self._before(key)
        entry = self._entries.get(key)
        if entry is None:
            return None
        self._lru.move_to_front(entry.node)
        return entry.value

    def delete(self, key: str) -> int:
        self._before(key)
        entry = self._entries.get(key)
        if entry is None:
            return 0
        self._delete_entry(entry)
        return 1

    def exists(self, key: str) -> int:
        self._before(key)
        return int(self._entries.contains(key))

    def dbsize(self) -> int:
        self._before()
        return self._entries.size()

    def keys(self) -> List[str]:
        self._before()
        return self._entries.keys()

    def config_set_maxmemory(self, amount: int) -> str:
        self._before()
        if amount < 0:
            raise ValueError('maxmemory는 0 이상이어야 합니다')
        # 과제의 제거 시점은 SET 이후다. 제한 변경 자체로는 제거하지 않는다.
        self.maxmemory = amount
        return 'OK'

    def info_memory(self) -> str:
        self._before()
        return ('used_memory:{}\nmaxmemory:{}\nevicted_keys:{}'
                .format(self.used_memory, self.maxmemory, self.evicted_keys))

    def expire(self, key: str, seconds: int) -> int:
        self._before(key)
        entry = self._entries.get(key)
        if entry is None:
            return 0
        if seconds <= 0:
            self._delete_entry(entry)
        else:
            entry.expire_at = self._clock() + seconds
            self._ttl_heap.push((entry.expire_at, key))
        return 1

    def ttl(self, key: str) -> int:
        self._before(key)
        entry = self._entries.get(key)
        if entry is None:
            return -2
        if entry.expire_at is None:
            return -1
        remaining = entry.expire_at - self._clock()
        if remaining <= 0:
            self._delete_entry(entry)
            return -2
        return int(remaining)

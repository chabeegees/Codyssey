"""키가 있는 해시 함수 SipHash-2-4를 64비트 정수 연산으로 구현한다."""

from typing import Tuple

MASK = 0xFFFFFFFFFFFFFFFF


def rotl(value: int, bits: int) -> int:
    """64비트 범위 안에서 왼쪽 순환 이동한다."""
    return ((value << bits) | (value >> (64 - bits))) & MASK


def sipround(v0: int, v1: int, v2: int, v3: int) -> Tuple[int, int, int, int]:
    """덧셈(Add), 순환 이동(Rotate), XOR로 상태를 섞는 ARX 한 라운드."""
    v0 = (v0 + v1) & MASK
    v1 = rotl(v1, 13) ^ v0
    v0 = rotl(v0, 32)
    v2 = (v2 + v3) & MASK
    v3 = rotl(v3, 16) ^ v2
    v0 = (v0 + v3) & MASK
    v3 = rotl(v3, 21) ^ v0
    v2 = (v2 + v1) & MASK
    v1 = rotl(v1, 17) ^ v2
    v2 = rotl(v2, 32)
    return v0, v1, v2, v3


def siphash24(key: bytes, data: bytes) -> int:
    """16바이트 비밀키와 입력 바이트에서 64비트 해시를 만든다."""
    if len(key) != 16:
        raise ValueError('SipHash 키는 16바이트여야 합니다')
    k0 = int.from_bytes(key[:8], 'little')
    k1 = int.from_bytes(key[8:], 'little')
    # ① somepseu / dorandom / lygenera / tedbytes 상수와 키를 XOR한다.
    v0 = 0x736F6D6570736575 ^ k0
    v1 = 0x646F72616E646F6D ^ k1
    v2 = 0x6C7967656E657261 ^ k0
    v3 = 0x7465646279746573 ^ k1
    end = len(data) - len(data) % 8
    # ② little-endian 8바이트 블록마다 압축 2라운드를 수행한다.
    for offset in range(0, end, 8):
        block = int.from_bytes(data[offset:offset + 8], 'little')
        v3 ^= block
        for _ in range(2):
            v0, v1, v2, v3 = sipround(v0, v1, v2, v3)
        v0 ^= block
    # ③ 마지막 블록의 최상위 바이트에는 전체 길이의 하위 8비트를 넣는다.
    block = ((len(data) & 0xFF) << 56) | int.from_bytes(data[end:], 'little')
    v3 ^= block
    for _ in range(2):
        v0, v1, v2, v3 = sipround(v0, v1, v2, v3)
    v0 ^= block
    # ④ 종료 표시 v2 ^= 0xFF 후 최종화 4라운드를 수행한다.
    v2 ^= 0xFF
    for _ in range(4):
        v0, v1, v2, v3 = sipround(v0, v1, v2, v3)
    return (v0 ^ v1 ^ v2 ^ v3) & MASK

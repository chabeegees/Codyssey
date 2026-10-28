# Python CLI Mini Redis

해시맵·이중 연결 리스트·최소 힙을 직접 구현한 문자열 저장소다.
Python 3.8 호환 문법과 표준 라이브러리만 사용하며, 종료하면 데이터는 사라진다.

## 실행

저장소 루트에서 실행한다. `python`이 없으면 `python3`를 사용한다.

```sh
cd B5-1/mini-redis
python -m unittest discover tests
python main.py
```

`exit`, `quit`, Ctrl+D, Ctrl+C로 종료한다. 명령어는 대소문자를 구분하지 않는다.
공백이 포함된 값이나 빈 문자열은 큰따옴표로 감싼다.

```text
mini-redis> SET greeting "안녕 세상"
OK
mini-redis> GET greeting
"안녕 세상"
```

## 파일 구성

```text
mini-redis/
├── main.py             # REPL 진입점
├── cli.py              # 파싱·명령 분기·출력
├── store.py            # 명령 로직·메모리·LRU·TTL
├── linked_list.py      # 이중 연결 리스트
├── hash_map.py         # 체이닝 해시맵
├── siphash.py          # SipHash-2-4
├── min_heap.py         # TTL 최소 힙
├── tests/              # 자료구조·저장소·CLI 테스트
├── scripts/
│   └── mission_commands.sh
└── README.md
```

## 명령어

| 명령 | 동작 |
| --- | --- |
| `SET key value` | 저장, 기존 TTL 초기화 |
| `GET key` | 값 조회, 없으면 `(nil)` |
| `DEL key` | 삭제 여부 반환 |
| `EXISTS key` | 존재 여부 반환 |
| `DBSIZE` / `KEYS` | 만료 키를 제외한 개수 / 목록 |
| `CONFIG SET maxmemory N` | 메모리 제한 설정, 0은 무제한 |
| `INFO memory` | 사용량·제한·LRU 제거 횟수 |
| `EXPIRE key seconds` | 만료 설정, 0 이하는 즉시 삭제 |
| `TTL key` | 남은 초, 무기한 `-1`, 없는 키 `-2` |

## 핵심 설계

- **연결 리스트:** head/tail sentinel로 경계 처리를 통일한다. 제거 후 prev/next를
  None으로 끊어 중복 제거와 참조 잔존을 막는다.
- **LRU:** 해시맵의 Entry가 자기 노드를 가리켜 O(1)에 이동한다.
  SET과 성공한 GET만 맨 앞으로 옮기며, 제거는 뒤에서 한다.
- **해시맵:** 버킷별 연결 리스트로 충돌을 처리한다. 랜덤 비밀키를 사용하는
  SipHash로 HashDoS용 충돌 키의 사전 예측을 어렵게 한다.
- **확장:** 로드 팩터 0.75 초과 시 버킷을 2배로 늘려 재배치한다.
  체인 길이를 제한하고, 등비급수 확장으로 평균 분할상환 삽입 O(1)을 유지한다.
- **TTL:** 최소 힙에 `(expire_at, key)`를 저장한다. 중간 삭제 대신 pop할 때
  현재 엔트리와 만료 시각을 비교하는 lazy deletion을 사용한다.
  만료 정리는 다음 명령 실행 시 수행하며, 테스트에는 clock을 주입한다.
- **메모리:** 키와 값의 UTF-8 바이트 합만 센다. 단일 엔트리가 제한보다 크면
  변경 전에 OOM을 반환한다. 성공한 SET 후 초과분은 LRU부터 제거한다.
  제한을 낮추는 CONFIG 자체는 키를 제거하지 않는다.

## 검증·시연

테스트는 자료구조, LRU, TTL, OOM, 한글 바이트 계산, CLI와 요구 시나리오를 검증한다.
`scripts/mission_commands.sh`는 **통째로 실행하지 말고 STEP별로 한 줄씩 복사한다.**

## 실행 로그

```text
[테스트 결과와 REPL 시나리오 로그를 여기에 붙인다]
```

## 트러블슈팅
- 모듈을 못 찾거나 테스트가 0개라면 `mini-redis` 폴더에서 실행한다.
- 수동 입력 중 시간이 지나 TTL이 작아질 수 있다. KEYS 순서는 실행마다 달라도 정상이다.



# Mini Redis — 핵심 개념 정리

## 1. Redis는 왜 빠른가

캐시는 **느리고 큰 원본 앞에 빠르고 작은 사본을 두는 것**이다. 이 패턴이 계층마다 반복된다.

| 계층 | 원본 (느림·큼) | 캐시 (빠름·작음) |
|---|---|---|
| 주소 변환 | Page table (RAM) | TLB (CPU 내부) |
| 데이터 | DB (디스크) | Redis (RAM) |

```
요청 → Redis ─ hit  → 즉시 응답 (μs)
            └ miss → DB 조회 (ms) → Redis에 저장 → 응답
```

빠른 이유는 두 가지다.
1. **저장 위치**: 디스크가 아닌 RAM
2. **자료구조**: RAM에서도 O(n) 탐색이면 느리다. 해시맵으로 O(1) 조회 ← 이 과제의 범위

RAM은 작으므로 꽉 차면 버릴 기준(LRU)과 만료(TTL)가 필요하다. 버려도 원본은 DB에 있다.

---

## 2. 자료구조별 역할

| 구조 | 답하는 질문 | 비용 |
|---|---|---|
| 해시맵 | 이 키 어디 있나? | O(1) 평균 |
| 이중 연결 리스트 | 가장 안 쓴 키는? / 방금 쓴 키를 맨 앞으로 | O(1) |
| 최소 힙 | 가장 먼저 만료되는 키는? | peek O(1), push/pop O(log n) |

### 2-1. 이중 연결 리스트

```
[head] ⇄ [A] ⇄ [B] ⇄ [C] ⇄ [tail]     head/tail = 더미 노드(sentinel)
```

- **prev가 필요한 이유**: C를 빼려면 앞 노드 B를 고쳐야 한다. 단일 리스트는 B를 찾으려 head부터 O(n) 탐색한다.
- **sentinel을 두는 이유**: 모든 실제 노드의 앞뒤에 항상 노드가 있어 맨 앞/뒤/빈 리스트 분기가 사라진다.

```python
def remove_node(node):
    node.prev.next = node.next
    node.next.prev = node.prev
    node.prev = node.next = None   # 리스트 밖 노드는 포인터를 끊는다
```

- `move_to_front = remove_node + insert_front`
- remove_node는 DEL·LRU 제거에서 단독으로도 쓰이므로 포인터를 None으로 끊는다.
  - 중복 제거 시 즉시 에러 → 버그가 조용히 리스트를 망가뜨리지 않음
  - 제거된 노드가 옛 이웃을 참조로 붙잡지 않음
- 불변식: **리스트 안 노드는 앞뒤가 서로 맞게 연결, 리스트 밖 노드는 prev/next가 None**

### 2-2. 해시맵 (체이닝)

```
index = hash(key) % capacity

[0] →
[1] → ("user:1","Alice") ⇄ ("user:9","Zed")   ← 같은 칸이면 체인으로 연결
[2] → ("user:2","Bob")
[3] →
```

**해시 함수 (djb2)**

```python
h = 5381
for c in key:
    h = (h * 33 + ord(c)) & 0xFFFFFFFF   # ord: 문자→코드값, &: 32비트로 자름
```

- `*33`: 앞 글자를 높은 자리로 밀어 **순서를 반영** (`"12"` ≠ `"21"`). `h*33 = (h<<5)+h`로 빠름
- `& 0xFFFFFFFF`: 파이썬 int는 무한이라 자르지 않으면 숫자가 계속 커진다
- 내장 `hash()`는 "직접 설계" 요구사항 위반

**충돌은 두 단계**

| 종류 | 원인 | 해결 |
|---|---|---|
| 해시 충돌 | 키가 다른데 해시값이 같음 | 좋은 해시 함수 |
| 버킷 충돌 | 해시값은 다른데 `% capacity` 결과가 같음 (훨씬 흔함) | 리사이즈 |

둘 다 "같은 칸에 여러 개" → 체인으로 저장한다.

**나쁜 해시 예시**

| 함수 | 문제 |
|---|---|
| `ord(key[0])` | `user:1`, `user:2`… 전부 같은 칸 → O(n) |
| `sum(ord(c))` | 순서 무시 → `"abc"`=`"cab"`, `"user:12"`=`"user:21"` |

해시값 자체가 같으면 capacity를 아무리 늘려도 같은 칸에 몰린다. **리사이즈는 버킷 충돌만 해결한다.**

**로드 팩터와 리사이즈**

```
로드 팩터 = 키 개수 / 버킷 개수 = 체인의 평균 길이
```

- 0.75 초과 시 버킷 2배. 0.75는 메모리와 속도의 경험적 타협값 (Java HashMap 기본값)
- 리사이즈 = 새 배열을 만들고 모든 키를 `hash % 새capacity`로 다시 넣는 것. 같은 번호 칸에 가도 1회로 센다
- 2배 확장 시 새 위치는 `i` 또는 `i + 옛capacity` 둘 중 하나

**왜 2배면 평균 O(1)인가 (amortized)**

용량 1에서 꽉 차면 2배로 16개를 넣으면:

| 리사이즈 시점 | 2번째 | 3번째 | 5번째 | 9번째 |
|---|---|---|---|---|
| 옮긴 개수 | 1 | 2 | 4 | 8 |

- 옮긴 총합 1+2+4+8 = 15 < 16. 다음 항이 앞 항 전체 합보다 크므로 **항상 n 미만**
- 총비용 < 넣기 n + 옮기기 n = 2n → **2n ÷ n = 2, 상수 → O(1)**
- 1칸씩 늘리면 옮긴 총합 1+2+…+n ≈ n²/2 → 한 번당 O(n)

### 2-3. 최소 힙

완전 이진 트리를 배열로 표현한다. 부모 ≤ 자식이므로 루트가 최솟값.

```
배열 [1,3,2,7,4,5]          1
                         /   \
                        3     2
                       / \   /
                      7   4 5

parent(i) = (i-1)//2   left(i) = 2i+1   right(i) = 2i+2
```

힙이 지킬 규칙은 두 개다: **① 모양(빈칸 없는 완전 이진 트리) ② 순서(부모 ≤ 자식)**

| 연산 | 모양 유지 | 순서 복구 | 비용 |
|---|---|---|---|
| push | 배열 맨 뒤에 추가 | `_heapify_up`: 부모보다 작으면 swap | O(log n) |
| pop | 맨 끝 원소를 루트로 이동 | `_heapify_down`: 더 작은 자식과 swap | O(log n) |

- 배열 끝에서만 넣고 빼면 모양은 절대 안 깨진다. 깨지는 건 순서뿐이고, 그건 **한 줄기(높이 log n)**만 고치면 된다.
- 루트를 빼고 자식을 끌어올리면 구멍이 배열 중간에 생겨 인덱스 공식이 무너진다.
- 매번 전체 정렬은 O(n log n): log n 단계 × 단계당 n번 비교. 힙은 **최솟값만 보장**하므로 더 싸다.
- 원소는 `(expire_at, key)` 튜플. 튜플은 첫 원소부터 비교하므로 만료 시각 기준 정렬.

### 2-4. CFS는 왜 RB트리인가

CFS는 sleep/block된 태스크를 **트리 중간에서 삭제**해야 한다. 힙은 중간 원소를 찾는 데 O(n)이 들어 부적합하고, RB트리는 삽입·삭제·탐색 모두 O(log n)이다.
이 과제의 힙은 중간 삭제(DEL, SET 덮어쓰기)를 **lazy deletion**으로 회피한다.

---

## 3. 과제 구조

```
mini-redis/
├── main.py          # 진입점, REPL
├── cli.py           # 파싱(따옴표), 명령 분기, 출력 포맷
├── store.py         # MiniRedis 본체: 명령 로직, 메모리·LRU·TTL
├── linked_list.py   # 이중 연결 리스트
├── hash_map.py      # 해시맵
├── min_heap.py      # 최소 힙
└── README.md
```

```
            store: HashMap (key → Entry)
"user:2" ─► Entry { key, value, node, expire_at=105 }
                              │
                              ▼
LRU:  [head] ⇄ [user:3] ⇄ [user:2] ⇄ [tail]
              (최근 사용)   (가장 오래됨 → 제거 대상)

TTL:  heap [(105,"user:2"), ...]
```

해시맵이 키 → 노드를 바로 가리키고, 리스트가 순서를 O(1)로 바꾼다. **둘을 합쳐야 O(1) LRU.**

### 3-1. used_memory

```
used_memory = Σ( len(utf8(key)) + len(utf8(value)) )
```

- 따옴표는 세지 않는다. `"Alice"` → `Alice` 5바이트
- 글자 수가 아닌 **바이트 수**: `len(s.encode("utf-8"))`. 한글 1글자 = 3바이트

### 3-2. SET 흐름 (maxmemory 30)

| 명령 | size | used | 리스트 (앞=최근) |
|---|---|---|---|
| `SET user:1 "Alice"` | 6+5=11 | 11 | user:1 |
| `SET user:2 "Bob"` | 6+3=9 | 20 | user:2, user:1 |
| `SET user:3 "Charlie"` | 6+7=13 | 33 > 30 | user:3, user:2, user:1 |
| → tail쪽 user:1 제거 | -11 | 22 ≤ 30 | user:3, user:2 |

1. 만료 체크 (만료면 삭제 후 없는 키 취급)
2. 엔트리 크기 > maxmemory → OOM 에러, 저장 안 함
3. 기존 키: 옛 크기 차감, 값 교체, **TTL 초기화**, move_to_front
4. 새 키: 해시맵 put, insert_front
5. used_memory 갱신 → 초과 시 tail쪽부터 제거, evicted_keys 누적

### 3-3. GET 흐름

```
GET key
 ├ 없음            → (nil)
 ├ expire_at ≤ now → 삭제 → (nil), LRU 갱신 안 함
 └ 정상            → move_to_front → "value"
```

### 3-4. TTL lazy deletion

```
EXPIRE user:2 3 → Entry.expire_at = now+3, heap.push((now+3,"user:2"))
SET user:2 "X"  → Entry.expire_at = None   (힙은 안 건드림)

heap.pop() → (now+3,"user:2")
  키가 없거나 Entry.expire_at ≠ 꺼낸 값 → 옛 기록이므로 무시
```

---

## 4. 실제 Redis와 비교

### 4-1. TTL: 별도 테이블 + 샘플링

```
db ├ dict    : key → value
   └ expires : key → 만료시각   (TTL 있는 키만)
```

- **Passive**: 키 접근 시 만료 확인 후 삭제
- **Active**: 초당 10회, expires에서 20개 샘플 → 만료분 삭제 → 만료 비율 > 25%면 반복 (시간 제한 있음)
- 힙 유지 비용 없이 "남은 만료 키 ≈ 25% 이하"를 확률적으로 보장

### 4-2. 근사 LRU

- 연결 리스트 없이 객체마다 **마지막 접근 시각(24비트)**만 기록
- 메모리 초과 시 키 5개(`maxmemory-samples`) 샘플 → eviction pool(16칸)에 idle 순 정렬 → 가장 오래된 키 제거 → 반복
- 이유: 키당 포인터 16바이트와 GET마다 리스트 조작을 없애 메모리·CPU 절약
- 정책은 `allkeys-lru`, `volatile-lru`, `allkeys-lfu` 등 선택. 기본값 `noeviction`

| | 이 과제 | 실제 Redis |
|---|---|---|
| TTL | 힙 + lazy deletion (정확) | expires 테이블 + 샘플링 (확률적) |
| LRU | 해시맵 + 이중 연결 리스트 (정확) | 접근 시각 + 샘플링 (근사) |
| 목적 | 원리 학습 | 대규모 환경에서 메모리·CPU 절약 |

### 4-3. 해시 함수

| 이름 | 특징 | 사용처 |
|---|---|---|
| djb2 | 단순, 적당한 분포 | 교육용 |
| FNV-1a | 단순, 분포 조금 나음 | 소형 테이블 |
| MurmurHash3 | 빠르고 분포 좋음 | 예전 Redis, Hadoop |
| xxHash | 매우 빠름 | 대용량 처리 |
| SipHash | **랜덤 비밀키**로 결과 예측 불가 | 현재 Redis, 파이썬 str |

- djb2는 고정 함수라 **HashDoS**(같은 칸에 몰리는 키를 대량 투입)에 취약하다.
- SipHash는 실행마다 랜덤 키(`os.urandom(16)`)를 섞어 공격자가 충돌 키를 만들 수 없다. 대신 순수 파이썬에선 느리다.
- 이 과제는 djb2로 충분. 실제 서비스는 SipHash 계열을 쓴다.

---

## 5. 동료평가 예상 질문

| 질문 | 답 |
|---|---|
| 해시맵 + 리스트가 왜 O(1) LRU인가 | 해시맵이 노드 위치를 O(1)로 찾고, 리스트가 prev/next 교체로 O(1) 이동 |
| 왜 힙인가 | 필요한 건 가장 빠른 만료 하나. 전체 정렬 불필요, peek O(1) |
| 힙 중간 삭제는 | lazy deletion: pop 시 유효성 확인 후 무시 |
| 0.75, 2배인 이유 | 체인 평균 길이 제한 / 2배 확장 시 리사이즈 총비용 < n → amortized O(1) |
| djb2를 고른 이유 | 곱셈으로 순서 반영, 구현 단순. 실서비스는 HashDoS 방어 위해 SipHash |
| remove_node에서 None 처리 | 단독 호출 시 중복 제거·참조 잔존 방지, 불변식 유지 |
| 실제 Redis와 차이 | 키당 포인터 오버헤드 때문에 샘플링 기반 근사 LRU·확률적 만료 사용 |
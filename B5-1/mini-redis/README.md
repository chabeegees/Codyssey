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
- 추가 문제와 해결 기록: 작성 예정.

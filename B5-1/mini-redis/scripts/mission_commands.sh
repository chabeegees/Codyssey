# 통째로 실행하지 말 것! STEP별로 필요한 한 줄만 복사해 실행한다.
# 셸 명령과 Mini Redis REPL 입력이 섞여 있다.
# 실수로 sh/bash로 실행하면 아래 안내 후 즉시 종료한다.
echo '통째로 실행하지 말 것: 파일을 읽고 STEP별 명령 한 줄만 복사하세요.'
exit 1

# STEP 1 — 터미널에서 저장소 루트(Codyssey) 기준으로 이동
cd B5-1/mini-redis

# STEP 2 — 터미널에서 테스트 실행 (python이 없으면 python3 사용)
python -m unittest discover tests

# STEP 3 — 터미널에서 REPL 실행 (새 프로세스로 빈 저장소에서 시작)
python main.py

# STEP 4 — 아래부터 mini-redis> 프롬프트에 한 줄씩 입력
CONFIG SET maxmemory 30
SET user:1 "Alice"
SET user:2 "Bob"
SET user:3 "Charlie"

# STEP 5 — user:1은 LRU 제거됨. 메모리 22 / 제한 30 / 제거 1
GET user:1
INFO memory
KEYS

# STEP 6 — 다음 두 줄은 바로 이어서 입력. TTL은 2 또는 3
EXPIRE user:2 3
TTL user:2

# STEP 7 — 실제로 3초 이상 기다린 뒤 입력. (nil), (integer) -2
GET user:2
TTL user:2

# STEP 8 — 표준 오류 확인
CONFIG SET maxmemory abc
GET
HELLO

# STEP 9 — REPL 종료
quit

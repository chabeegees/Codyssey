"""입력 해석과 Redis 스타일 출력은 저장소 로직에서 분리한다."""

from typing import List, Optional

from store import MiniRedis

INTEGER_ERROR = '(error) ERR value is not an integer or out of range'


def parse_command(line: str) -> List[str]:
    """큰따옴표 안 공백/빈 문자열을 보존하고 따옴표 자체는 제거한다.

    따옴표 안의 역슬래시는 큰따옴표와 역슬래시만 이스케이프한다.
    상태 두 개(따옴표 내부, 토큰 시작 여부)로 단순하게 해석한다.
    """
    tokens: List[str] = []
    chars: List[str] = []
    quoted = False
    started = False
    index = 0
    while index < len(line):
        char = line[index]
        if quoted and char == '\\' and index + 1 < len(line):
            if line[index + 1] in ('"', '\\'):
                chars.append(line[index + 1])
                index += 2
                continue
        if char == '"':
            quoted = not quoted
            started = True
        elif char.isspace() and not quoted:
            if started:
                tokens.append(''.join(chars))
                chars = []
                started = False
        else:
            chars.append(char)
            started = True
        index += 1
    if quoted:
        raise ValueError('unbalanced quotes in request')
    if started:
        tokens.append(''.join(chars))
    return tokens


def parse_integer(value: str) -> int:
    """ASCII 10진수만 허용한다. Redis처럼 부호 있는 64비트 범위를 검사한다."""
    digits = value[1:] if value[:1] in ('+', '-') else value
    if not digits or any(char < '0' or char > '9' for char in digits):
        raise ValueError('invalid integer')
    number = int(value)
    if number < -(1 << 63) or number > (1 << 63) - 1:
        raise ValueError('integer out of range')
    return number


def quote(value: str) -> str:
    """문자열의 큰따옴표/역슬래시/개행을 출력용으로 이스케이프한다."""
    escaped = value.replace('\\', '\\\\').replace('"', '\\"')
    escaped = escaped.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
    return '"' + escaped + '"'


class CLI:
    """execute는 출력 문자열을 반환하고 종료 요청일 때만 None을 반환한다."""

    def __init__(self, store: Optional[MiniRedis] = None) -> None:
        self.store = MiniRedis() if store is None else store

    @staticmethod
    def _arity_error(command: str) -> str:
        return "(error) ERR wrong number of arguments for '{}' command".format(command)

    @staticmethod
    def _unknown(command: str) -> str:
        return "(error) ERR unknown command '{}'".format(command)

    def execute(self, line: str) -> Optional[str]:
        # 잘못된 명령도 하나의 명령 실행이므로 만료 기록을 먼저 정리한다.
        self.store._active_expire()
        try:
            tokens = parse_command(line)
        except ValueError as error:
            return '(error) ERR ' + str(error)
        if not tokens:
            return ''
        original = tokens[0]
        command = original.upper()
        # 명령 테이블 대신 명시적 분기로 인자 수와 실행 경로를 쉽게 읽게 한다.
        if command in ('EXIT', 'QUIT'):
            return None if len(tokens) == 1 else self._arity_error(original)
        if command == 'SET':
            expected = 3
        elif command in ('GET', 'DEL', 'EXISTS', 'TTL', 'INFO'):
            expected = 2
        elif command in ('DBSIZE', 'KEYS'):
            expected = 1
        elif command == 'EXPIRE':
            expected = 3
        elif command == 'CONFIG':
            expected = 4
        else:
            return self._unknown(original)
        if len(tokens) != expected:
            return self._arity_error(original)

        try:
            if command == 'SET':
                return self.store.set(tokens[1], tokens[2])
            if command == 'GET':
                value = self.store.get(tokens[1])
                return '(nil)' if value is None else quote(value)
            if command == 'DEL':
                result = self.store.delete(tokens[1])
            elif command == 'EXISTS':
                result = self.store.exists(tokens[1])
            elif command == 'DBSIZE':
                result = self.store.dbsize()
            elif command == 'TTL':
                result = self.store.ttl(tokens[1])
            elif command == 'EXPIRE':
                result = self.store.expire(tokens[1], parse_integer(tokens[2]))
            elif command == 'KEYS':
                keys = self.store.keys()
                if not keys:
                    return '(empty array)'
                return '\n'.join('{}) {}'.format(i, quote(key))
                                 for i, key in enumerate(keys, 1))
            elif command == 'CONFIG':
                if tokens[1].upper() != 'SET' or tokens[2].lower() != 'maxmemory':
                    return self._unknown(original)
                return self.store.config_set_maxmemory(parse_integer(tokens[3]))
            else:  # INFO
                if tokens[1].lower() != 'memory':
                    return self._unknown(original)
                return self.store.info_memory()
            return '(integer) {}'.format(result)
        except (ValueError, OverflowError):
            return INTEGER_ERROR
        except MemoryError as error:
            return '(error) OOM ' + str(error)

    def run(self) -> None:
        """EOF/Ctrl+C는 traceback 없이 종료한다. 입력과 출력만 담당한다."""
        while True:
            try:
                line = input('mini-redis> ')
                result = self.execute(line)
                if result is None:
                    break
                if result:
                    print(result)
            except (EOFError, KeyboardInterrupt):
                print()
                break

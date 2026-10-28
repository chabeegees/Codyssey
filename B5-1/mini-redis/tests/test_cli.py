import unittest
from unittest.mock import patch

from cli import CLI, INTEGER_ERROR, parse_command, parse_integer
from store import MiniRedis
from test_store import FakeClock


class CLITests(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.cli = CLI(MiniRedis(clock=self.clock))

    def test_required_mission_scenario(self):
        c = self.cli
        for line in ['CONFIG SET maxmemory 30', 'SET user:1 "Alice"',
                     'SET user:2 "Bob"', 'SET user:3 "Charlie"']:
            self.assertEqual(c.execute(line), 'OK')
        self.assertEqual(c.execute('GET user:1'), '(nil)')
        self.assertEqual(c.execute('INFO memory'),
                         'used_memory:22\nmaxmemory:30\nevicted_keys:1')
        # 랜덤 SipHash 때문에 KEYS 순서는 고정하지 않고 번호와 키를 검사한다.
        lines = c.execute('KEYS').splitlines()
        self.assertEqual(len(lines), 2)
        self.assertTrue(lines[0].startswith('1) '))
        self.assertTrue(lines[1].startswith('2) '))
        self.assertEqual(sorted(line[3:] for line in lines), ['"user:2"', '"user:3"'])
        self.assertEqual(c.execute('EXPIRE user:2 3'), '(integer) 1')
        self.assertIn(c.execute('TTL user:2'), ['(integer) 2', '(integer) 3'])
        self.clock.now += 3
        self.assertEqual(c.execute('GET user:2'), '(nil)')
        self.assertEqual(c.execute('TTL user:2'), '(integer) -2')
        self.assertEqual(c.execute('CONFIG SET maxmemory abc'), INTEGER_ERROR)
        self.assertEqual(c.execute('GET'),
                         "(error) ERR wrong number of arguments for 'GET' command")
        self.assertEqual(c.execute('HELLO'), "(error) ERR unknown command 'HELLO'")

    def test_parser_quotes_spaces_and_escapes(self):
        self.assertEqual(parse_command('  SET  "a b" ""  '), ['SET', 'a b', ''])
        self.assertEqual(parse_command('SET a "hello world"'), ['SET', 'a', 'hello world'])
        self.assertEqual(parse_command(r'SET a "say \"hi\" \\ ok"'),
                         ['SET', 'a', 'say "hi" \\ ok'])
        self.assertEqual(self.cli.execute('SET a "hello'),
                         '(error) ERR unbalanced quotes in request')
        self.assertEqual(self.cli.execute('   '), '')

    def test_case_empty_strings_and_all_basic_outputs(self):
        c = self.cli
        self.assertEqual(c.execute('keys'), '(empty array)')
        self.assertEqual(c.execute('sEt "" ""'), 'OK')
        self.assertEqual(c.execute('gEt ""'), '""')
        self.assertEqual(c.execute('eXiStS ""'), '(integer) 1')
        self.assertEqual(c.execute('dBsIzE'), '(integer) 1')
        self.assertEqual(c.execute('dEl ""'), '(integer) 1')
        self.assertEqual(c.execute('DEL ""'), '(integer) 0')
        self.assertEqual(c.execute('cOnFiG sEt MAXMEMORY 2'), 'OK')
        self.assertEqual(c.execute('iNfO MEMORY'),
                         'used_memory:0\nmaxmemory:2\nevicted_keys:0')
        self.assertEqual(c.execute('SET big value'),
                         "(error) OOM command not allowed when used_memory > 'maxmemory'")

    def test_invalid_integers_and_arities(self):
        c = self.cli
        for value in ['abc', '-1', '1.5', '1_000', '１２', '9223372036854775808', '""']:
            with self.subTest(value=value):
                self.assertEqual(c.execute('CONFIG SET maxmemory ' + value), INTEGER_ERROR)
        for value in ['abc', '1.2', '9223372036854775808']:
            self.assertEqual(c.execute('EXPIRE missing ' + value), INTEGER_ERROR)
        self.assertEqual(parse_integer('+3'), 3)
        self.assertEqual(parse_integer('-9223372036854775808'), -(1 << 63))
        for command in ['SET', 'GET a b', 'DEL', 'EXISTS', 'DBSIZE a', 'KEYS a',
                        'CONFIG SET', 'INFO', 'EXPIRE a', 'TTL', 'quit extra']:
            self.assertIn('wrong number of arguments', c.execute(command))
        self.assertIn('unknown command', c.execute('CONFIG GET maxmemory 1'))
        self.assertIn('unknown command', c.execute('INFO other'))

    def test_repl_exit_eof_and_interrupt(self):
        for ending in ['exit', 'QUIT', EOFError(), KeyboardInterrupt()]:
            with self.subTest(ending=ending):
                with patch('builtins.input', side_effect=['SET a b', ending]) as read:
                    with patch('builtins.print') as output:
                        self.cli.run()
                        output.assert_any_call('OK')
                        read.assert_called_with('mini-redis> ')

    def test_invalid_command_also_expires_data(self):
        self.cli.execute('SET a b')
        self.cli.execute('EXPIRE a 1')
        self.clock.now += 1
        self.cli.execute('HELLO')
        self.assertEqual(self.cli.store.used_memory, 0)

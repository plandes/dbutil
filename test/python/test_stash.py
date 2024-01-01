from pathlib import Path
from zensols.config import ImportIniConfig, ImportConfigFactory
from zensols.persist import Stash
from util import SqliteTestCase
from sql import Person


class TestStash(SqliteTestCase):
    def setUp(self):
        super().setUp()
        self.fac = ImportConfigFactory(
            ImportIniConfig(Path('test-resources/sqlitestash.conf')),
            reload=True)

    def _test_init(self, stash: Stash):
        self.assertFalse(Path('target/test.sqlite3').exists())

        self.assertEqual(0, len(stash))
        self.assertTrue(Path('target/test.sqlite3').exists())

    def _test_crud(self, stash: Stash):
        self._test_init(stash)

        # insert
        self.assertFalse('jane' in stash)
        stash.dump('jane', 'usa')
        self.assertTrue('jane' in stash)
        self.assertEqual(1, len(stash))
        self.assertEqual(('jane',), tuple(stash.keys()))
        self.assertEqual('usa', stash['jane'])

        # multiple
        stash.dump('bob', 'brazil')
        self.assertEqual('brazil', stash.load('bob'))
        self.assertEqual({'jane', 'bob'}, set(stash.keys()))
        self.assertEqual(2, len(stash))
        self.assertEqual({'usa', 'brazil'}, set(stash.values()))

        # update
        stash.dump('bob', 'poland')
        self.assertEqual('poland', stash['bob'])
        self.assertEqual(2, len(stash))

        # delete
        stash.delete('jane')
        self.assertEqual(1, len(stash))
        self.assertEqual({'bob'}, set(stash.keys()))
        self.assertEqual('poland', stash['bob'])

        # dup
        stash.dump('frank', 'germany')
        stash.dump('frank', 'germany')
        self.assertEqual(2, len(stash))

        return
        # clear
        stash.clear()
        self.assertEqual(0, len(stash))
        self.assertEqual(0, len(tuple(stash.keys())))
        self.assertEqual(0, len(tuple(stash.values())))

    def _test_mixed_type(self, stash: Stash):
        stash.dump('anint', 5)
        self.assertEqual(int, type(stash['anint']))
        self.assertEqual(stash['anint'], 5)

        nasc = Person('paul', 21, 'id123')
        stash.dump('nasc', nasc)

        diff = Person('paulie', 30, 'id123')
        self.assertNotEqual(nasc, diff)

        self.assertEqual(2, len(stash))
        copy: Person = stash['nasc']
        self.assertNotEqual(id(nasc), id(copy))
        self.assertEqual(copy, nasc)
        self.assertNotEqual(copy, diff)

    def test_crud_str(self):
        stash = self.fac('db_str')
        self._test_crud(stash)

    def test_crud_binary(self):
        stash = self.fac('db_bin')
        self._test_crud(stash)

    def test_mixed_type(self):
        stash = self.fac('db_bin')
        self._test_init(stash)
        self._test_mixed_type(stash)

    def test_crud_json(self):
        stash = self.fac('db_json')
        stash_str = self.fac('db_str')

        self._test_init(stash)
        self._test_mixed_type(stash)

        stash.dump('anint', 5)
        self.assertEqual(int, type(stash['anint']))
        self.assertEqual(stash['anint'], 5)

        nasc = Person('paul', 21, 'id123')
        stash.dump('nasc', nasc)
        should = '{"py/object": "sql.Person", "id": "id123", "name": "paul", "age": 21}'
        self.assertEqual(should, stash_str['nasc'])

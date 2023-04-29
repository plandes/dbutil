from pathlib import Path
from zensols.db import DBError, BeanStash
from sql import Person
from util import SqliteTestCase


class TestSqlLite(SqliteTestCase):
    def test_person_persister(self):
        persister = self.fac.instance('person_db_persister')
        db_path = Path(self.target_path, 'sql-test1.db')
        self.assertFalse(db_path.exists())
        self.assertEqual(1, persister.insert_row('paul', 23))
        self.assertEqual(2, persister.insert_row('sue', 33))
        self.assertTrue(db_path.exists())
        peeps = persister.get('dict')
        self.assertEqual(2, len(peeps))
        self.assertEqual({'id': 1, 'name': 'paul', 'age': 23}, peeps[0])
        self.assertEqual({'id': 2, 'name': 'sue', 'age': 33}, peeps[1])
        peeps = persister.get('tuple')
        self.assertEqual(('paul', 23, 1), peeps[0])
        peeps = persister.get(Person)
        self.assertEqual('id: 1, name: paul, age: 23', str(peeps[0]))
        self.assertEqual('id: 2, name: sue, age: 33', str(peeps[1]))
        persister.conn_manager.drop()
        self.assertFalse(db_path.exists())

    def test_stash(self):
        def key_change():
            stash.dump('5', peep)

        persister = self.fac.instance('inst_db_persister', row_factory=Person)
        stash = BeanStash(persister)
        db_path = Path(self.target_path, 'sql-test2.db')
        self.assertFalse(db_path.exists())
        peep = Person('paul', 24)
        stash.dump(None, peep)
        self.assertTrue(db_path.exists())
        self.assertEqual(1, len(stash))
        self.assertEqual(1, peep.id)
        self.assertTrue(stash.exists(1))
        self.assertTrue(stash.exists('1'))
        self.assertEqual('id: 1, name: paul, age: 24', str(stash['1']))
        self.assertEqual('id: 1, name: paul, age: 24', str(stash[1]))
        peep.name = 'joe'
        stash.dump(None, peep)
        self.assertEqual('id: 1, name: joe, age: 24', str(stash['1']))
        peep = Person('bob', 55)
        stash.dump('1', peep)
        self.assertEqual('id: 1, name: bob, age: 55', str(stash['1']))
        self.assertEqual(1, len(stash))
        with self.assertRaises(DBError):
            key_change()
        self.assertEqual(2, peep.id)
        self.assertEqual(2, len(stash))
        self.assertEqual('id: 2, name: bob, age: 55', str(stash['2']))
        persister.delete('1')
        self.assertEqual(1, len(stash))
        pid, peep = next(iter(stash))
        self.assertEqual(('2', 'id: 2, name: bob, age: 55'), (pid, str(peep)))

    def test_inst_persister(self):
        self._test_inst_persister()

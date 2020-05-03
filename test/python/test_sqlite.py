import logging
import unittest
from pathlib import Path
import shutil
from zensols.config import ImportConfigFactory
from zensols.db import (
    #DbPersisterFactory,
    DbPersister,
    BeanStash,
)
from config import AppConfig
from sql import Person

logger = logging.getLogger(__name__)

if 0:
    logging.basicConfig(level=logging.INFO)
    logger.setLevel(logging.DEBUG)


class PersonPersister(DbPersister):
    def insert_row(self, name: str, age: int):
        return self.execute_no_read('insert_person', params=(name, age,))

    def get(self, row_factory='tuple'):
        sql = self.sql_entries['select_people']
        return self.execute(sql, row_factory=row_factory)


#DbPersisterFactory.register(PersonPersister)


class TestSqlLite(unittest.TestCase):
    def setUp(self):
        self.config = AppConfig.instance()
        self.target_path = Path('./target')
        if self.target_path.exists():
            shutil.rmtree(self.target_path)
        self.fac = ImportConfigFactory(self.config)

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

    def test_inst_persister(self):
        persister = self.fac.instance('inst_db_persister', row_factory=Person)
        db_path = Path(self.target_path, 'sql-test2.db')
        self.assertFalse(db_path.exists())
        self.assertEqual(0, persister.get_count())
        self.assertEqual(1, persister.insert_row('paul', 23))
        self.assertEqual(2, persister.insert_row('sue', 33))
        self.assertTrue(db_path.exists())
        peeps = persister.get()
        self.assertTrue(2, len(peeps))
        self.assertEqual({'id': 1, 'name': 'paul', 'age': 23}, peeps[0].get_attrs())
        self.assertEqual({'id': 2, 'name': 'sue', 'age': 33}, peeps[1].get_attrs())
        peeps = persister.get()
        self.assertEqual((1, 'paul', 23), peeps[0].get_row())
        self.assertEqual(('paul', 23), peeps[0].get_insert_row())
        peeps = persister.get()
        self.assertEqual('id: 1, name: paul, age: 23', str(peeps[0]))
        self.assertEqual('id: 2, name: sue, age: 33', str(peeps[1]))
        peeps = persister.get()
        self.assertEqual('id: 1, name: paul, age: 23', str(peeps[0]))
        self.assertEqual('id: 2, name: sue, age: 33', str(peeps[1]))
        new_peeps = (('bob', 42), ('jane', 90),)
        self.assertEqual(4, persister.insert_rows(new_peeps))
        peeps = persister.get()
        self.assertEqual({'id': 3, 'name': 'bob', 'age': 42}, peeps[0].get_attrs())
        self.assertEqual({'id': 4, 'name': 'jane', 'age': 90}, peeps[1].get_attrs())
        bean = Person('kyle', 52)
        self.assertEqual(None, bean.id)
        self.assertEqual(5, persister.insert(bean))
        self.assertEqual(5, bean.id)
        self.assertEqual(((5,),), persister.execute_by_name('people_count'))
        peep = persister.get_by_id(2)
        self.assertEqual('id: 2, name: sue, age: 33', str(peep))
        peep = persister.get_by_id(5)
        self.assertEqual('id: 5, name: kyle, age: 52', str(peep))
        self.assertEqual(None, persister.get_by_id(100))
        self.assertTrue(persister.exists(1))
        self.assertTrue(persister.exists(5))
        self.assertFalse(persister.exists(100))
        peep = persister.get_by_id(2)
        peep.age = 41
        self.assertTrue(2, persister.update(peep))
        peep = persister.get_by_id(2)
        self.assertEqual('id: 2, name: sue, age: 41', str(peep))
        self.assertTrue(persister.exists(2))
        self.assertTrue(2, persister.delete(2))
        self.assertFalse(persister.exists(2))
        self.assertEqual(((4,),), persister.execute_by_name('people_count'))
        self.assertEqual(4, persister.get_count())
        self.assertEqual((1, 3, 4, 5), tuple(persister.get_keys()))
        new_peeps = (Person('jake', 62), Person('christina', 22),)
        self.assertEqual(7, persister.insert_beans(new_peeps))
        peeps = persister.get()
        self.assertEqual({'id': 6, 'name': 'jake', 'age': 62}, peeps[2].get_attrs())
        self.assertEqual({'id': 7, 'name': 'christina', 'age': 22}, peeps[1].get_attrs())

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
        with self.assertRaises(ValueError):
            key_change()
        self.assertEqual(2, peep.id)
        self.assertEqual(2, len(stash))
        self.assertEqual('id: 2, name: bob, age: 55', str(stash['2']))
        persister.delete('1')
        self.assertEqual(1, len(stash))
        pid, peep = next(iter(stash))
        self.assertEqual((2, 'id: 2, name: bob, age: 55'), (pid, str(peep)))

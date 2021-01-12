from zensols.db import DbPersister
from util import SqliteTestCase


class TestPandas(SqliteTestCase):
    def test_sql(self):
        persister = self._test_inst_persister()
        self.assertTrue(isinstance(persister, DbPersister))
        df = persister.execute('select * from person', row_factory='pandas')
        self.assertEqual(6, len(df))
        self.assertEqual(['name', 'age'], list(df.columns))
        self.assertEqual('paul bob jane kyle jake christina'.split(),
                         df['name'].tolist())
        self.assertEqual([23, 42, 90, 52, 62, 22], df['age'].tolist())

    def test_by_name(self):
        persister = self._test_inst_persister()
        self.assertTrue(isinstance(persister, DbPersister))
        df = persister.execute_by_name('select_people', row_factory='pandas')
        self.assertEqual(6, len(df))
        self.assertEqual(['name', 'age', 'id'], list(df.columns))
        self.assertEqual('bob christina jake jane kyle paul'.split(),
                         df['name'].tolist())
        self.assertEqual([42, 22, 62, 90, 52, 23], df['age'].tolist())

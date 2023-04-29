from zensols.db import cursor
from util import SqliteTestCase


class TestCursor(SqliteTestCase):
    def test_person_persister(self):
        persister = self.fac.instance('person_db_persister')
        self.assertEqual(1, persister.insert_row('paul', 23))
        self.assertEqual(2, persister.insert_row('sue', 33))
        with cursor(persister, name='select_people') as c:
            for i, row in enumerate(c):
                if i == 0:
                    self.assertEqual(('paul', 23, 1), row)
                elif i == 1:
                    self.assertEqual(('sue', 33, 2), row)
                else:
                    self.assertTrue(False, 'bad iteration')
        self.assertEqual(i, 1)

import logging
import unittest
from config import AppConfig
from zensols.db import (
    DynamicDataParser,
)

logger = logging.getLogger(__name__)

if 0:
    logging.basicConfig(level=logging.INFO)
    logger.setLevel(logging.DEBUG)


class TestParser(unittest.TestCase):
    def setUp(self):
        self.config = AppConfig.instance()

    def test_parse(self):
        db_path = self.config.get_option_path('sql_file', 'parse-test')
        parser = DynamicDataParser(db_path)
        secs = parser.sections
        self.assertEqual(2, len(secs))
        self.assertEqual(set('create_idx create_tables'.split()), secs.keys())
        self.assertEqual('create table person (id int, name text, age int);',
                         secs['create_tables'])
        self.assertEqual({'init_sections': 'create_tables,create_idx'},
                         parser.meta)

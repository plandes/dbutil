from dataclasses import dataclass, field
from zensols.db import BeanDbPersister


@dataclass
class Person(object):
    name: str = field()
    age: int = field()
    id: int = field(default=None)


@dataclass
class Application(object):
    """A people database"""

    persister: BeanDbPersister

    def demo(self):
        # create a row using an instance of a dataclass and return the unique
        # ID of the inserted row
        paul_id: int = self.persister.insert(Person('Paul', 31))

        # we can also insert by columns in the order given in the dataclass
        jane_id: int = self.persister.insert_row('Jane', 32)

        # print everyone in the database
        print(self.persister.get())

        # delete a row
        self.persister.delete(paul_id)
        print(self.persister.get())

        # update jane's age
        self.persister.update_row(jane_id, 'jane', 36)

        # get the updated row we just set
        jane = self.persister.get_by_id(jane_id)
        print(f'jane: {jane}')

        # clean up, which for SQLite deletes the file
        self.persister.conn_manager.drop()

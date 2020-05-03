from zensols.db import Bean


class Person(Bean):
    def __init__(self, name, age, id=None):
        self.id = id
        self.name = name
        self.age = age

    def get_attr_names(self):
        return 'id name age'.split()

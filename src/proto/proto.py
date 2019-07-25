import logging
from zensols.actioncli import ClassImporter
from zensols.db import AppConfig

logger = logging.getLogger(__name__)


def instance(name, info=(), debug=()):
    conf = AppConfig('resources/dbutil.conf')
    for l in debug:
        logging.getLogger(f'zensols.db.{l}').setLevel(logging.DEBUG)
    return ClassImporter(name).instance(conf)


def tmp():
    app = instance('zensols.db.app.MainApplication', debug='app'.split())
    app.tmp()


def main():
    logging.basicConfig(level=logging.WARNING)
    run = 1
    {1: tmp,
     }[run]()


main()

from pathlib import Path
from zensols.pybuild import SetupUtil

su = SetupUtil(
    setup_path=Path(__file__).parent.absolute(),
    name="zensols.db",
    package_names=['zensols', 'resources'],
    package_data={'': ['*.conf', '*.sql']},
    description='A library of database convenience utilities, typically for creation of temporary files for processing large data.',
    user='plandes',
    project='dbutil',
    keywords=['tooling'],
    has_entry_points=False,
).setup()

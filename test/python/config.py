from zensols.actioncli import ExtendedInterpolationConfig


class AppConfig(ExtendedInterpolationConfig):
    def __init__(self, *args, **kwargs):
        super(AppConfig, self).__init__(*args, default_expect=True, **kwargs)

    @staticmethod
    def instance():
        return AppConfig('test-resources/db.conf')

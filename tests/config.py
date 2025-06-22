from zensols.config import ExtendedInterpolationConfig


class AppConfig(ExtendedInterpolationConfig):
    @staticmethod
    def instance():
        return AppConfig('test-resources/db.conf')

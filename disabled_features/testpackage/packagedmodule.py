from testpackage import othermodule # noqa
from core import featurebase


class TestClass(featurebase.FeatureBase):
    pass


def get_feature_class():
    return TestClass()

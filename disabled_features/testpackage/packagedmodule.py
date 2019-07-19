from testpackage import othermodule
from core import featurebase

class TestClass(featurebase.FeatureBase):
    pass

def get_feature_class():
    return TestClass()

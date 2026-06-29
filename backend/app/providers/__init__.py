from .demo import DemoProvider
from .gutendex import GutendexProvider

providers = {
    "classics-a": DemoProvider("classics-a", "内置中文公版书库"),
    "gutendex": GutendexProvider(),
}

__all__ = ["providers"]

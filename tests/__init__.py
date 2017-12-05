import os.path

from discover import DiscoveringTestLoader


def get_tests():
    start_dir = os.path.dirname(__file__)
    test_loader = DiscoveringTestLoader()
    return test_loader.discover(start_dir, pattern="*.py")

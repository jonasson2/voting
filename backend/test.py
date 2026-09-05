import unittest

if __name__ == '__main__':
    tests = unittest.TestLoader().discover(
        'tests', pattern='test_*.py', top_level_dir='.'
    )
    result = unittest.TextTestRunner(buffer=True).run(tests)
    raise SystemExit(not result.wasSuccessful())

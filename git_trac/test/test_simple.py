"""
Easy doctests
"""

import unittest


class SimpleTests(unittest.TestCase):

    def testTrue(self):
        """
        Make sure there is at least one passing doctest
        """
        self.assertTrue(True)




if __name__ == '__main__':
    unittest.main()


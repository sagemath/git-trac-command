"""
Test the command line argument parser
"""

import unittest
from git_trac.cmdline import make_parser


class ParserTests(unittest.TestCase):

    def testHelp(self):
        parser = make_parser()
        args = parser.parse_args(['help'])
        self.assertEqual(args.subcommand, 'help')

    def testDashHelp(self):
        parser = make_parser()
        args = parser.parse_args(['-h'])
        self.assertEqual(args.subcommand, 'help')





if __name__ == '__main__':
    unittest.main()


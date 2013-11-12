#!/usr/bin/env python3

# Easiest way to use this is to create a symlink
# /dir/in/search/path/git-trac -> run.py


import os
import sys

try:
    from git_trac import cmdline
except ImportError:
    sys.path.append('')
    from git_trac import cmdline

if __name__ == '__main__':
    cmdline.launch()


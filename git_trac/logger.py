"""
Customized Python logger
"""
##############################################################################
#  Copyright (C) 2014  Volker Braun <vbraun.name@gmail.com>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
##############################################################################


import logging


def make_logger(name, doctest_mode=False):
    logger = logging.getLogger(name)
    if len(logger.handlers) == 0:
        if doctest_mode:
            formatter = logging.Formatter('[%(name)s] %(levelname)s: %(message)s')
        else:
            formatter = logging.Formatter('%(asctime)s [%(name)s] %(levelname)s: %(message)s',
                                          datefmt='%H:%M:%S')
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(logging.WARNING)
    
    return logger


def enable_doctest_mode():
    global logger
    logger = make_logger('git-trac', True)    


logger = make_logger('git-trac')    





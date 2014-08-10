"""
Create a new beta/rc/stable release.
"""

import os
import tempfile
import shutil
from subprocess import Popen, check_call


def update_version(version):
    check_call(['sage', '-sh', '-c', 'sage-update-version {0}'.format(version)])

def create_tarball():
    check_call(['sage', '-sdist'])

def sage_build(clean=None, internet=True, cwd=None, test_long=False):
    env = dict(os.environ)
    env['SAGE_PARALLEL_SPKG_BUILD'] = 'yes'
    env['SAGE_ATLAS_ARCH'] = 'Corei2,SSE3,SSE2,SSE1'
    env['SAGE_ATLAS_LIB'] = '/usr/lib64/atlas'
    env['MAKE'] = 'make -j10'
    if not internet:
        poison =  'http://192.0.2.0:5187/'
        env['http_proxy'] = poison
        env['https_proxy'] = poison
        env['ftp_proxy'] = poison
        env['rsync_proxy'] = poison
    def run(*args):
        proc = Popen(args, env=env, cwd=cwd)
        rc = proc.wait()
        if rc != 0: 
            raise RuntimeError('command returned non-zero exit code: ' + ' '.join(args))
    if clean is None:
        run('make', 'doc-clean')
    elif clean:
        run('make', 'distclean')
    run('make')
    run('make', 'doc-pdf')
    run('make', 'ptestlong' if test_long else 'ptest')

def check_tarball(tarball):
    print('-' * 78)
    print('Checking tarball: ' + tarball)
    tarball = os.path.abspath(tarball)
    if not os.path.exists(tarball):
        raise ValueError('tarball file does not exist')
    cwd = os.getcwd()
    tmp = tempfile.mkdtemp(dir='/var/tmp')
    try:
        os.chdir(tmp)
        check_call(['tar', 'xf', tarball])
        sage_root = os.path.join(tmp, os.listdir(tmp)[0])
        sage_build(clean=False, cwd=sage_root, internet=False, test_long=True)
    finally:
        os.chdir(cwd)
        shutil.rmtree(tmp)

def check_upgrade(git, from_version, to_version):
    print('-' * 78)
    print('Checking upgrade {0} -> {1}'.format(from_version, to_version))
    sage_root = git.rev_parse(show_toplevel=True).strip()
    git.checkout(from_version)
    sage_build(clean=True, cwd=sage_root)
    git.checkout(to_version)
    sage_build(cwd=sage_root, test_long=True)
    git.checkout('develop')

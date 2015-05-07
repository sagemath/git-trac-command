"""
Fab file for interaction with our GCE instance
"""
import os

try:
    import fabric
    from fabric.api import env, run, sudo, put, settings, cd
    from fabric.contrib.files import exists
except ImportError:
    # Fabric shoud be py3-compatible any time now, but not yet
    # Evil hack to make importable in py3 tests
    class AttrDict(dict):
        def __init__(self, *args, **kwargs):
            super(AttrDict, self).__init__(*args, **kwargs)
            self.__dict__ = self
    env = AttrDict()

env.use_ssh_config = True
env.user = 'sagemath'
env.hosts = ['google_compute_engine']


def package_name(url_or_path):
    tarball_name = os.path.basename(url_or_path)
    return tarball_name.split('-', 1)[0]


def upload_tarball(url_or_path):
    """
    Add tarball to http://sagemath.org/packages/upstream
    """
    package = package_name(url_or_path)
    destination = os.path.join('/home/sagemath/files/spkg/upstream', package)
    if os.path.exists(url_or_path):        # is local file
        put(url_or_path, os.path.join(destination, os.path.basename(url_or_path)))
    else:                                  # should be a url
        with cd(destination):
            run('wget --no-directories -p -N ' + url_or_path)
    run('/home/sagemath/publish-files.sh')


    
def upload_dist_tarball(tarball):
    """
    Add tarball to http://sagemath.org/packages/upstream
    """
    basename = os.path.basename(tarball)
    put(tarball, os.path.join('/home/sagemath/files/devel', basename))
    run('/home/sagemath/publish-files.sh')


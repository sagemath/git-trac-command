Git-Trac Integration
====================

About
-----

This module implements a "git trac" subcommand of the git suite that
interfaces with trac over XMLRPC.

Included is a one-page git cheat sheet for Sage/Git/Trac: 
http://github.com/sagemath/git-trac-command/raw/master/doc/git-cheat-sheet.pdf

Installation
------------

The easiest way to just try out the code in this repo is to source the
``enable.sh`` script, which will prepend it to your PATH. This enables
the git trac subcommand until you close that shell, so no permanent
change is made:

    $ git clone https://github.com/sagemath/git-trac-command.git
    $ source git-trac-command/enable.sh
    Prepending the git-trac command to your search PATH

To permanently install the code from this repo, clone it and run
``setup.py``:

    $ git clone https://github.com/sagemath/git-trac-command.git
    $ cd git-trac-command
    $ python setup.py install

Alternatively you can just symlink ``git-trac`` to anywhere in your path:

    $ git clone https://github.com/sagemath/git-trac-command.git
    $ cd git-trac-command
    $ ln -s `pwd`/git-trac ~/bin/

On a Mac, which may not have a default in the home directory for commands,
it may be easier to add this to your ``.profile``: 

    $ git clone https://github.com/sagemath/git-trac-command.git
    $ cd git-trac-command
    $ pico/vim/emacs $HOME/.profile
    <add a line like "export PATH=$PATH:$HOME/Downloads/git-trac-command/bin">

Usage
-----

* Print the trac ticket information using ``git trac print
  <ticket_number>``. 

      $ git trac print 12345
      ==============================================================================
      Trac #12345: Title of ticket 12345
      ...
      ==============================================================================

  Alternatively, you can pass a remote branch name, in which case trac
  is searched for a ticket whose (remote) "Branch:" field equals the
  branch name.  If that fails, the ticket number will be deduced from
  the branch name by scanning for a number. If you neither specify a
  ticket number or branch name, the local git branch name is used:

      $ git branch
      /u/user/description
      $ git trac print
      ==============================================================================
      Trac #nnnnn: Title
      <BLANKLINE>
      Description
      Status: Status                          Component: Component                
      ...
      Branch: u/user/description
      ==============================================================================


* Checkout 
  a remote branch:

      $ git trac checkout 12345

  Will automatically pick a local branch name ``t/12345/description``
  based on the remote branch name. If you want a particular local
  branch name, you can specify it manually:

      $ git trac checkout -b my_branch 12345


* Create a new ticket on trac, and a new local branch 
  corresponding to it:

      $ git trac create "This is the summary"

  This will automatically create a local branch name
  ``t/12345/this_is_the_summary``. You can specify it manually if you
  prefer with:
  
      $ git trac create -b my_branch "This is the summary"


* Pull (= fetch + merge) from the branch
  on a ticket:

      $ git trac pull 12345

  You can omit the ticket number, in which case the script will try to
  search for the ticket having the local branch name attached. If that
  fails, an attempt is made to deduce the ticket number from the local
  branch name.


* Push (upload) to the branch
  on a ticket, and set the trac "Branch:" field accordingly:

      $ git trac push 12345

  You can omit the ticket number, in which case the script will try to
  search for the ticket having the local branch name attached. If that
  fails, an attempt is made to deduce the ticket number from the local
  branch name.


* Log of the commits for a
  ticket:

      $ git trac log 12345
    

* Find the trac ticket for a 
  commit, either identified by its SHA1 or branch/tag name.

      $ git log --oneline -1 ee5e39e
      ee5e39e Allow default arguments in closures
      $ git trac find ee5e39e
      Commit has been merged by the release manager into your current branch.
      commit 44efa774c5f991ea5f160646515cfe8d3f738479
      Merge: 5fd5442 679310b
      Author: Release Manager <release@sagemath.org>
      Date:   Sat Dec 21 01:16:56 2013 +0000

          Trac #15447: implement evaluation of PARI closures

* Review tickets with minimal recompiling. This assumes that you are
  currently on the "develop" branch, that is, the latest beta. Just
  checking out an older ticket would most likely reset the Sage tree
  to an older version, so you would have to compile older versions of
  packages to make it work. Instead, you can create an anonymous
  ("detached HEAD") merge of the ticket and the develop branch::

      $ git trac try 12345

  This will only touch files that are really modified by the
  ticket. In particular, if only Python files are changed by the
  ticket (which is true for most tickets) then you just have to run
  `sage -b` to rebuild the Sage library. When you are finished
  reviewing, just checkout a named branch. For example::

      $ git checkout develop
     
  If you want to edit the ticket branch (that is, add additional
  commits) you cannot use `git trac try`. You must use `git trac
  checkout` to get the actual ticket branch as a starting point.


Too Long, Didn't Read
---------------------

To fix a bug, start with

    $ git trac create "Fix foo"
    
This will open the ticket and create a new local branch
``t/<number>/fix_foo``. Then edit Sage, followed by 

    $ git add <filename>
    $ git commit

Repeat edit/commit as necessary. When you are finished, run

    $ git trac push

It will take the ticket number out of the branch name, so you don't
have to specify it.

    
Configuration
-------------

The scripts assume that the trac remote repository is set up as the
remote ``trac`` in the local repo. That is, you should have the
following for the Sage git server:

    $ git remote add trac https://trac.sagemath.org/sage.git      # read-only
    $ git remote add trac ssh://git@trac.sagemath.org/sage.git   # read-write
    $ git remote -v
    trac	ssh://git@trac.sagemath.org/sage.git (fetch)
    trac	ssh://git@trac.sagemath.org/sage.git (push)

Trac username and password are stored in the local repo (the
DOT_GIT/config file):
  
    $ git trac config --user=Myself --pass=s3kr1t
    Trac xmlrpc URL:
        https://trac.sagemath.org/xmlrpc (anonymous)
        https://trac.sagemath.org/login/xmlrpc (authenticated)
    Username: Myself
    Password: s3kr1t

If you do not want to store your trac username/password on disk you
can temporarily override it with the environment variables
``TRAC_USERNAME`` and ``TRAC_PASSWORD``. These take precedence over
any other configuration.


Sage-Trac Specifics
-------------------

Some of the functionality depends on the special trac plugins (see
https://github.com/sagemath/sage_trac), namely:

* Searching for a trac ticket by branch name requires the
  ``trac_plugin_search_branch.py`` installed in trac and a custom trac
  field named "Branch:":

      $ git trac search --branch=u/vbraun/toric_bundle
      15328

* SSH public key management requires the ``sshkeys.py`` trac 
  plugin:

      $ git trac ssh-keys
      $ git trac ssh-keys --add=~/.ssh/id_rsa.pub
      This is not implemented yet


Release Management
------------------

The Sage release management scripts are in the `git-trac.releasemgr`
subdirectory. They are probably only useful to the Sage release
manager.


Testing and Python Compatibility
--------------------------------

* The git-trac command supports Python 2.6, 2.7, 3.3, and 3.4.
* Most recent [Travis CI](https://travis-ci.org/sagemath/git-trac-command) test:
  [![Build Status](https://travis-ci.org/sagemath/git-trac-command.svg?branch=master)](https://travis-ci.org/sagemath/git-trac-command)

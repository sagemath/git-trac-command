Git-Trac Integration
====================

About
-----

This module implements a "git trac" subcommand of the git suite that
interfaces with trac over XMLRPC.
 

Installation
------------

The easiest way to use the code from this repo is to clone it and
create a symlink named ``git-trac`` somewhere in your path and
pointing to ``run.py``:

    $ git clone https://github.com/sagemath/git-trac-command.git
    $ cd git-trac-command
    $ ln -s `pwd`/run.py ~/bin/git-trac


Usage
-----

* Print the trac ticket information using ``git trac get
  <ticket_number>``. 

      $ git trac get 12345
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
      $ git trac get
      ==============================================================================
      Trac #nnnnn: Title
      <BLANKLINE>
      Description
      Status: Status                          Component: Component                
      ...
      Branch: u/user/description
      ==============================================================================
  

* Trac username and password are stored in the local repo (the
  DOT_GIT/config file):
  
      $ git trac config --user=Myself --pass=s3kr1t
      Trac xmlrpc URL:
          http://trac.sagemath.org/xmlrpc (anonymous)
          http://trac.sagemath.org/login/xmlrpc (authenticated)
      Username: Myself
      Password: s3kr1t




Sage-Trac Specifics
-------------------

Some of the functionality depends on the special trac plugins (see
https://github.com/sagemath/sage_trac), namely:

* Searching for a trac ticket by branch name requires the
  ``trac_plugin_search_branch.py`` installed in trac and a custom trac
  field named "Branch:":

      $ git trac search --branch=u/vbraun/toric_bundle
      15328

* SSH public key management requries the ``sshkeys.py`` trac 
  plugin:

      $ git trac ssh-keys
      $ git trac ssh-keys --add=~/.ssh/id_rsa.pub
      This is not implemented yet
      
      
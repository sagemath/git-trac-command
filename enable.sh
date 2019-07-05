#!/usr/bin/env bash
#
# As yet another way to use the git-trac command, this script adds it
# to the path manually. The only way to use it is to source it into
# your current shell:
#
#     [user@localhost]$ source enable.sh
#

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]
then
    echo "You are trying to call this script directly, which is not"
    echo "possible. You must source this script instead:" 
    echo ""
    echo "    [user@localhost]$ source git-trac-command/enable.sh"
    echo ""
    exit 1
fi

function set_path_git_trac {
    GIT_TRAC_CMD="$GIT_TRAC_DIR/git-trac"

    if [[ "$(command -v git-trac)" == "$GIT_TRAC_CMD" ]]
    then
        echo "The git-trac command is already in your search PATH"
    else
        echo "Prepending the git-trac command to your search PATH"
        export PATH="$GIT_TRAC_DIR":$PATH
    fi
}

if [[ -n $BASH_VERSION ]]; then
    # Assume bash
    if [[ ${BASH_VERSINFO[0]} -le 2 ]]
    then
        echo 'Your bash version is too old.'
    fi
    GIT_TRAC_DIR=`cd $(dirname -- $BASH_SOURCE)/bin && pwd -P`
    set_path_git_trac
elif [[ -n $ZSH_VERSION ]]; then
    # Assume zsh
    GIT_TRAC_DIR=`cd $(dirname -- ${(%):-%x})/bin && pwd -P`
    set_path_git_trac
else
    echo "This script only works if you use bash or zsh, aborting."
fi 

unset set_path_git_trac

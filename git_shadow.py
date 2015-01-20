#!/usr/bin/env python
# 
# Jonathan Foote
# jmfoote@loyola.edu

import subprocess, re, sys, os, json, difflib

def add_shadow_repo(cwd="."):
    '''
    Hack that adds shadow repo to enclosing git repo. Run as a pre-commit hook,
    for example.
    '''
    shadow_git_repo_path = os.path.join(".shadow", ".git")
    if not os.path.exists(shadow_git_repo_path):
        sys.stderr.write("git-shadow hook is installed, but shadow repository "
            " doesn't exist at '%s'. Try 'git shadow deactivate [repo]'." %\
            shadow_git_repo_path)
        sys.exit(-1)

    # rename shadow's git repository 
    shadow_repo_storage_path = os.path.join(".shadow", "git")
    shutil.move(shadow_git_repo_path, shadow_repo_storage_path)
    
    # git add shadow directory
    subprocess.check_call(["git", "add", os.path.join(".shadow", "*")], cwd=cwd)

def get_shadow_repo_path(cwd):
    return os.path.join(get_repo_path(cwd), ".shadow")

def delete_shadow_repo(cwd):
    subprocess.check_call(["rm", "-rf", get_shadow_repo_path(cwd)], cwd=cwd)

def create_shadow_repo(cwd=".", force=True):
    '''
    Creates a new shadow repo in the conventional subdir below cwd. If shadow 
    repo dir exists and force is False, the script errors out. Otherwise the
    old repo is deleted before the new one is created.
    Called when shadow is initialized and by hooks (such as post-commit).
    '''
    shadow_repo_path = get_shadow_repo_path(cwd)
    if os.path.exists(shadow_repo_path):
        if force == False:
            sys.stderr.write(".shadow already exists in %s" % shadow_repo_path) 
            sys.exit(-1)
        else:
            delete_shadow_repo(cwd)
 
    # make shadow repo
    subprocess.check_output(["git", "init", shadow_repo_path], cwd=cwd)

def get_repo_path(path):
    if not os.path.isdir(path):
        path = os.path.dirname(path)
    return subprocess.check_output(["git", "rev-parse", "--show-toplevel"], cwd=path).strip()

def add_hooks(cwd):
    '''
    Create (or add to) git hook files that call git-shadow. 
    '''
    hook_dir = os.path.join(get_repo_path(cwd), ".git", "hooks")
    for hook in ["pre-commit", "post-commit", "pre-checkout"]:
        filepath = os.path.join(hook_dir, hook)
        if not os.path.exists(filepath):
            with open(filepath, "wt") as fp:
                fp.write("#!/bin/sh\ngit shadow %s\n" % hook)
        else:
            with open(filepath, "at") as fp:
                fp.write("\ngit shadow %s\n" % hook)

def remove_hooks(cwd):
    '''
    Remove git-shadow hooks from git repo
    '''
    hook_dir = os.path.join(get_repo_path(cwd), ".git", "hooks")
    for hook in ["pre-commit", "post-commit", "pre-checkout"]:
        filepath = os.path.join(hook_dir, hook)
        lines = [l.strip() for l in open(filepath, "rt").readlines()]
        lines = [l for l in lines if "git shadow" not in l]
        # if this hook file was created by git-shadow, delete it
        if len(lines) == 1 and "#!/bin/sh" in lines[0]:
            os.remove(filepath)
        else:
            open(filepath, "wt").write("\n".join(lines))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.stderr.write("not enough args")
        sys.exit(-1)

    if len(sys.argv) > 2:
        cwd = sys.argv[2]
    else:
        cwd = "."

    if sys.argv[1] == "activate":
        create_shadow_repo(cwd=cwd, force=True)
        add_hooks(cwd=cwd)
    elif sys.argv[1] == "deactivate":
        remove_hooks(cwd=cwd)
        delete_shadow_repo(cwd)
    elif sys.argv[1] in ["pre-commit"]:
        add_shadow_repo(cwd=cwd)
    elif sys.argv[1] in ["post-commit", "pre-checkout"]:
        create_shadow_repo(cwd=cwd, force=False)
    elif sys.argv[1] == "add-hooks":
        add_hooks(cwd)
    elif sys.argv[1] == "remove-hooks": 
        remove_hooks(cwd)
    else:
        # run git command in mirror directory of shadow repo
        pass

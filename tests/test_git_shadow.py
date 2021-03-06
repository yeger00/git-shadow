#!/usr/bin/env python

from unittest import TestCase
import subprocess, os, shutil, tempfile

# Load git-shadow as a module for functional unit tests. Le Hack. Sacrebleu!!1
import imp
git_shadow = imp.load_source("git_shadow", os.path.join(os.getcwd(), "git-shadow")) 

def rm_r(path):
    if os.path.isdir(path):
        shutil.rmtree(path)
    elif os.path.exists(path):
        os.remove(path)

def num_commits(repo_dir):
    print "num_commits", subprocess.check_output(["git", "log"], cwd=repo_dir)
    out = subprocess.check_output(["git", "log", "--format=%H"], cwd=repo_dir)
    return len(out.strip().splitlines())

class UnitTests(TestCase):

    def setUp(self):
        # create dummy repo for testing
        self.repo_dir = os.path.realpath(tempfile.mkdtemp())
        subprocess.check_call(["git", "init", self.repo_dir])

        # add cwd to path to support execution of "git-shadow" in tests
        os.environ["PATH"] = ":".join(os.environ["PATH"].split(":") + [os.getcwd()])
        self.env = os.environ

    def tearDown(self):
        rm_r(self.repo_dir)

    def test_get_shadow_path(self):
        '''
        Verify the shadow repo path is constructed properly and that an 
        Exception is raised if the func is called outside a git repo.
        '''
        p = git_shadow.get_shadow_path(self.repo_dir)
        self.assertEqual(p, os.path.join(self.repo_dir, ".shadow"))

        tdir = tempfile.mkdtemp()
        try:
            with self.assertRaises(subprocess.CalledProcessError):
                git_shadow.get_shadow_path(tdir)
        finally:
            rm_r(tdir)

    def test_get_current_path(self):
        '''
        Verify the urrent repo path is constructed properly and that an 
        Exception is raised if the func is called outside a git repo.
        '''
        p = git_shadow.get_current_path(self.repo_dir)
        self.assertEqual(p, os.path.join(self.repo_dir, ".shadow", "current"))

        tdir = tempfile.mkdtemp()
        try:
            with self.assertRaises(subprocess.CalledProcessError):
                git_shadow.get_current_path(tdir)
        finally:
            rm_r(tdir)

    def test_create_current(self):
        '''
        Verify the function creates/overwrites repos properly 
        '''
        git_shadow.create_current(cwd=self.repo_dir)
        self.assertTrue(os.path.exists(os.path.join(self.repo_dir, 
            ".shadow", "current", ".git")))
        with self.assertRaises(OSError):
            git_shadow.create_current(cwd=self.repo_dir)

    def test_create_current_shadow(self):
        '''
        Verify the function shadows controlled files
        '''
        fp_a = os.path.join(self.repo_dir, "a")
        open(fp_a, "wt").write("test_a")

        dir_b = os.path.join(self.repo_dir, "db")
        os.mkdir(dir_b)
        fp_b = os.path.join(dir_b, "b")
        open(fp_b, "wt").write("test_b")

        subprocess.call(["git", "add", fp_a, fp_b], cwd=self.repo_dir)
        subprocess.call(["git", "commit", "-m", "'message'"], cwd=self.repo_dir)
 
        git_shadow.create_current(cwd=self.repo_dir)
        self.assertTrue(os.path.exists(os.path.join(self.repo_dir, 
            ".shadow", "current", fp_a)))
        self.assertTrue(os.path.exists(os.path.join(self.repo_dir, 
            ".shadow", "current", fp_b)))


    def test_add_hooks(self):
        # verify hooks are installed in parent repository
        git_shadow.add_hooks(self.repo_dir)
        subprocess.call(["git", "shadow", "add-hooks", self.repo_dir], env=self.env)
        self.assertTrue(os.path.exists(os.path.join(self.repo_dir, ".git", "hooks", "post-commit")))
        self.assertTrue(os.path.exists(os.path.join(self.repo_dir, ".git", "hooks", "post-checkout")))

    def test_add_hooks_merge(self):
        hook_path = os.path.join(self.repo_dir, ".git", "hooks", "post-commit")
        open(hook_path, "wt").write("echo test")
        git_shadow.add_hooks(self.repo_dir)
        self.assertEqual(open(hook_path, "rt").read(), 
            "echo test\ngit shadow post-commit\n")

    def test_remove_hooks(self):
        # verify hooks are removed from parent repository
        git_shadow.add_hooks(self.repo_dir)
        git_shadow.remove_hooks(self.repo_dir)
        self.assertFalse(os.path.exists(os.path.join(self.repo_dir, ".git", "hooks", "post-commit")))
        self.assertFalse(os.path.exists(os.path.join(self.repo_dir, ".git", "hooks", "post-checkout")))

    def test_remove_hooks_merge(self):
        # verify git-shadow hooks are removed without clobbering existing hook file
        filetext = "foobaz"
        filepath = os.path.join(self.repo_dir, ".git", "hooks", "post-commit")
        open(filepath, "wt").write(filetext)

        git_shadow.add_hooks(self.repo_dir)
        git_shadow.remove_hooks(self.repo_dir)

        self.assertTrue(os.path.exists(os.path.join(self.repo_dir, ".git", "hooks", "post-commit")))
        self.assertEqual(filetext, open(filepath, "rt").read())
        self.assertFalse(os.path.exists(os.path.join(self.repo_dir, ".git", "hooks", "post-checkout")))

    def test_activate(self):
        git_shadow.activate(self.repo_dir)
        path = os.path.join(self.repo_dir, ".shadow", "current")
        self.assertTrue(os.path.exists(path))
        self.assertTrue(git_shadow.is_active(self.repo_dir))

        git_shadow.deactivate(self.repo_dir)
        path = os.path.join(self.repo_dir, ".shadow", "current")
        self.assertFalse(os.path.exists(path))
        self.assertFalse(git_shadow.is_active(self.repo_dir))

    def test_shadow_controlled_files_moves(self):
        '''
        Verify the function shadows controlled files when git mv, rm are used
        '''
        '''
        TODO
        fp_a = os.path.join(self.repo_dir, "a")
        open(fp_a, "wt").write("test_a")

        dir_b = os.path.join(self.repo_dir, "db")
        os.mkdir(dir_b)
        fp_b = os.path.join(dir_b, "b")
        open(fp_b, "wt").write("test_b")

        subprocess.call(["git", "add", fp_a, fp_b], cwd=self.repo_dir)
        subprocess.call(["git", "commit", "-m", "'message'"], cwd=self.repo_dir)
 
        git_shadow.create_current(cwd=self.repo_dir)
        self.assertTrue(os.path.exists(os.path.join(self.repo_dir, 
            ".shadow", "current", fp_a)))
        self.assertTrue(os.path.exists(os.path.join(self.repo_dir, 
            ".shadow", "current", fp_b)))
        '''
        pass

    def test_shadow_file(self):
        # add some files to a test repo
        test_filepath = os.path.join(self.repo_dir, "foobar")
        open(test_filepath, "wt").write("some file contents")
        subprocess.check_call(["git", "add", test_filepath], cwd=self.repo_dir, env=self.env)

        os.mkdir(os.path.join(self.repo_dir, "foobaz"))
        test_filepath = os.path.join(self.repo_dir, "foobaz", "foomanchu")
        open(test_filepath, "wt").write("some other file contents")

        subprocess.check_call(["git", "add", test_filepath], cwd=self.repo_dir, env=self.env)
        subprocess.check_call(["git", "commit", "-m", "'message'"], cwd=self.repo_dir, env=self.env)

        git_shadow.activate(self.repo_dir)

        # verify adding an unchanged file results in creation of .shadow/current, 
        # but doesn't make an additional commit
        shadow_repo_path = git_shadow.get_current_path(self.repo_dir)
        print "self.repo_dir", self.repo_dir
        git_shadow.shadow_file(test_filepath, test_filepath)
        self.assertEqual(1, num_commits(shadow_repo_path))

        # verify adding a changed file *does* result in a commit to the shadow repo
        with tempfile.NamedTemporaryFile() as tf:
            tf.write("new contents..\nare here!")
            tf.flush()
            git_shadow.shadow_file(test_filepath, tf.name)
            self.assertEqual(2, num_commits(shadow_repo_path))

"""

class IntegrationTests(TestCase):

    def setUp(self):
        # create dummy repo for testing
        self.repo_dir = os.path.realpath(tempfile.mkdtemp())
        subprocess.check_call(["git", "init", self.repo_dir])

        # add cwd to path to support execution of "git-shadow" in tests
        self.env = os.environ
        self.env["PATH"] = ":".join(self.env["PATH"].split(":") + [os.getcwd()])

    def tearDown(self):
        rm_r(self.repo_dir)

    def test_shadow_file(self):
        # add some files to a test repo
        test_filepath = os.path.join(self.repo_dir, "foobar")
        open(test_filepath, "wt").write("some file contents")
        subprocess.check_call(["git", "add", test_filepath], cwd=self.repo_dir, env=self.env)

        os.mkdir(os.path.join(self.repo_dir, "foobaz"))
        test_filepath = os.path.join(self.repo_dir, "foobaz", "foomanchu")
        open(test_filepath, "wt").write("some other file contents")

        subprocess.check_call(["git", "add", test_filepath], cwd=self.repo_dir, env=self.env)
        subprocess.check_call(["git", "commit", "-m", "'message'"], cwd=self.repo_dir, env=self.env)

        # create shadow repo
        git_shadow.create_shadow_repo(self.repo_dir)
        git_shadow.shadow_controlled_files(self.repo_dir)
        git_shadow.add_hooks(self.repo_dir)

        # simulate two modifications to a file 
        with tempfile.NamedTemporaryFile() as tf:
            tf.write("new contents..\nare here!")
            tf.flush()
            git_shadow.shadow_file(test_filepath, tf.name)

            tf.write("new contents..\nare here now!")
            tf.flush()
            git_shadow.shadow_file(test_filepath, tf.name)

            # simulate a save 
            shutil.copyfile(tf.name, test_filepath)

        # simulate an add/commit to the enclosing repo
        subprocess.check_call(["git", "add", test_filepath], cwd=self.repo_dir, env=self.env)
        subprocess.check_call(["git", "commit", "-m", "'message'"], cwd=self.repo_dir, env=self.env)

        # make sure: new shadow repo was initialized in HEAD, and it is empty: 
        #  - only a single commit -- all tracked files being added
        self.assertTrue(os.path.exists(os.path.join(self.repo_dir, ".shadow", ".git")))
        self.assertEqual(num_commits(os.path.join(self.repo_dir, ".shadow")), 1)

        # make sure: old shadow repo was committed with last commit 
        subprocess.check_call(["git", "checkout", "HEAD^"], cwd=self.repo_dir, env=self.env)
        self.assertTrue(os.path.exists(os.path.join(self.repo_dir, ".shadow", "git")))
        self.assertEqual(num_commits(os.path.join(self.repo_dir, ".shadow")), 2)
"""

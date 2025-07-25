import os
import tempfile
from pathlib import Path
import pytest
from db2repo.git.manager import GitManager
from git import InvalidGitRepositoryError, GitCommandError, Repo


def test_initialize_and_is_git_repository():
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / "repo"
        assert not GitManager.is_git_repository(repo_path)
        assert GitManager.initialize_repository(repo_path)
        assert GitManager.is_git_repository(repo_path)
        # Should be a valid git repo
        gm = GitManager(str(repo_path))
        assert gm.repo is not None


def test_get_status_and_add_commit():
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)
        GitManager.initialize_repository(repo_path)
        gm = GitManager(str(repo_path))
        # Create a file
        file_path = repo_path / "test.txt"
        file_path.write_text("hello")
        # Status should show untracked
        status = gm.get_status()
        assert "test.txt" in status["untracked"]
        # Add file
        assert gm.add_files([str(file_path)])
        status = gm.get_status()
        assert "test.txt" in status["changed"] or not status["untracked"]
        # Commit
        assert gm.commit_changes(
            "Initial commit", author_name="Test", author_email="test@example.com"
        )
        status = gm.get_status()
        assert not status["changed"]
        assert not status["untracked"]


def test_invalid_repo_raises():
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / "not_a_repo"
        gm = GitManager(str(repo_path))
        with pytest.raises(InvalidGitRepositoryError):
            gm.get_status()
        with pytest.raises(InvalidGitRepositoryError):
            gm.add_files(["foo.txt"])
        with pytest.raises(InvalidGitRepositoryError):
            gm.commit_changes("msg")


def test_add_files_error():
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)
        GitManager.initialize_repository(repo_path)
        gm = GitManager(str(repo_path))
        # Try to add a non-existent file
        with pytest.raises(GitCommandError):
            gm.add_files([str(repo_path / "does_not_exist.txt")])

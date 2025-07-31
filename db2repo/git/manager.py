"""
Git management module for DB2Repo.

This module handles git operations and repository management.
"""

from pathlib import Path
from typing import Optional, List
import subprocess
from git import Repo, InvalidGitRepositoryError, NoSuchPathError, GitCommandError


class GitManager:
    """Manages git operations for DDL repositories."""

    def __init__(self, repo_path: str) -> None:
        self.repo_path = Path(repo_path).expanduser().resolve()
        try:
            self.repo = Repo(str(self.repo_path))
        except (InvalidGitRepositoryError, NoSuchPathError):
            self.repo = None

    @staticmethod
    def is_git_repository(path: str) -> bool:
        repo_path = Path(path).expanduser().resolve()
        try:
            _ = Repo(str(repo_path))
            return True
        except (InvalidGitRepositoryError, NoSuchPathError):
            return False

    @staticmethod
    def initialize_repository(path: str) -> bool:
        repo_path = Path(path).expanduser().resolve()
        repo_path.mkdir(parents=True, exist_ok=True)
        try:
            Repo.init(str(repo_path))
            return True
        except Exception:
            return False

    def get_status(self) -> dict:
        if not self.repo:
            raise InvalidGitRepositoryError(f"Not a git repository: {self.repo_path}")
        try:
            changed = [item.a_path for item in self.repo.index.diff(None)]
            untracked = self.repo.untracked_files
            branch = self.repo.active_branch.name if self.repo.head.is_valid() else None
            return {
                "changed": changed,
                "untracked": untracked,
                "branch": branch,
                "is_dirty": self.repo.is_dirty(),
            }
        except Exception as e:
            raise GitCommandError(f"Failed to get git status: {e}", 1)

    def add_files(self, file_paths: List[str]) -> bool:
        if not self.repo:
            raise InvalidGitRepositoryError(f"Not a git repository: {self.repo_path}")
        try:
            rel_paths = [
                str(Path(f).resolve().relative_to(self.repo_path)) for f in file_paths
            ]
            self.repo.index.add(rel_paths)
            return True
        except Exception as e:
            raise GitCommandError(f"Failed to add files: {e}", 1)

    def commit_changes(
        self,
        message: str,
        author_name: Optional[str] = None,
        author_email: Optional[str] = None,
    ) -> bool:
        if not self.repo:
            raise InvalidGitRepositoryError(f"Not a git repository: {self.repo_path}")
        try:
            author = None
            if author_name and author_email:
                from git import Actor

                author = Actor(author_name, author_email)
            self.repo.index.commit(message, author=author)
            return True
        except Exception as e:
            raise GitCommandError(f"Failed to commit changes: {e}", 1)

    def push_changes(self, remote: str = "origin", branch: str = "main") -> bool:
        """
        Push changes to remote repository.

        Args:
            remote: Remote repository name
            branch: Branch name to push

        Returns:
            True if successful, False otherwise
        """
        # TODO: Implement git push operation
        # This will be implemented in Story 4.3
        raise NotImplementedError("Git push operation not yet implemented")

    def pull_changes(self, remote: str = "origin", branch: str = "main") -> bool:
        """
        Pull changes from remote repository.

        Args:
            remote: Remote repository name
            branch: Branch name to pull

        Returns:
            True if successful, False otherwise
        """
        # TODO: Implement git pull operation
        # This will be implemented in Story 4.3
        raise NotImplementedError("Git pull operation not yet implemented")

    def get_branches(self) -> List[str]:
        """
        Get list of all branches in the repository.

        Returns:
            List of branch names
        """
        if not self.repo:
            raise InvalidGitRepositoryError(f"Not a git repository: {self.repo_path}")
        try:
            branches = [ref.name for ref in self.repo.references if ref.name.startswith('refs/heads/')]
            return [branch.replace('refs/heads/', '') for branch in branches]
        except Exception as e:
            raise GitCommandError(f"Failed to get branches: {e}", 1)

    def create_branch(self, branch_name: str) -> bool:
        """
        Create a new branch.

        Args:
            branch_name: Name of the branch to create

        Returns:
            True if successful, False otherwise
        """
        if not self.repo:
            raise InvalidGitRepositoryError(f"Not a git repository: {self.repo_path}")
        try:
            # Create new branch from current branch
            new_branch = self.repo.create_head(branch_name)
            return True
        except Exception as e:
            raise GitCommandError(f"Failed to create branch '{branch_name}': {e}", 1)

    def switch_branch(self, branch_name: str) -> bool:
        """
        Switch to a different branch.

        Args:
            branch_name: Name of the branch to switch to

        Returns:
            True if successful, False otherwise
        """
        if not self.repo:
            raise InvalidGitRepositoryError(f"Not a git repository: {self.repo_path}")
        try:
            # Get the branch reference
            branch_ref = self.repo.heads[branch_name]
            # Checkout the branch
            self.repo.heads[branch_name].checkout()
            return True
        except Exception as e:
            raise GitCommandError(f"Failed to switch to branch '{branch_name}': {e}", 1)

    def get_current_branch(self) -> Optional[str]:
        """Get the current branch name."""
        try:
            return self.repo.active_branch.name
        except Exception:
            return None
 
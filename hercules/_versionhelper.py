

import git
from pathlib import Path

_hexbug_dir = Path(__file__).parent.absolute() / 'hexbug'
_hexbug_version_file = _hexbug_dir / 'hexbugversion'

def get_hexbug_commit_version():
    if not _hexbug_version_file.exists():
        return ''
    with open(_hexbug_version_file, 'r') as f:
        return f.read()

def persist_hexbug_commit_version():
    hexbug_version = get_git_commit_version(_hexbug_dir)

    with open(_hexbug_version_file, 'w') as f:
        f.write(hexbug_version)

def get_python_dir_commit_version():
    from .constants import CONFIG
    python_dir = Path(CONFIG.python_script_path)
    return get_git_commit_version(python_dir)

def is_git_repo(path):
    try:
        _ = git.Repo(path).git_dir
        return True
    except git.exc.InvalidGitRepositoryError:
        return False
    
def is_dirty_or_untracked(repo):
    return repo.is_dirty() or len(repo.untracked_files)>0
    
def get_git_commit_version(path):

    if not is_git_repo(path):
        return ''

    repo = git.Repo(path)
    hash = repo.head.object.hexsha

    if is_dirty_or_untracked(repo):
        hash += '-dirty/untracked'

    return hash
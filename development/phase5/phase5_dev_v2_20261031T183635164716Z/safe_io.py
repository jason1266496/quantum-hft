"""Application path guard for synthetic fixtures and exclusive outputs."""
import os,pathlib,stat
class PathRejected(ValueError):pass

def guarded_path(root,relative,existing=True):
    root=pathlib.Path(root).resolve(strict=True)
    rel=pathlib.PurePath(relative)
    if rel.is_absolute() or not rel.parts or any(part in ('..','.') for part in rel.parts):raise PathRejected('PATH_ESCAPE')
    p=root.joinpath(*rel.parts)
    parent=root
    for part in rel.parts[:-1]:
        parent=parent/part
        try:mode=parent.lstat().st_mode
        except FileNotFoundError:raise PathRejected('MISSING_PARENT')
        if stat.S_ISLNK(mode) or not stat.S_ISDIR(mode):raise PathRejected('SYMLINK_OR_BAD_PARENT')
    if p.parent.resolve(strict=True)!=parent:raise PathRejected('PATH_ESCAPE')
    if existing:
        try:st=p.lstat()
        except FileNotFoundError:raise PathRejected('MISSING_INPUT')
        if not stat.S_ISREG(st.st_mode) or st.st_nlink!=1:raise PathRejected('SYMLINK_OR_HARDLINK')
        if p.resolve(strict=True).is_relative_to(root) is False:raise PathRejected('PATH_ESCAPE')
    return p

def read_fixture(root,relative):
    p=guarded_path(root,relative)
    fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
    try:
        st=os.fstat(fd)
        if not stat.S_ISREG(st.st_mode) or st.st_nlink!=1:raise PathRejected('SYMLINK_OR_HARDLINK')
        return os.read(fd,st.st_size+1)
    finally:os.close(fd)

def exclusive_write(root,relative,data):
    p=guarded_path(root,relative,False)
    fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600)
    try:os.write(fd,data)
    finally:os.close(fd)
    return p

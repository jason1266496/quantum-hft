"""Retain exact null exception; add owned-private-temp lifecycle only."""
import os,stat,sys
from pathlib import Path
from experiments.phase4b1_recovery import scope as original
ROOT=original.ROOT
ScopeViolation=original.ScopeViolation
def active():return original.ACTIVE
class PrivateTmpScope(original.WriteScope):
    def __init__(self,run,*,unit=True,report=None):
        super().__init__(run,unit=unit,report=report)
        self.tmp=self.run/"tmp";s=self.tmp.lstat()
        if self.tmp.is_symlink() or self.tmp.resolve()!=self.tmp or not stat.S_ISDIR(s.st_mode) or stat.S_IMODE(s.st_mode)!=0o700 or s.st_uid!=os.geteuid():raise ValueError("PRIVATE_TMP_IDENTITY")
        self.tmp_identity=(s.st_dev,s.st_ino,s.st_uid)
        self.created={};self.fds={};self._original_io={}
    def destination(self,raw):
        if ".." in Path(raw).parts:self.deny(raw,"PATH_TRAVERSAL_PROHIBITED")
        return super().destination(raw)
    def validate_tmp(self):
        s=self.tmp.lstat()
        if (s.st_dev,s.st_ino,s.st_uid)!=self.tmp_identity or stat.S_IMODE(s.st_mode)!=0o700 or self.tmp.is_symlink() or self.tmp.resolve()!=self.tmp:raise ScopeViolation("PRIVATE_TMP_CHANGED")
    def temp_candidate(self,raw):
        p=Path(raw);p=p if p.is_absolute() else Path.cwd()/p
        return p.is_relative_to(self.tmp) or p.resolve(strict=False).is_relative_to(self.tmp)
    def temp_path(self,raw):
        self.validate_tmp();p=self.destination(raw)
        if not p.is_relative_to(self.tmp):self.deny(raw,"NOT_PRIVATE_TMP")
        return p
    def bind(self,p,kind="file"):
        p=Path(p)
        if str(p) not in self.created or self.created[str(p)].get("deleted"):self.deny(p,"TEMP_NOT_CREATED_BY_THIS_PROCESS")
        s=p.lstat();wanted=stat.S_ISREG(s.st_mode) if kind=="file" else stat.S_ISDIR(s.st_mode)
        if not wanted or s.st_uid!=os.geteuid() or stat.S_IMODE(s.st_mode)!=(0o600 if kind=="file" else 0o700):self.deny(p,"TEMP_OWNER_TYPE_OR_MODE")
        identity=[s.st_dev,s.st_ino,s.st_uid]
        v=self.created[str(p)]
        if "identity" in v and v["identity"]!=identity:self.deny(p,"TEMP_IDENTITY_REPLACED")
        v["identity"]=identity
        return identity
    def hook(self,event,args):
        if event=="open" and isinstance(args[0],(str,bytes,os.PathLike)):
            raw=os.fsdecode(args[0])
            if self.temp_candidate(raw):
                p=self.temp_path(raw);mode=str(args[1] or "");flags=int(args[2] or 0)
                writable=any(k in mode for k in ("w","a","x","+")) or bool(flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC))
                if p==self.tmp:
                    # io.open uses the directory as a placeholder; the trusted opener still
                    # performs a second, exclusive mkstemp open checked by this same hook.
                    frame=sys._getframe(1);placeholder=False
                    while frame:
                        if frame.f_code.co_filename=="/usr/lib/python3.14/tempfile.py" and frame.f_code.co_name=="NamedTemporaryFile":
                            opener=frame.f_locals.get("opener");directory=frame.f_locals.get("dir")
                            placeholder=(directory==str(self.tmp) and callable(opener) and opener.__code__.co_name=="opener" and opener.__code__.co_filename==frame.f_code.co_filename)
                            break
                        frame=frame.f_back
                    if not placeholder:self.deny(raw,"DIRECT_DIRECTORY_OR_ANONYMOUS_TMP_OPEN_NOT_AUTHORIZED")
                    self.record("TEMP_NAMED_FILE_DIRECTORY_PLACEHOLDER",path=str(p),mode=mode,flags=flags,actual_creation_requires_separate_exclusive_audit=True)
                    return
                if p.exists():
                    self.bind(p)
                else:
                    if not writable or not flags&os.O_CREAT or not flags&os.O_EXCL:self.deny(raw,"TEMP_EXCLUSIVE_CREATE_REQUIRED")
                    self.created[str(p)]={"kind":"file","deleted":False}
                self.record("TEMP_OPEN_AUTHORIZED",path=str(p),mode=mode,flags=flags,writable=writable)
                return
        if event in ("os.remove","os.rmdir") and args and isinstance(args[0],(str,bytes,os.PathLike)):
            raw=os.fsdecode(args[0])
            if self.temp_candidate(raw):
                if len(args)>1 and args[1] not in (-1,None):self.deny(raw,"TEMP_DIR_FD_NOT_AUTHORIZED")
                p=self.temp_path(raw)
                if p==self.tmp:self.deny(raw,"PRIVATE_TMP_ROOT_REMOVAL_PROHIBITED")
                self.bind(p,"file" if event=="os.remove" else "directory")
                self.record("TEMP_CLEANUP_AUTHORIZED",path=str(p),operation=event)
                return
        if event=="os.mkdir" and args and isinstance(args[0],(str,bytes,os.PathLike)):
            raw=os.fsdecode(args[0])
            if self.temp_candidate(raw):
                p=self.temp_path(raw)
                if p==self.tmp and p.is_dir():return
                if p.exists():self.deny(raw,"EXISTING_TEMP_DIRECTORY")
                self.created[str(p)]={"kind":"directory","deleted":False}
                self.record("TEMP_DIRECTORY_CREATE_AUTHORIZED",path=str(p))
                return
        return super().hook(event,args)
    def note_file_io(self,path,operation,byte_count):
        p=self.temp_path(path);self.bind(p)
        self.record("TEMP_FILE_OBJECT_IO_VERIFIED",path=str(p),operation=operation,bytes=byte_count)
    def install(self):
        # Wrappers always call the real OS functions; the audit hook still authorizes before OS access.
        super().install()
        for name in ("open","read","write","close","unlink","remove","rmdir"):self._original_io[name]=getattr(os,name)
        def wrapped_open(path,flags,mode=0o777,*,dir_fd=None):
            if dir_fd is not None:self.deny(str(path),"DIR_FD_OPEN_NOT_AUTHORIZED")
            fd=self._original_io["open"](path,flags,mode)
            if isinstance(path,(str,bytes,os.PathLike)) and self.temp_candidate(os.fsdecode(path)):
                p=self.temp_path(os.fsdecode(path));identity=self.bind(p)
                self.fds[fd]={"path":str(p),"identity":identity}
                self.record("TEMP_FD_OPEN_COMPLETED",path=str(p),fd=fd,flags=flags)
            return fd
        def fd_record(fd):
            v=self.fds.get(fd)
            if v:
                try:s=os.fstat(fd)
                except OSError:self.fds.pop(fd,None);return None
                if [s.st_dev,s.st_ino,s.st_uid]!=v["identity"]:self.fds.pop(fd,None);return None
            return v
        def wrapped_write(fd,data):
            v=fd_record(fd);n=self._original_io["write"](fd,data)
            if v:self.record("TEMP_FD_WRITE_COMPLETED",path=v["path"],fd=fd,bytes=n)
            return n
        def wrapped_read(fd,n):
            v=fd_record(fd);data=self._original_io["read"](fd,n)
            if v:self.record("TEMP_FD_READ_COMPLETED",path=v["path"],fd=fd,bytes=len(data))
            return data
        def wrapped_close(fd):
            v=fd_record(fd);result=self._original_io["close"](fd);self.fds.pop(fd,None)
            if v:self.record("TEMP_FD_CLOSE_COMPLETED",path=v["path"],fd=fd)
            return result
        def cleaner(name):
            def wrapped(path,*,dir_fd=None):
                if dir_fd is not None:self.deny(str(path),"DIR_FD_CLEANUP_NOT_AUTHORIZED")
                result=self._original_io[name](path)
                if isinstance(path,(str,bytes,os.PathLike)) and self.temp_candidate(os.fsdecode(path)):
                    p=self.temp_path(os.fsdecode(path));self.created[str(p)]["deleted"]=True
                    self.record("TEMP_CLEANUP_COMPLETED",path=str(p),operation=name)
                return result
            return wrapped
        os.open=wrapped_open;os.write=wrapped_write;os.read=wrapped_read;os.close=wrapped_close
        os.unlink=cleaner("unlink");os.remove=cleaner("remove");os.rmdir=cleaner("rmdir")
    def summary(self):
        return {**super().summary(),"private_tmp":str(self.tmp),"tmp_identity":list(self.tmp_identity),"tracked_temporary_paths":self.created,
          "temporary_paths_cleaned":sum(v.get("deleted",False) for v in self.created.values()),"io_instrumentation":"Real OS functions delegated; audit hook remains active. FD operations and verified fixture file-object I/O recorded; C file-object calls are not globally intercepted."}

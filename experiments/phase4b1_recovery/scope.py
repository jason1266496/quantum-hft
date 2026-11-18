"""Audit hook: exclusive run writes and exact, provenance-bound null type probes."""
import os,sys,stat,hashlib,json
from pathlib import Path
ROOT=Path("/home/jason/quantum-hft")
DILL=Path("/home/jason/.venvs/quantum-hft-qml/lib/python3.14/site-packages/dill/_dill.py")
ACTIVE=None
class ScopeViolation(RuntimeError):pass
class WriteScope:
    def __init__(self,run,*,unit=True,report=None):
        self.run=Path(run).resolve(strict=True);self.unit=unit;self.report=Path(report) if report else None
        if not self.run.is_relative_to(ROOT/"artifacts"):raise ValueError("INVALID_RUN_SCOPE")
        s=Path("/dev/null").lstat()
        if Path("/dev/null").is_symlink() or Path("/dev/null").resolve()!=Path("/dev/null") or not stat.S_ISCHR(s.st_mode) or (os.major(s.st_rdev),os.minor(s.st_rdev))!=(1,3):raise ValueError("NOT_REAL_NULL_DEVICE")
        self.null_identity=(s.st_dev,s.st_ino,s.st_rdev);self.events=[];self.current_test=None
        self.dill_sha=hashlib.sha256(DILL.read_bytes()).hexdigest()
    def record(self,kind,**kw):
        self.events.append({"kind":kind,"test":self.current_test,**kw})
    def deny(self,path,reason="UNIT_WRITE_SCOPE",**kw):
        self.record("DENIED",path=str(path),reason=reason,**kw)
        raise ScopeViolation(reason+": "+str(path))
    def null_probe(self,raw,mode,flags):
        if raw!="/dev/null":return False
        s=Path(raw).lstat()
        if (s.st_dev,s.st_ino,s.st_rdev)!=self.null_identity or not stat.S_ISCHR(s.st_mode) or Path(raw).is_symlink():return False
        frame=sys._getframe(1)
        while frame:
            if frame.f_code.co_filename==str(DILL) and frame.f_code.co_name=="get_file_type" and frame.f_lineno==165:
                args=frame.f_locals.get("args",());kwargs=frame.f_locals.get("kwargs",{})
                if len(args)!=1 or args[0] not in ("r+b","wb") or kwargs.get("buffering")!=-1:return False
                original=args[0];extra=getattr(os,"O_CLOEXEC",0)|getattr(os,"O_LARGEFILE",0)|getattr(os,"O_BINARY",0)
                expected=os.O_RDWR if original=="r+b" else os.O_WRONLY|os.O_CREAT|os.O_TRUNC
                if (flags&~extra)!=expected:return False
                self.record("ALLOWED_NULL_TYPE_PROBE",path=raw,mode=mode,original_mode=original,flags=flags,buffering=-1,
                    caller_file=str(DILL),caller_function="get_file_type",caller_line=165,device_identity=list(self.null_identity))
                return True
            frame=frame.f_back
        return False
    def destination(self,raw):
        p=Path(raw);p=p if p.is_absolute() else Path.cwd()/p
        resolved=p.resolve(strict=False)
        if any(q.is_symlink() for q in (p,*p.parents)):self.deny(raw,"UNIT_WRITE_SCOPE_SYMLINK",resolved=str(resolved))
        if not (resolved.is_relative_to(self.run) or (self.report is not None and resolved==self.report)):
            self.deny(raw,resolved=str(resolved))
        return resolved
    def hook(self,event,args):
        if event in ("socket.connect","socket.getaddrinfo","subprocess.Popen"):self.deny(event,"NETWORK_SUBPROCESS_PROHIBITED")
        if event in ("os.remove","os.rmdir","os.rename","os.link","os.symlink","os.chmod","os.chown","os.truncate"):
            self.deny(str(args[0]) if args else event,"MUTATION_NOT_AUTHORIZED",operation=event)
        if event=="os.mkdir":
            raw=os.fsdecode(args[0]);p=Path(raw);p=p if p.is_absolute() else Path.cwd()/p
            if self.report is not None and p==self.report.parent and p.is_dir() and not p.is_symlink():return
            self.destination(raw);return
        if event!="open" or not isinstance(args[0],(str,bytes,os.PathLike)):return
        raw=os.fsdecode(args[0]);mode=str(args[1] or "");flags=int(args[2] or 0)
        writable=any(k in mode for k in ("w","a","x","+")) or bool(flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC))
        if writable:
            if self.null_probe(raw,mode,flags):return
            p=self.destination(raw)
            if p.exists() or not flags&os.O_EXCL or not flags&os.O_CREAT:self.deny(raw,"EXCLUSIVE_NEW_FILE_REQUIRED",mode=mode,flags=flags)
            return
        p=Path(raw);p=p if p.is_absolute() else Path.cwd()/p
        if p.suffix==".csv" and any("holdout" in part.lower() for part in p.parts):self.deny(raw,"HOLDOUT_READ_PROHIBITED")
        frame=sys._getframe(1)
        while frame:
            if not self.unit and frame.f_code.co_name=="sha" and frame.f_code.co_filename==str(ROOT/"experiments/phase4a1/contracts.py"):return
            frame=frame.f_back
        if p.suffix in (".csv",".npy") and p.is_relative_to(ROOT/"artifacts"):
            if p.is_relative_to(self.run):return
            train=ROOT/"artifacts/datasets/btcusdt_aggregate_v1_20261026T202040Z/1000ms/train.csv"
            if not self.unit and p==train:return
            self.deny(raw,"OFFICIAL_VALUES_PROHIBITED")
    def install(self):
        global ACTIVE
        ACTIVE=self;sys.addaudithook(self.hook)
    def summary(self):
        return {"scope":str(self.run),"unit":self.unit,"dill_source_sha256":self.dill_sha,"null_identity":list(self.null_identity),
          "allowed_null_probes":sum(e["kind"]=="ALLOWED_NULL_TYPE_PROBE" for e in self.events),
          "denied_events":sum(e["kind"]=="DENIED" for e in self.events),"events":self.events}

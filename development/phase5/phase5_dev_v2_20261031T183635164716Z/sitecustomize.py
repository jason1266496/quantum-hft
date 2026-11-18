"""Python-level observable events. Native and pre-hook access are not observable here."""
import os,sys
_fd=None
_name=os.environ.get('PHASE5_AUDIT_LOG')
if _name:
    _fd=os.open(_name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_CLOEXEC,0o600)
    def _audit(event,args):
        if event in ('open','os.listdir','os.scandir','subprocess.Popen','socket.connect'):
            try:
                data=(event+' '+repr(args)[:1000]+'\n').encode('utf-8','backslashreplace')
                os.write(_fd,data)
            except Exception:
                pass
    sys.addaudithook(_audit)

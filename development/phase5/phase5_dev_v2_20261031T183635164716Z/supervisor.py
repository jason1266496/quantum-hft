"""One-child-at-a-time OS-isolated supervisor with reaping and trace preservation."""
import hashlib,json,os,pathlib,resource,signal,subprocess,time
PYTHON='/home/jason/.venvs/quantum-hft-qml/bin/python'
BWRAP='/usr/bin/bwrap'
class BoundaryError(RuntimeError):pass

def command(source,run,script,args,name,timeout=30,cancel=None,term_grace=0.2):
    source=pathlib.Path(source).resolve(strict=True);run=pathlib.Path(run).resolve(strict=True)
    if not source.is_dir() or not run.is_dir():raise BoundaryError('MISSING_ROOT')
    if script not in [p.name for p in source.glob('*.py')]:raise BoundaryError('SCRIPT_NOT_IN_LOCKED_SOURCE')
    if not (source/script).is_file():raise BoundaryError('MISSING_SCRIPT')
    logs=run/'commands';audits=run/'access_events';logs.mkdir(exist_ok=True);audits.mkdir(exist_ok=True)
    stdout_path=logs/f'{name}.stdout';stderr_path=logs/f'{name}.stderr';record_path=logs/f'{name}.json'
    for p in (stdout_path,stderr_path,record_path,audits/f'{name}.events'):
        if p.exists():raise BoundaryError('NO_OVERWRITE')
    env={k:v for k,v in os.environ.items() if k in ('PATH','LANG','LC_ALL')}
    env.update({'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1','NUMEXPR_NUM_THREADS':'1','VECLIB_MAXIMUM_THREADS':'1','PYTHONDONTWRITEBYTECODE':'1','PYTHONPATH':'/work/source','PYTHONNOUSERSITE':'1','TMPDIR':'/work/run/tmp','HOME':'/work/run/tmp','PHASE5_AUDIT_LOG':f'/work/run/access_events/{name}.events'})
    # Mount only the locked source, this run, Python environment and system libraries.
    argv=[BWRAP,'--die-with-parent','--ro-bind','/usr','/usr','--ro-bind','/lib','/lib','--ro-bind','/lib64','/lib64','--ro-bind','/home/jason/.venvs/quantum-hft-qml','/home/jason/.venvs/quantum-hft-qml','--dev','/dev','--proc','/proc','--tmpfs','/tmp','--dir','/work','--ro-bind',str(source),'/work/source','--bind',str(run),'/work/run','--chdir','/work/source']
    for k,v in env.items():argv+=['--setenv',k,v]
    argv += [PYTHON,f'/work/source/{script}',*map(str,args)]
    begin=time.monotonic();before=resource.getrusage(resource.RUSAGE_CHILDREN);reason='normal';term_sent=False;kill_sent=False
    with stdout_path.open('xb') as out,stderr_path.open('xb') as err:
        proc=subprocess.Popen(argv,stdout=out,stderr=err,start_new_session=True,close_fds=True)
        while proc.poll() is None:
            if cancel is not None and cancel.is_set():reason='cancelled';break
            if time.monotonic()-begin>timeout:reason='timeout';break
            time.sleep(0.02)
        if reason!='normal' and proc.poll() is None:
            try:os.killpg(proc.pid,signal.SIGTERM);term_sent=True
            except ProcessLookupError:pass
            if term_grace>0:
                try:proc.wait(timeout=term_grace)
                except subprocess.TimeoutExpired:pass
            if proc.poll() is None or term_grace==0:
                try:os.killpg(proc.pid,signal.SIGKILL);kill_sent=True
                except ProcessLookupError:pass
        exit_code=proc.wait(timeout=2)
    after=resource.getrusage(resource.RUSAGE_CHILDREN)
    rec={'name':name,'argv':argv,'exit_code':exit_code,'reason':reason,'sigterm_sent':term_sent,'sigkill_sent':kill_sent,'reaped':proc.poll() is not None,'child_pid':proc.pid,'wall_time_s':time.monotonic()-begin,'cpu_time_s':after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime,'peak_rss_kb':after.ru_maxrss,'stdout_path':str(stdout_path.relative_to(run)),'stderr_path':str(stderr_path.relative_to(run)),'stdout_sha256':hashlib.sha256(stdout_path.read_bytes()).hexdigest(),'stderr_sha256':hashlib.sha256(stderr_path.read_bytes()).hexdigest(),'audit_path':str((audits/f'{name}.events').relative_to(run)),'timeout_s':timeout}
    with record_path.open('x') as f:json.dump(rec,f,indent=2);f.write('\n')
    return rec

import json,os,pathlib,re,sys,tempfile,threading,time
import safe_io,supervisor

def case(name,expected,actual,evidence=None):return {'test':name,'expected':expected,'actual':actual,'status':'PASS' if expected==actual else 'FAIL','evidence':evidence or {}}
def group_gone(pid):
    try:os.killpg(pid,0);return False
    except ProcessLookupError:return True

def run(source,run):
    tests=[];f=run/'synthetic_fixture';f.mkdir(exist_ok=False);(f/'inside.txt').write_text('SYNTHETIC_ONLY')
    outside=run/'outside_substitute.txt';outside.write_text('SYNTHETIC_ONLY')
    host_outside=source.parents[1]/f'boundary_substitute_{run.name}.txt'
    with host_outside.open('x') as fh:fh.write('SYNTHETIC_ONLY')
    (f/'link.txt').symlink_to(outside)
    os.link(outside,f/'hard.txt')
    def reject(path):
        try:safe_io.read_fixture(f,path);return 'ACCEPTED'
        except safe_io.PathRejected:return 'REJECTED'
    tests.append(case('fixture valid read',b'SYNTHETIC_ONLY'.hex(),safe_io.read_fixture(f,'inside.txt').hex()))
    for name,path in [('traversal','../outside_substitute.txt'),('absolute',str(outside)),('symlink','link.txt'),('hardlink','hard.txt')]:
        tests.append(case('fixture '+name+' rejected','REJECTED',reject(path),{'synthetic_substitute':str(outside)}))
    safe_io.exclusive_write(f,'output.txt',b'original')
    try:safe_io.exclusive_write(f,'output.txt',b'replacement');overwrote=True
    except FileExistsError:overwrote=False
    tests.append(case('exclusive output no overwrite',False,overwrote,{'content':(f/'output.txt').read_text()}))
    modes=[('normal',4,0.2,None),('early',4,0.2,None),('timeout',0.2,0,None),('outside',4,0.2,None),('tmpdir',4,0.2,None)]
    records={}
    for mode,timeout,grace,cancel in modes:
        records[mode]=supervisor.command(source,run,'safety_child.py',[mode,str(host_outside)] if mode=='outside' else [mode],f'safety_{mode}',timeout=timeout,term_grace=grace,cancel=cancel)
    e=threading.Event();timer=threading.Timer(0.2,e.set);timer.start()
    try:records['cancel']=supervisor.command(source,run,'safety_child.py',['cancel'],'safety_cancel',timeout=4,cancel=e,term_grace=0)
    finally:timer.cancel()
    tests.append(case('child normal exit',(0,'normal',True),(records['normal']['exit_code'],records['normal']['reason'],records['normal']['reaped'])))
    early_err=(run/'commands/safety_early.stderr').read_text()
    tests.append(case('early exit traceback',(7,True),(records['early']['exit_code'],'Traceback' in early_err),{'stderr_path':'commands/safety_early.stderr'}))
    for mode,reason in [('timeout','timeout'),('cancel','cancelled')]:
        x=records[mode]
        tests.append(case(mode+' SIGTERM SIGKILL reap',(reason,True,True,True,True),(x['reason'],x['sigterm_sent'],x['sigkill_sent'],x['reaped'],group_gone(x['child_pid'])),{'record':f'commands/safety_{mode}.json'}))
    outside_stdout=(run/'commands/safety_outside.stdout').read_text()
    tests.append(case('OS unauthorized read rejected',(0,True),(records['outside']['exit_code'],'OUTSIDE_EXISTS=False' in outside_stdout),{'synthetic_substitute':str(host_outside),'host_exists':host_outside.is_file()}))
    tmp_stdout=(run/'commands/safety_tmpdir.stdout').read_text()
    tests.append(case('private TMPDIR',True,'TMPDIR=/work/run/tmp' in tmp_stdout and 'TMPFILE=/work/run/tmp/' in tmp_stdout))
    tests.append(case('pycache suppressed',True,not any(run.rglob('__pycache__')) and not any(source.rglob('__pycache__'))))
    try:supervisor.command(source,run,'safety_child.py',['normal'],'safety_normal');duplicate='ACCEPTED'
    except supervisor.BoundaryError:duplicate='REJECTED'
    tests.append(case('supervisor no overwrite','REJECTED',duplicate))
    event_files=list((run/'access_events').glob('safety_*.events'))
    tests.append(case('Python access events recorded',True,len(event_files)==6 and any('open' in p.read_text() for p in event_files),{'event_files':[str(p.relative_to(run)) for p in event_files]}))
    with (run/'safety_tests.json').open('x') as fh:json.dump(tests,fh,indent=2);fh.write('\n')
    return tests
if __name__=='__main__':
    source=pathlib.Path(sys.argv[1]);run_path=pathlib.Path(sys.argv[2]);tests=run(source,run_path)
    print(json.dumps({'tests':len(tests),'passed':sum(x['status']=='PASS' for x in tests),'failed':[x['test'] for x in tests if x['status']=='FAIL']}),flush=True)
    sys.exit(0 if all(x['status']=='PASS' for x in tests) else 1)

import datetime,hashlib,json,os,pathlib,resource,shutil,sys,time,traceback
import supervisor
ROOT=pathlib.Path(__file__).resolve().parent
SOURCE=('core.py','oracle.py','verify.py','qaoa_v2.py','sitecustomize.py','safe_io.py','supervisor.py','safety_child.py','safety_gate.py','math_gate.py','predictor_source.py','synthetic_signal.py','p2_gate.py','runner.py')
GLOBAL_SECONDS=1800
CAPACITY_BYTES=128*1024*1024

def dump(path,obj):
    with path.open('x') as f:json.dump(obj,f,indent=2,sort_keys=True);f.write('\n')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def size(root):return sum(p.stat().st_size for p in root.rglob('*') if p.is_file())
def gate(rec,label):
    if rec['reason']!='normal' or rec['exit_code']!=0:raise RuntimeError(f'{label} child failure reason={rec["reason"]} code={rec["exit_code"]}')
def json_tests(path):
    tests=json.loads(path.read_text())
    if not tests or any(x['status']!='PASS' or not all(k in x for k in ('expected','actual','evidence')) for x in tests):raise RuntimeError(f'TEST_GATE_FAIL {path}')
    return len(tests)
def limits(run,start):
    if time.monotonic()-start>GLOBAL_SECONDS:raise TimeoutError('GLOBAL_TIME_LIMIT')
    if size(run)>CAPACITY_BYTES:raise RuntimeError('RUN_CAPACITY_LIMIT')

def summarize(rows):
    n=len(rows)
    return {'jobs':n,'cost_evaluations':sum(j['cost_evaluations'] for j in rows),'statevector_constructions':sum(j['statevector_constructions'] for j in rows),'extra_diagnostic_statevectors':sum(j['extra_diagnostic_statevectors'] for j in rows),'shots':sum(j['shots'] for j in rows),'mean_energy':sum(j['energy'] for j in rows)/n,'mean_feasible_probability':sum(j['feasible_probability'] for j in rows)/n,'mean_infeasible_probability':sum(j['infeasible_probability'] for j in rows)/n,'mean_optimal_probability':sum(j['optimal_probability'] for j in rows)/n,'mean_expectation_gap':sum(j['expectation_optimality_gap'] for j in rows)/n,'optimizer_success_jobs':sum(j['optimizer']['success'] for j in rows),'wall_time_s':sum(j['wall_time_s'] for j in rows),'cpu_time_s':sum(j['cpu_time_s'] for j in rows),'peak_rss_kb':max(j['peak_rss_kb'] for j in rows)}

def main():
    run=ROOT/datetime.datetime.now(datetime.UTC).strftime('phase5_v2_run_%Y%m%dT%H%M%S%fZ');run.mkdir(exist_ok=False);start=time.monotonic()
    status={'P0':'BLOCKED','P1':'BLOCKED','P2':'BLOCKED','access_audit':'AUDIT_INCOMPLETE'}
    for d in ('source','tmp','jobs','commands','access_events'):(run/d).mkdir(exist_ok=False)
    source=run/'source';completed=0
    try:
        for name in SOURCE:shutil.copyfile(ROOT/name,source/name)
        source_sha={name:sha(source/name) for name in SOURCE};dump(run/'source_manifest.json',source_sha)
        dump(run/'input_manifest.json',{'type':'SYNTHETIC_ONLY','mu':['2','4','0','-1/2','-1'],'q':[0,1,2,3],'q_prev':1,'c':'1','rho':'1/2','master_seed':20261101,'seed_slots':[11,23,37,53,71],'seed_derivation':{'initial':'SeedSequence([master_seed, instance, depth, seed])','sampling':'SeedSequence([master_seed, instance, depth, seed, 4096])'}})
        dump(run/'protocol.json',{'qaoa_jobs':100,'cost_evaluations_per_job_max':200,'shots_per_job':4096,'job_timeout_seconds':30,'global_seconds':GLOBAL_SECONDS,'run_capacity_bytes':CAPACITY_BYTES,'network_namespace_enforced':False,'python_bytecode_write_disabled':True,'private_tmpdir':'/work/run/tmp','history_run_immutable':'phase5_run_20261031T181924625777Z'})
        for f in source.iterdir():f.chmod(0o444)
        source.chmod(0o555)
        # Safety gate is outside bwrap because it supervises and tests bwrap children.
        import safety_gate
        safety=safety_gate.run(source,run)
        count=json_tests(run/'safety_tests.json');print(f'PHASE=SAFETY passed={count}',flush=True)
        rec=supervisor.command(source,run,'verify.py',['/work/run/p0'],'p0',timeout=30);gate(rec,'p0')
        p0_count=json_tests(run/'p0/p0_tests.json')
        audit=json.loads((run/'p0/energy_audit.json').read_text())
        if len(audit)!=80:raise RuntimeError('80_STATE_GATE_FAIL')
        status['P0']='PASS';print(f'PHASE=P0 passed={p0_count} states=80',flush=True)
        rec=supervisor.command(source,run,'math_gate.py',['/work/run/math_tests.json'],'math',timeout=30);gate(rec,'math')
        math_count=json_tests(run/'math_tests.json');print(f'PHASE=MATH passed={math_count}',flush=True)
        rec=supervisor.command(source,run,'p2_gate.py',['/work/run/p2_pre'],'p2_pre',timeout=30);gate(rec,'p2_pre')
        p2_count=json_tests(run/'p2_pre/tests.json');print(f'PHASE=P2_PRE passed={p2_count}',flush=True)
        rec=supervisor.command(source,run,'qaoa_v2.py',['/work/run/smoke.json','smoke',0,1,0],'smoke',timeout=30);gate(rec,'smoke')
        smoke=json.loads((run/'smoke.json').read_text())
        if smoke['sampling_method']!='Statevector.sample_counts' or smoke['statevector_constructions']!=smoke['cost_evaluations']+1:raise RuntimeError('SMOKE_GATE_FAIL')
        print(f'PHASE=SMOKE evaluations={smoke["cost_evaluations"]} vectors={smoke["statevector_constructions"]}',flush=True)
        data={'first':[],'repeat':[]}
        for phase in ('first','repeat'):
            for i in range(5):
                for depth in (1,2):
                    for slot in range(5):
                        limits(run,start);name=f'{phase}_i{i}_p{depth}_s{slot}'
                        rec=supervisor.command(source,run,'qaoa_v2.py',[f'/work/run/jobs/{name}.json',phase,i,depth,slot],name,timeout=30);gate(rec,name)
                        j=json.loads((run/'jobs'/f'{name}.json').read_text());raw=dict(j);saved=raw.pop('sha256')
                        if hashlib.sha256(json.dumps(raw,sort_keys=True,separators=(',',':')).encode()).hexdigest()!=saved:raise RuntimeError('JOB_SHA_MISMATCH')
                        if j['qaoa_source_sha256']!=source_sha['qaoa_v2.py'] or j['cost_evaluations']>200 or j['statevector_constructions']!=j['cost_evaluations']+1 or sum(j['counts'].values())!=4096:raise RuntimeError('JOB_CONTRACT_FAIL')
                        data[phase].append(j);completed+=1
                        elapsed=time.monotonic()-start;print(f'phase={phase} instance={i+1}/5 depth={depth} seed={slot+1}/5 cost_eval={j["cost_evaluations"]}/200 jobs={completed}/100 pct={completed}% elapsed={elapsed:.1f}s failures=0 ETA={(100-completed)*elapsed/completed:.1f}s',flush=True)
        for phase in data:
            dump(run/f'{phase}_results.json',{'jobs':[{'file':f'jobs/{phase}_i{j["instance"]}_p{j["depth"]}_s{j["slot"]}.json','payload_sha256':j['sha256']} for j in data[phase]],'summary':summarize(data[phase])})
        fields=('instance','depth','slot','seed','initial_parameters','selected_parameters','selected_evaluation','evaluation_trace','cost_evaluations','statevector_constructions','statevector_amplitudes','probabilities','counts','energy','feasible_probability','optimal_probability')
        pairs=[{'instance':a['instance'],'depth':a['depth'],'slot':a['slot'],'matches':{f:a[f]==b[f] for f in fields}} for a,b in zip(data['first'],data['repeat'])]
        deterministic=len(pairs)==50 and all(all(x['matches'].values()) for x in pairs)
        dump(run/'determinism.json',{'pairs':pairs,'all_match':deterministic})
        dump(run/'first_repeat_tests.json',[{'test':'100 independent child jobs','expected':(50,50),'actual':(len(data['first']),len(data['repeat'])),'status':'PASS' if len(data['first'])==len(data['repeat'])==50 else 'FAIL','evidence':{'first':'first_results.json','repeat':'repeat_results.json'}},{'test':'50 paired deterministic payloads','expected':True,'actual':deterministic,'status':'PASS' if deterministic else 'FAIL','evidence':{'pairs':'determinism.json'}}])
        json_tests(run/'first_repeat_tests.json')
        dump(run/'comparison.json',{phase:{str(depth):summarize([j for j in data[phase] if j['depth']==depth]) for depth in (1,2)} for phase in data})
        status['P1']='PASS'
        rec=supervisor.command(source,run,'p2_gate.py',['/work/run/p2_post','/work/run/jobs/first_i0_p1_s0.json'],'p2_post',timeout=30);gate(rec,'p2_post')
        json_tests(run/'p2_post/tests.json');status['P2']='PASS'
        event_files=list((run/'access_events').glob('*.events'))
        event_counts={p.name:sum(1 for _ in p.open()) for p in event_files}
        dump(run/'access_audit.json',{'os_enforcement':'bwrap mount namespace: only read-only /usr /lib /lib64 Python venv and locked source; writable current run and private tmpfs /tmp','application_guard':'safe_io rejects path traversal, symlinks, hardlinks; exclusive output','python_event_audit':{'files':len(event_files),'events':sum(event_counts.values()),'per_file':event_counts,'limits':'Python hook starts in sitecustomize and cannot observe pre-hook or native C file access','status':'AUDIT_INCOMPLETE'},'network_namespace':'UNAVAILABLE: bwrap --unshare-net failed; no network APIs used','history_exception':'prior AGENTS filename enumeration preserved in old development copy','full_no_open_claim':False})
        dump(run/'environment.json',{'versions':data['first'][0]['environment'],'python':supervisor.PYTHON,'network_namespace':'UNAVAILABLE','thread_limits':'1','tmpdir':'/work/run/tmp'})
        dump(run/'timing_memory.json',{'total_wall_time_s':time.monotonic()-start,'qaoa_wall_time_s':sum(j['wall_time_s'] for rows in data.values() for j in rows),'qaoa_cpu_time_s':sum(j['cpu_time_s'] for rows in data.values() for j in rows),'qaoa_peak_rss_kb':max(j['peak_rss_kb'] for rows in data.values() for j in rows)})
        dump(run/'completion_report.json',{'status':status,'formal_acceptance':'BLOCKED_BY_AUDIT_INCOMPLETE','run_id':run.name,'jobs':completed,'cost_evaluations':sum(j['cost_evaluations'] for rows in data.values() for j in rows),'statevector_constructions':sum(j['statevector_constructions'] for rows in data.values() for j in rows),'shots':sum(j['shots'] for rows in data.values() for j in rows),'unexecuted':['market data','live capture','QPU','real trading','paper trading','formal training','Phase 6']})
    except Exception as exc:
        dump(run/'failure_report.json',{'status':status,'reason':repr(exc),'traceback':traceback.format_exc(),'completed_jobs':completed,'wall_time_s':time.monotonic()-start})
        print(f'PHASE=FAIL reason={exc}',file=sys.stderr,flush=True)
    finally:
        manifest={str(p.relative_to(run)):sha(p) for p in run.rglob('*') if p.is_file() and p.name!='sha256_manifest.json'}
        dump(run/'sha256_manifest.json',manifest)
        print(f'RUN_PATH={run} STATUS={status}',flush=True)
    return 0 if status['P0']==status['P1']==status['P2']=='PASS' else 1
if __name__=='__main__':sys.exit(main())

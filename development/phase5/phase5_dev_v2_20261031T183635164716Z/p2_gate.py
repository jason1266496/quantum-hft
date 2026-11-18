import copy,hashlib,json,pathlib,sys
import core,qaoa_v2,synthetic_signal as ss

def fixture(source):
    predictor=(source/'predictor_source.py').read_bytes();psha=hashlib.sha256(predictor).hexdigest()
    calibration={'calibration_id':'CAL-SYN-001','predictor_id':'SYN-P','predictor_version':'v2','prediction_class':'UP','horizon_ms':1000,'synthetic_expected_return':'2','provenance':'SYNTHETIC_ONLY'}
    record={'sample_id':'SYN-001','predictor_id':'SYN-P','predictor_version':'v2','predictor_source_sha256':psha,'prediction_class':'UP','horizon_ms':1000,
    'prediction_available_time':'2026-11-01T00:00:00Z','decision_time':'2026-11-01T00:00:00.001Z','clock_id':ss.CLOCK,'timestamp_semantics':ss.SEMANTICS,
    'calibration_id':calibration['calibration_id'],'calibration_sha256':ss.digest(calibration),'provenance':'SYNTHETIC_ONLY',
    'provenance_sha256':ss.digest({'type':'SYNTHETIC_ONLY','predictor_source_sha256':psha,'sample_id':'SYN-001'}),
    'synthetic_expected_return':'2','risk':'1/2','cost_assumption':'1'}
    return predictor,calibration,record

def outcome(fn):
    try:fn();return 'ACCEPTED'
    except ss.SignalError as exc:return str(exc)

def test(name,expected,actual,evidence=None):return {'test':name,'expected':expected,'actual':actual,'status':'PASS' if expected==actual else 'FAIL','evidence':evidence or {}}
def run(out,source,actual_job=None):
    predictor,calibration,record=fixture(source)
    if actual_job is None:
        job=qaoa_v2.job(0,1,0,'smoke',False);job['phase']='first';raw=dict(job);raw.pop('sha256');job['sha256']=ss.digest(raw)
    else:job=json.loads(actual_job.read_text())
    expected_source=hashlib.sha256((source/'qaoa_v2.py').read_bytes()).hexdigest()
    tests=[]
    result=ss.solve(record,calibration,predictor,job,expected_source)
    tests.append(test('synthetic predictor calibration QUBO Exact QAOA',('SYNTHETIC_ONLY','-3/2'),(result['status'],result['exact_optimum']),result))
    tests.append(test('missing calibration','CALIBRATION_REQUIRED',outcome(lambda:ss.solve(record,None,predictor,job,expected_source))))
    for field in ('true_class','future_return_bps','validation_score'):
        r=dict(record,**{field:1})
        tests.append(test('future leakage '+field,'FUTURE_LEAKAGE_REJECTED',outcome(lambda r=r:ss.solve(r,calibration,predictor,job,expected_source))))
    r=dict(record,unexpected_field='x')
    tests.append(test('unknown field','SCHEMA_FIELDS_REJECTED',outcome(lambda:ss.solve(r,calibration,predictor,job,expected_source))))
    r=dict(record,decision_time='2026-10-31T23:59:59Z')
    tests.append(test('decision before availability','FUTURE_LEAKAGE_REJECTED',outcome(lambda:ss.solve(r,calibration,predictor,job,expected_source))))
    r=dict(record,horizon_ms=2000)
    tests.append(test('horizon fixed','HORIZON_CONTRACT',outcome(lambda:ss.solve(r,calibration,predictor,job,expected_source))))
    r=dict(record,clock_id='UNKNOWN')
    tests.append(test('clock semantics','TIMESTAMP_SEMANTICS',outcome(lambda:ss.solve(r,calibration,predictor,job,expected_source))))
    r=dict(record,calibration_sha256='0'*64)
    tests.append(test('calibration SHA','CALIBRATION_SHA_MISMATCH',outcome(lambda:ss.solve(r,calibration,predictor,job,expected_source))))
    r=dict(record,provenance_sha256='0'*64)
    tests.append(test('provenance SHA','PROVENANCE_SHA_MISMATCH',outcome(lambda:ss.solve(r,calibration,predictor,job,expected_source))))
    r=dict(record,predictor_source_sha256='0'*64)
    tests.append(test('predictor source SHA','PREDICTOR_SOURCE_SHA_MISMATCH',outcome(lambda:ss.solve(r,calibration,predictor,job,expected_source))))
    def mutated(**kwargs):
        j=dict(job,**kwargs);raw=dict(j);raw.pop('sha256');j['sha256']=ss.digest(raw);return j
    corrupt=dict(job,energy=job['energy']+1)
    tests.append(test('QAOA digest','QAOA_DIGEST_MISMATCH',outcome(lambda:ss.solve(record,calibration,predictor,corrupt,expected_source))))
    for name,kwargs,expected in [('source',{'qaoa_source_sha256':'0'*64},'QAOA_SOURCE_MISMATCH'),('instance',{'instance':4},'QAOA_INSTANCE_MISMATCH'),('semantics',{'sampled_statevector_source':'optimizer_final'},'QAOA_SEMANTICS_MISMATCH'),('shots',{'shots':4095},'QAOA_SHOT_CONTRACT')]:
        j=mutated(**kwargs)
        tests.append(test('QAOA '+name,expected,outcome(lambda j=j:ss.solve(record,calibration,predictor,j,expected_source))))
    out.mkdir(exist_ok=False)
    with (out/'tests.json').open('x') as f:json.dump(tests,f,indent=2);f.write('\n')
    with (out/'fixture_manifest.json').open('x') as f:json.dump({'predictor_source_sha256':hashlib.sha256(predictor).hexdigest(),'calibration':calibration,'record':record,'qaoa_source_sha256':expected_source},f,indent=2);f.write('\n')
    return tests
if __name__=='__main__':
    tests=run(pathlib.Path(sys.argv[1]),pathlib.Path(__file__).resolve().parent,pathlib.Path(sys.argv[2]) if len(sys.argv)>2 else None)
    print(json.dumps({'tests':len(tests),'passed':sum(t['status']=='PASS' for t in tests),'failed':[t['test'] for t in tests if t['status']=='FAIL']}),flush=True)
    sys.exit(0 if all(t['status']=='PASS' for t in tests) else 1)

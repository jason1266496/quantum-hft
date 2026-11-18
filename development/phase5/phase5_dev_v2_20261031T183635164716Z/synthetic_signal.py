import datetime,hashlib,json,math,pathlib
from fractions import Fraction as F
import core
class SignalError(ValueError):pass
FIELDS=frozenset(('sample_id','predictor_id','predictor_version','predictor_source_sha256','prediction_class','horizon_ms','prediction_available_time','decision_time','clock_id','timestamp_semantics','calibration_id','calibration_sha256','provenance','provenance_sha256','synthetic_expected_return','risk','cost_assumption'))
FORBIDDEN=frozenset(('true_class','future_return_bps','validation_score','future_price','macro_f1','realized_return'))
SEMANTICS='synthetic_UTC_instant_available_before_decision'
CLOCK='SYNTHETIC_UTC'
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def utc(value):
    if not isinstance(value,str) or not value.endswith('Z'):raise SignalError('TIMESTAMP_SEMANTICS')
    try:v=datetime.datetime.fromisoformat(value.replace('Z','+00:00'))
    except ValueError as e:raise SignalError('TIMESTAMP_SEMANTICS') from e
    if v.tzinfo!=datetime.timezone.utc:raise SignalError('TIMESTAMP_SEMANTICS')
    return v

def validate(record,calibration,predictor_source_bytes):
    if not isinstance(record,dict):raise SignalError('SCHEMA_REQUIRED')
    if FORBIDDEN.intersection(record):raise SignalError('FUTURE_LEAKAGE_REJECTED')
    if set(record)!=FIELDS:raise SignalError('SCHEMA_FIELDS_REJECTED')
    if record['provenance']!='SYNTHETIC_ONLY':raise SignalError('SYNTHETIC_ONLY_REQUIRED')
    if record['clock_id']!=CLOCK or record['timestamp_semantics']!=SEMANTICS:raise SignalError('TIMESTAMP_SEMANTICS')
    if record['horizon_ms']!=1000 or isinstance(record['horizon_ms'],bool):raise SignalError('HORIZON_CONTRACT')
    if utc(record['decision_time'])<utc(record['prediction_available_time']):raise SignalError('FUTURE_LEAKAGE_REJECTED')
    if not isinstance(predictor_source_bytes,bytes) or hashlib.sha256(predictor_source_bytes).hexdigest()!=record['predictor_source_sha256']:raise SignalError('PREDICTOR_SOURCE_SHA_MISMATCH')
    provenance={'type':'SYNTHETIC_ONLY','predictor_source_sha256':record['predictor_source_sha256'],'sample_id':record['sample_id']}
    if digest(provenance)!=record['provenance_sha256']:raise SignalError('PROVENANCE_SHA_MISMATCH')
    if calibration is None:raise SignalError('CALIBRATION_REQUIRED')
    if not isinstance(calibration,dict) or calibration.get('provenance')!='SYNTHETIC_ONLY':raise SignalError('CALIBRATION_REQUIRED')
    if digest(calibration)!=record['calibration_sha256']:raise SignalError('CALIBRATION_SHA_MISMATCH')
    for k in ('calibration_id','predictor_id','predictor_version','prediction_class','horizon_ms'):
        if calibration.get(k)!=record[k]:raise SignalError('CALIBRATION_REQUIRED')
    try:mu=core.finite_fraction(calibration['synthetic_expected_return']);stated=core.finite_fraction(record['synthetic_expected_return']);risk=core.finite_fraction(record['risk']);cost=core.finite_fraction(record['cost_assumption'])
    except (KeyError,ValueError) as e:raise SignalError('INVALID_NUMERIC') from e
    if mu!=stated:raise SignalError('CALIBRATION_MISMATCH')
    if mu not in core.MUS or risk!=F(1,2) or cost!=1:raise SignalError('FIXED_SYNTHETIC_CONTRACT')
    return mu

def validate_qaoa(payload,mu,expected_source_sha):
    if not isinstance(payload,dict):raise SignalError('QAOA_PAYLOAD_REQUIRED')
    raw=dict(payload);saved=raw.pop('sha256',None)
    if saved!=digest(raw):raise SignalError('QAOA_DIGEST_MISMATCH')
    if payload.get('qaoa_source_sha256')!=expected_source_sha:raise SignalError('QAOA_SOURCE_MISMATCH')
    if payload.get('instance')!=core.MUS.index(mu) or payload.get('mu')!=str(mu):raise SignalError('QAOA_INSTANCE_MISMATCH')
    if payload.get('sampled_statevector_source')!='lowest_evaluated_energy' or payload.get('cost_objective')!='scaled_ising_expectation' or payload.get('sampling_method')!='Statevector.sample_counts':raise SignalError('QAOA_SEMANTICS_MISMATCH')
    if payload.get('phase') not in ('first','repeat') or payload.get('depth') not in (1,2) or payload.get('seed') not in (11,23,37,53,71):raise SignalError('QAOA_SEMANTICS_MISMATCH')
    tr=payload.get('evaluation_trace')
    if not isinstance(tr,list) or len(tr)!=payload.get('cost_evaluations') or not 1<=len(tr)<=200:raise SignalError('QAOA_SEMANTICS_MISMATCH')
    selected=payload.get('selected_evaluation')
    if not isinstance(selected,int) or selected not in range(1,len(tr)+1):raise SignalError('QAOA_SEMANTICS_MISMATCH')
    row=tr[selected-1]
    if row['parameters']!=payload.get('selected_parameters') or abs(row['raw_energy']-payload.get('energy',float('nan')))>1e-9 or row['raw_energy']!=min(v['raw_energy'] for v in tr):raise SignalError('QAOA_SEMANTICS_MISMATCH')
    if abs(payload['energy']-(payload['selected_scaled_expectation']*payload['hamiltonian_scale']+float(F(payload['ising_offset']))))>1e-9:raise SignalError('QAOA_SEMANTICS_MISMATCH')
    if payload.get('statevector_constructions')!=len(tr)+payload.get('extra_diagnostic_statevectors') or payload.get('extra_diagnostic_statevectors')!=1:raise SignalError('QAOA_SEMANTICS_MISMATCH')
    if payload.get('shots')!=4096 or sum(payload.get('counts',{}).values())!=4096:raise SignalError('QAOA_SHOT_CONTRACT')
    amplitudes=payload.get('statevector_amplitudes');probs=payload.get('probabilities')
    if not isinstance(amplitudes,list) or len(amplitudes)!=16 or not isinstance(probs,dict) or len(probs)!=16:raise SignalError('QAOA_SEMANTICS_MISMATCH')
    for i,z in enumerate(amplitudes):
        bit=core.display(core.bits(i))
        if not math.isclose(z['real']**2+z['imag']**2,probs[bit],abs_tol=1e-10):raise SignalError('QAOA_SEMANTICS_MISMATCH')
    return True

def solve(record,calibration,predictor_source_bytes,payload,expected_source_sha):
    mu=validate(record,calibration,predictor_source_bytes)
    validate_qaoa(payload,mu,expected_source_sha)
    optimum,bits=core.direct(mu)
    return {'sample_id':record['sample_id'],'status':'SYNTHETIC_ONLY','exact_optimum':str(optimum),'optimal_bits':list(bits),'qaoa_job_sha256':payload['sha256'],'qaoa_energy':payload['energy'],'qaoa_best_sampled_feasible':payload['best_sampled_feasible']}

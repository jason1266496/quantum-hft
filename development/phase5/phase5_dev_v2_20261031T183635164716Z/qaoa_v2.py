import hashlib,json,math,os,pathlib,resource,sys,time,traceback
import numpy as np
from scipy.optimize import minimize
from qiskit.quantum_info import SparsePauliOp,Statevector
from qiskit.circuit.library import qaoa_ansatz
import core
MASTER_SEED=20261101
SEEDS=(11,23,37,53,71)

def version_check():
    import qiskit,scipy
    actual={'python':sys.version.split()[0],'qiskit':qiskit.__version__,'numpy':np.__version__,'scipy':scipy.__version__}
    expected={'python':'3.14.4','qiskit':'2.6.1','numpy':'2.5.4','scipy':'1.18.1'}
    if actual!=expected:raise RuntimeError(f'ENVIRONMENT_MISMATCH {actual}')
    return actual

def hamiltonian(coeff):
    entries=[]
    for i,h in enumerate(coeff['h']):
        label=['I']*4;label[3-i]='Z';entries.append((''.join(label),float(h)))
    for i in range(4):
        for j in range(i+1,4):
            label=['I']*4;label[3-i]=label[3-j]='Z';entries.append((''.join(label),float(coeff['J'][i][j])))
    scale=max(1.0,sum(abs(v) for _,v in entries))
    return SparsePauliOp.from_list([(label,value/scale) for label,value in entries]),scale

def initial_angles(instance,depth,seed,parameters):
    rng=np.random.default_rng(np.random.SeedSequence([MASTER_SEED,instance,depth,seed]))
    return np.array([rng.uniform(0,np.pi) if str(p).startswith('β') else rng.uniform(0,2*np.pi) for p in parameters],dtype=float)

def sampling_seed(instance,depth,seed):
    return int(np.random.SeedSequence([MASTER_SEED,instance,depth,seed,4096]).generate_state(1)[0])

def summarize_counts(counts,exact_bits,energies):
    full={core.display(core.bits(i)):int(counts.get(core.display(core.bits(i)),0)) for i in range(16)}
    if any(v<0 for v in full.values()):raise ValueError('negative count')
    total=sum(full.values())
    if total!=4096:raise ValueError('shot count mismatch')
    legal=[(energies[i],core.display(core.bits(i))) for i in range(16) if sum(core.bits(i))==1 and full[core.display(core.bits(i))]>0]
    return full,({'energy':min(legal)[0],'bits':min(legal)[1]} if legal else None)

def job(instance,depth,slot,phase,progress=True):
    started=time.monotonic();cpu=time.process_time();environment=version_check()
    if instance not in range(5) or depth not in (1,2) or slot not in range(5) or phase not in ('smoke','first','repeat'):raise ValueError('job arguments')
    seed=SEEDS[slot];mu=core.MUS[instance];qubo=core.compile_qubo(mu);ising=core.ising(qubo);op,scale=hamiltonian(ising)
    circuit=qaoa_ansatz(op,reps=depth);parameters=list(circuit.parameters)
    if circuit.num_qubits!=4 or len(parameters)!=2*depth:raise RuntimeError('circuit contract')
    initial=initial_angles(instance,depth,seed,parameters)
    energies=np.array([float(core.qubo_energy(core.bits(i),qubo)) for i in range(16)])
    trace=[];best=None;vector_count=0;last_update=time.monotonic()
    def make_state(theta):
        nonlocal vector_count
        if len(theta)!=len(parameters) or not all(math.isfinite(float(t)) for t in theta):raise ValueError('invalid parameters')
        vector_count+=1
        return Statevector.from_instruction(circuit.assign_parameters(dict(zip(parameters,map(float,theta)))))
    def cost(theta):
        nonlocal best,last_update
        state=make_state(theta)
        scaled=float(np.real(state.expectation_value(op)))
        raw=scaled*scale+float(ising['offset'])
        row={'evaluation':len(trace)+1,'parameters':[float(t) for t in theta],'scaled_expectation':scaled,'raw_energy':raw}
        trace.append(row)
        if best is None or raw<best['raw_energy']:
            best={'evaluation':len(trace),'parameters':row['parameters'],'scaled_expectation':scaled,'raw_energy':raw,'state':state}
        now=time.monotonic()
        if progress and (len(trace)%10==0 or now-last_update>=2):
            print(f'phase={phase} instance={instance+1}/5 depth={depth} seed={slot+1}/5 cost_eval={len(trace)}/200 elapsed={now-started:.1f}s',flush=True)
            last_update=now
        return scaled
    result=minimize(cost,initial,method='COBYLA',options={'maxiter':200,'tol':1e-6,'rhobeg':0.5})
    if not trace or len(trace)>200:raise RuntimeError('cost evaluation budget')
    diagnostic_state=make_state(result.x)
    diagnostic_scaled=float(np.real(diagnostic_state.expectation_value(op)))
    state=best['state'];state.seed(sampling_seed(instance,depth,seed))
    observed=state.sample_counts(4096)
    exact,optimum_bits,_=core.enumerate_exact(mu)
    counts,sampled_best=summarize_counts(observed,optimum_bits,energies)
    prob=np.asarray(state.probabilities(),dtype=float)
    feasible=float(sum(prob[i] for i in range(16) if sum(core.bits(i))==1))
    optimal=float(sum(prob[i] for i in range(16) if core.display(core.bits(i)) in optimum_bits))
    if abs(float(prob.sum())-1)>1e-10:raise RuntimeError('probability normalization')
    vector=[{'real':float(z.real),'imag':float(z.imag)} for z in state.data]
    result_data={'instance':instance,'mu':str(mu),'depth':depth,'slot':slot,'seed':seed,'master_seed':MASTER_SEED,'phase':phase,
        'seed_derivation':{'initial':'SeedSequence([master_seed, instance, depth, seed])','sampling':'SeedSequence([master_seed, instance, depth, seed, 4096])'},
        'parameter_names':[str(p) for p in parameters],'initial_parameters':initial.tolist(),'optimizer_parameters':[float(v) for v in result.x],
        'selected_parameters':best['parameters'],'selected_evaluation':best['evaluation'],'sampled_statevector_source':'lowest_evaluated_energy',
        'cost_objective':'scaled_ising_expectation','hamiltonian_scale':scale,'ising_offset':str(ising['offset']),
        'evaluation_trace':trace,'cost_evaluations':len(trace),'statevector_constructions':vector_count,'extra_diagnostic_statevectors':1,
        'optimizer':{'success':bool(result.success),'status':int(result.status),'message':str(result.message),'fun_scaled':float(result.fun)},
        'optimizer_final_diagnostic':{'scaled_expectation':diagnostic_scaled,'raw_energy':diagnostic_scaled*scale+float(ising['offset'])},
        'selected_scaled_expectation':best['scaled_expectation'],'energy':best['raw_energy'],'statevector_amplitudes':vector,
        'probabilities':{core.display(core.bits(i)):float(prob[i]) for i in range(16)},'sampling_method':'Statevector.sample_counts','sampling_seed':sampling_seed(instance,depth,seed),'shots':4096,'counts':counts,
        'feasible_probability':feasible,'infeasible_probability':1-feasible,'optimal_probability':optimal,
        'best_sampled_feasible':sampled_best,'exact_optimum':str(exact),'exact_optimal_bits':list(optimum_bits),
        'sampled_optimality_gap':sampled_best['energy']-float(exact) if sampled_best else None,
        'expectation_optimality_gap':best['raw_energy']-float(exact),
        'wall_time_s':time.monotonic()-started,'cpu_time_s':time.process_time()-cpu,'peak_rss_kb':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'environment':environment,'exit_code':0,'qaoa_source_sha256':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest()}
    raw=json.dumps(result_data,sort_keys=True,separators=(',',':')).encode();result_data['sha256']=hashlib.sha256(raw).hexdigest()
    return result_data

if __name__=='__main__':
    try:
        out=pathlib.Path(sys.argv[1]);data=job(int(sys.argv[3]),int(sys.argv[4]),int(sys.argv[5]),sys.argv[2])
        with out.open('x') as f:json.dump(data,f,indent=2);f.write('\n')
    except Exception:traceback.print_exc();sys.exit(1)

import json,math,pathlib,sys
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from qiskit.circuit.library import qaoa_ansatz
import core,oracle,qaoa_v2

def check(name,expected,actual,evidence=None):
    if isinstance(expected,np.generic):expected=expected.item()
    if isinstance(actual,np.generic):actual=actual.item()
    return {'test':name,'expected':expected,'actual':actual,'status':'PASS' if expected==actual else 'FAIL','evidence':evidence or {}}
def independent_circuit(ising,scale,depth,angles,params):
    c=QuantumCircuit(4);c.h(range(4))
    binding={str(p):float(a) for p,a in zip(params,angles)}
    for layer in range(depth):
        gamma=binding[f'γ[{layer}]'];beta=binding[f'β[{layer}]']
        for i in range(4):c.rz(2*gamma*float(ising['h'][i])/scale,i)
        for i in range(4):
            for j in range(i+1,4):c.rzz(2*gamma*float(ising['J'][i][j])/scale,i,j)
        for i in range(4):c.rx(2*beta,i)
    return c

def run(out):
    tests=[]
    for instance,mu in enumerate(core.MUS):
        q=core.compile_qubo(mu);ising=core.ising(q);op,scale=qaoa_v2.hamiltonian(ising)
        expected_scale=max(1.0,sum(abs(float(x)) for x in ising['h'])+sum(abs(float(ising['J'][i][j])) for i in range(4) for j in range(i+1,4)))
        tests.append(check(f'I{instance} Hamiltonian scale',expected_scale,scale))
        for index in range(16):
            x=core.bits(index);state=Statevector.from_int(index,16)
            actual=float(np.real(state.expectation_value(op)))*scale+float(ising['offset']);expected=float(oracle.original(mu,x))
            tests.append(check(f'I{instance} basis {index} energy',True,abs(actual-expected)<1e-10,{'expected_energy':expected,'actual_energy':actual,'bits':core.display(x)}))
    for depth in (1,2):
        q=core.compile_qubo(core.MUS[0]);ising=core.ising(q);op,scale=qaoa_v2.hamiltonian(ising);c=qaoa_ansatz(op,reps=depth);params=list(c.parameters)
        angles=qaoa_v2.initial_angles(0,depth,11,params)
        actual=Statevector.from_instruction(c.assign_parameters(dict(zip(params,angles))))
        independent=Statevector.from_instruction(independent_circuit(ising,scale,depth,angles,params))
        fidelity=abs(np.vdot(actual.data,independent.data))**2
        tests.append(check(f'p={depth} independent RZ RZZ RX',True,abs(fidelity-1)<1e-10,{'fidelity':float(fidelity)}))
        zero=Statevector.from_instruction(c.assign_parameters({p:0.0 for p in params})).probabilities()
        tests.append(check(f'p={depth} zero angles uniform',True,bool(np.allclose(zero,np.full(16,1/16),atol=1e-12))))
        tests.append(check(f'p={depth} parameter binding positive',0,len(c.assign_parameters(dict(zip(params,angles))).parameters)))
        try:Statevector.from_instruction(c.assign_parameters({params[0]:0.1}));negative='ACCEPTED'
        except Exception:negative='REJECTED'
        tests.append(check(f'p={depth} parameter binding partial negative','REJECTED',negative))
    tests.append(check('statevector bit order index8',8,int(np.argmax(Statevector.from_int(8,16).probabilities()))))
    counts={core.display(core.bits(0)):4096}
    full,best=qaoa_v2.summarize_counts(counts,('0010',),np.arange(16,dtype=float))
    tests.append(check('no legal shots',None,best))
    tests.append(check('illegal shots not renormalized',4096,full['0000']))
    job=qaoa_v2.job(0,1,0,'smoke',False)
    tests.append(check('optimizer budget exhaustion actual',(200,False),(job['cost_evaluations'],job['optimizer']['success']),{'status':job['optimizer']}))
    tests.append(check('sampled selected lowest evaluated',min(r['raw_energy'] for r in job['evaluation_trace']),job['energy']))
    tests.append(check('statevector count',job['cost_evaluations']+1,job['statevector_constructions']))
    tests.append(check('sampling method','Statevector.sample_counts',job['sampling_method']))
    tests.append(check('sampling reproducibility',job['counts'],qaoa_v2.job(0,1,0,'smoke',False)['counts']))
    with out.open('x') as f:json.dump(tests,f,indent=2);f.write('\n')
    return tests
if __name__=='__main__':
    tests=run(pathlib.Path(sys.argv[1]));print(json.dumps({'tests':len(tests),'passed':sum(t['status']=='PASS' for t in tests),'failed':[t['test'] for t in tests if t['status']=='FAIL']}),flush=True)
    sys.exit(0 if all(t['status']=='PASS' for t in tests) else 1)

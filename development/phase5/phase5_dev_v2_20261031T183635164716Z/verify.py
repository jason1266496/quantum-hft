import json,sys,hashlib,math, tempfile,pathlib
from fractions import Fraction as F
import core,oracle

def check(name,expected,actual,details=None):
    ok=expected==actual
    return {'test':name,'expected':core.jsonable(expected),'actual':core.jsonable(actual),'status':'PASS' if ok else 'FAIL','evidence':core.jsonable(details or {})}
def p0():
    tests=[]; audits=[]; results=[]
    for k,fix in enumerate(oracle.FIXED):
        mu=fix['mu']; q=core.compile_qubo(mu); z=core.ising(q)
        tests.append(check(f'I{k} candidate coefficients',fix['f'],q['f']))
        tests.append(check(f'I{k} penalty',fix['A'],q['A']))
        expected_u=tuple(tuple((fix['f'][i]-fix['A'] if i==j else 2*fix['A'] if i<j else F(0)) for j in range(4)) for i in range(4))
        tests.append(check(f'I{k} upper coefficients',expected_u,q['upper']))
        tests.append(check(f'I{k} symmetric coefficients',tuple(tuple(fix['f'][i]-fix['A'] if i==j else fix['A'] for j in range(4)) for i in range(4)),q['symmetric']))
        tests.append(check(f'I{k} constant',fix['A'],q['constant']))
        for i in range(16):
            x=core.bits(i); b=core.display(x)
            # oracle is original, unexpanded formula with independent penalty expression
            e=oracle.original(mu,x); eu=core.qubo_energy(x,q); es=core.qubo_energy(x,q,True); ei=core.ising_energy(x,z)
            row={'instance':k,'index':i,'bits':b,'original':e,'upper':eu,'symmetric':es,'ising':ei,'feasible':sum(x)==1,'match':e==eu==es==ei}
            audits.append(row)
            tests.append(check(f'I{k} state {b} all energies', (e,e,e),(eu,es,ei),row))
            tests.append(check(f'I{k} state {b} bit ordering',(i,x),(sum(v<<j for j,v in enumerate(core.decode(b))),core.decode(b))))
        expected_opt=(fix['optimum'],fix['optimal_bits']); direct=core.direct(mu); enumerated=core.enumerate_exact(mu)
        tests.append(check(f'I{k} direct exact and ties',expected_opt,direct))
        tests.append(check(f'I{k} enumeration exact and ties',expected_opt,enumerated[:2]))
        tests.append(check(f'I{k} penalty sufficiency',True,all(r['feasible'] for r in audits[-16:] if r['original']<=fix['optimum']),{'minimum_infeasible':min(r['original'] for r in audits[-16:] if not r['feasible'])}))
        results.append({'instance':k,'mu':mu,'qubo':q,'ising':z,'direct':direct,'enumerated':enumerated[:2]})
    tests.append(check('80 states complete',80,len(audits)))
    tests.append(check('one-hot count',5*4,sum(r['feasible'] for r in audits)))
    qq=core.compile_qubo(F(2))
    wrong=[list(row) for row in qq['upper']]
    wrong[0][1]=F(1)
    mutated=dict(qq,upper=tuple(tuple(row) for row in wrong))
    tests.append(check('wrong upper coefficient rejected',True,any(core.qubo_energy(core.bits(i),mutated)!=oracle.original(F(2),core.bits(i)) for i in range(16))))
    zz=core.ising(core.compile_qubo(F(2))); bad=dict(zz,offset=zz['offset']+1)
    tests.append(check('wrong Ising offset rejected',True,any(core.ising_energy(core.bits(i),bad)!=oracle.original(F(2),core.bits(i)) for i in range(16))))
    for v in (float('nan'),float('inf'),float('-inf')):
        try:core.compile_qubo(v); rejected=False
        except ValueError:rejected=True
        tests.append(check(f'nonfinite {v} rejected',True,rejected))
    for b in ('001','2abc','10000'):
        try:core.decode(b); rejected=False
        except ValueError:rejected=True
        tests.append(check(f'invalid bits {b} rejected',True,rejected))
    return tests,audits,results

if __name__=='__main__':
    out=pathlib.Path(sys.argv[1]); out.mkdir(exist_ok=False)
    tests,audits,results=p0()
    for name,data in [('p0_tests.json',tests),('energy_audit.json',audits),('exact_results.json',results),('oracle_manifest.json',oracle.FIXED)]:
        (out/name).write_text(json.dumps(core.jsonable(data),indent=2)+'\n')
    ok=all(t['status']=='PASS' for t in tests)
    print(json.dumps({'P0':'PASS' if ok else 'FAIL','tests':len(tests),'states':len(audits),'run_dir':str(out)},sort_keys=True),flush=True)
    sys.exit(0 if ok else 1)

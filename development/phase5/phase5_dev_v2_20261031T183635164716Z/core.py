from fractions import Fraction as F
from itertools import product
from dataclasses import dataclass

Q=(0,1,2,3)
MUS=(F(2),F(4),F(0),F(-1,2),F(-1))

def bits(index):
    if not isinstance(index,int) or index<0 or index>=16: raise ValueError('index')
    return tuple((index>>i)&1 for i in range(4))
def display(x):
    if len(x)!=4 or any(v not in (0,1) for v in x): raise ValueError('bits')
    return ''.join(str(v) for v in reversed(x))
def decode(s):
    if not isinstance(s,str) or len(s)!=4 or any(v not in '01' for v in s): raise ValueError('bitstring')
    return tuple(int(v) for v in reversed(s))
def finite_fraction(v):
    try: return F(v)
    except (ValueError,TypeError,OverflowError,ZeroDivisionError) as e: raise ValueError('nonfinite or invalid coefficient') from e

def candidate(mu):
    mu=finite_fraction(mu)
    return tuple(-mu*q+abs(q-1)+F(1,2)*q*q for q in Q)
def direct(mu):
    fs=candidate(mu); m=min(fs)
    return m,tuple(display(tuple(int(i==j) for i in range(4))) for j,v in enumerate(fs) if v==m)

def compile_qubo(mu):
    fs=candidate(mu); a=1+sum(map(abs,fs))
    upper=tuple(tuple((fs[i]-a if i==j else 2*a if i<j else F(0)) for j in range(4)) for i in range(4))
    symmetric=tuple(tuple((fs[i]-a if i==j else a) for j in range(4)) for i in range(4))
    return {'f':fs,'A':a,'upper':upper,'symmetric':symmetric,'constant':a}
def qubo_energy(x,q,symmetric=False):
    matrix=q['symmetric'] if symmetric else q['upper']
    return q['constant']+sum(matrix[i][j]*x[i]*x[j] for i in range(4) for j in range(4))
def ising(q):
    # E(x)=constant+sum_i d_i*x_i+sum_i<j u_ij*x_i*x_j, x_i=(1-Z_i)/2.
    d=[q['upper'][i][i] for i in range(4)]
    u=q['upper']; h=tuple(-d[i]/2-sum(u[min(i,j)][max(i,j)] for j in range(4) if i!=j)/4 for i in range(4))
    J=tuple(tuple(F(0) if i==j else u[min(i,j)][max(i,j)]/4 for j in range(4)) for i in range(4))
    offset=q['constant']+sum(d)/2+sum(u[i][j] for i in range(4) for j in range(i+1,4))/4
    return {'h':h,'J':J,'offset':offset}
def ising_energy(x,ising_coeff):
    z=tuple(1-2*v for v in x)
    return ising_coeff['offset']+sum(ising_coeff['h'][i]*z[i] for i in range(4))+sum(ising_coeff['J'][i][j]*z[i]*z[j] for i in range(4) for j in range(i+1,4))
def enumerate_exact(mu):
    q=compile_qubo(mu); states=[{'index':i,'bits':display(bits(i)),'feasible':sum(bits(i))==1,'energy':qubo_energy(bits(i),q)} for i in range(16)]
    best=min(v['energy'] for v in states); optimal=tuple(v['bits'] for v in states if v['energy']==best)
    return best,optimal,states

def jsonable(obj):
    if isinstance(obj,F):return str(obj)
    if isinstance(obj,tuple):return [jsonable(v) for v in obj]
    if isinstance(obj,list):return [jsonable(v) for v in obj]
    if isinstance(obj,dict):return {k:jsonable(v) for k,v in obj.items()}
    return obj

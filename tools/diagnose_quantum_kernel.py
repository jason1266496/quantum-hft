#!/usr/bin/env python3
"""Phase4A-2 read-only diagnostic entrypoint; no estimator or Qiskit imports."""
import os,sys
from pathlib import Path
for name in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS","NUMEXPR_NUM_THREADS"):os.environ[name]="1"
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.phase4a2.runner import run
if __name__=="__main__":
    if len(sys.argv)!=3 or sys.argv[1]!="--run-id":raise SystemExit("usage: --run-id UTC_RUN_ID")
    print(run(sys.argv[2]))

"""Entrypoint requires the completed fixture gate and immutable lock."""
import sys,os
from pathlib import Path
for key in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS","NUMEXPR_NUM_THREADS"):os.environ[key]="1"
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.phase4b1.runner import run
if __name__=="__main__":
    if len(sys.argv)!=3 or sys.argv[1]!="--run-id":raise SystemExit("usage --run-id UTC_RUN_ID")
    print(run(sys.argv[2]))

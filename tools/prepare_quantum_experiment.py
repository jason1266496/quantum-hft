"""Phase 4A-0 only. No package installation, model fit or quantum execution."""
import argparse,os,sys
from pathlib import Path
for name in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS","NUMEXPR_NUM_THREADS"):os.environ[name]="1"
os.environ["PYTHONDONTWRITEBYTECODE"]="1"
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.quantum_preparation.io import run_path
from experiments.quantum_preparation.runner import execute
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--run-id",required=True)
    args=p.parse_args();return execute(run_path(args.run_id))
if __name__=="__main__":raise SystemExit(main())

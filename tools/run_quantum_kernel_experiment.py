"""Phase4A-1 only. Smoke, fixed Prototype and one determinism repeat."""
import argparse,os,sys
from pathlib import Path
for name in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS","NUMEXPR_NUM_THREADS"):os.environ[name]="1"
os.environ["QISKIT_PARALLEL"]="FALSE";os.environ["PYTHONDONTWRITEBYTECODE"]="1"
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.phase4a1.contracts import run_path
from experiments.phase4a1.runner import execute
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--run-id",required=True)
    return execute(run_path(parser.parse_args().run_id))
if __name__=="__main__":raise SystemExit(main())

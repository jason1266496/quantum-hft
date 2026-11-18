"""Phase 3B build; no Quantum model or trading."""
import argparse,os,sys
from pathlib import Path
for name in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS","NUMEXPR_NUM_THREADS"):os.environ[name]="1"
os.environ["PYTHONDONTWRITEBYTECODE"]="1"
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from experiments.kernel_comparison.freeze import run_path
from experiments.kernel_comparison.rbf_runner import execute
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--run-id",required=True)
    args=p.parse_args()
    return execute("build",run_path(args.run_id))
if __name__=="__main__":raise SystemExit(main())

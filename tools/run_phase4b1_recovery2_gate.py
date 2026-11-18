"""Start only the artificial Gate; environment must already be set by launcher."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.phase4b1_recovery2.harness import run
if __name__=="__main__":
    if len(sys.argv)!=3 or sys.argv[1]!="--run-id":raise SystemExit("usage --run-id UTC_RUN_ID")
    result=run(sys.argv[2]);raise SystemExit(0 if result["status"]=="PASS" else 1)

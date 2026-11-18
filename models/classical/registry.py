"""Exclusive run artifacts; all previous phases and HFT remain outside write scope."""
import csv,hashlib,json,pickle
from pathlib import Path
ROOT=Path("/home/jason/quantum-hft")
def safe_output(path):
    p=Path(path)
    if not p.is_absolute():p=ROOT/p
    if ".." in p.parts or any(x.is_symlink() for x in (p,*p.parents)):raise ValueError("UNSAFE_OUTPUT")
    if p.is_relative_to(ROOT/"artifacts/phase3a/20261026T205307Z") or p==ROOT/"docs/PHASE3A_REPORT_20261026T205307Z.md":
        raise ValueError("OLD_FAIL_WRITE_PROHIBITED")
    if not (p.is_relative_to(ROOT/"artifacts/phase3a") or p.is_relative_to(ROOT/"tests/fixtures/phase3a")
            or (p.parent==ROOT/"docs" and p.name.startswith("PHASE3A_REPORT_"))):
        raise ValueError("OUTPUT_OUTSIDE_PHASE3A")
    return p
def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()
def write_json(path,value):
    p=safe_output(path)
    with p.open("x",encoding="utf-8") as f:json.dump(value,f,sort_keys=True,ensure_ascii=False,allow_nan=False,indent=2);f.write("\n")
    return sha(p)
def write_csv(path,fields,rows):
    p=safe_output(path)
    with p.open("x",encoding="utf-8",newline="") as f:
        writer=csv.writer(f,lineterminator="\n");writer.writerow(fields);writer.writerows(rows)
    return sha(p)
def save_model(path,value):
    p=safe_output(path)
    with p.open("xb") as f:pickle.dump(value,f,protocol=5)
    return {"path":p.name,"sha256":sha(p),"origin":"created in this run; no external pickle loaded",
            "deployment_status":"NOT_APPROVED_FOR_DEPLOYMENT"}

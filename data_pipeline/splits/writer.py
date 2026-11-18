"""Exclusive, path-bounded JSON and metadata index CSV writers."""
import csv,hashlib,json
from pathlib import Path
ROOT=Path("/home/jason/quantum-hft")

def safe_output(path):
    p=Path(path)
    if not p.is_absolute():p=ROOT/p
    if ".." in p.parts or not p.is_relative_to(ROOT):
        raise ValueError("OUTPUT_OUTSIDE_QUANTUM_PROJECT")
    if not (p.is_relative_to(ROOT/"artifacts/phase2e") or
            p.is_relative_to(ROOT/"tests/fixtures/phase2e") or
            (p.parent==ROOT/"docs" and p.name.startswith("PHASE2E_REPORT_"))):
        raise ValueError("OUTPUT_OUTSIDE_PHASE2E_ALLOWLIST")
    if any(x.is_symlink() for x in (p,*p.parents)):
        raise ValueError("SYMLINK_OUTPUT_PROHIBITED")
    return p

def sha_file(path):
    d=hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):d.update(block)
    return d.hexdigest()

def write_json(path,value):
    p=safe_output(path)
    with p.open("x",encoding="utf-8",newline="") as f:
        json.dump(value,f,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)
        f.write("\n")
    return sha_file(p)

def write_csv(path,fields,records):
    p=safe_output(path)
    count=0
    with p.open("x",encoding="utf-8",newline="") as f:
        writer=csv.writer(f,lineterminator="\n");writer.writerow(fields)
        for record in records:
            if len(record)!=len(fields) or any(type(x) is float for x in record):
                raise ValueError("INVALID_INDEX_RECORD")
            writer.writerow(["" if x is None else x for x in record]);count+=1
    return {"sha256":sha_file(p),"row_count":count,"size_bytes":p.stat().st_size}

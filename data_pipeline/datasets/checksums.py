"""Exclusive writes and a tree digest with an explicit normalized-manifest self rule."""
import copy,hashlib,json
from pathlib import Path
ROOT=Path("/home/jason/quantum-hft")
TREE_DEFINITION=("SHA256 of sorted UTF-8 lines '<file_sha256>  <POSIX relative path>\\n'; "
                 "checksums.sha256 excluded; dataset_manifest.json uses canonical JSON with dataset_tree_hash=null")

def safe_output(path):
    path=Path(path)
    if not path.is_absolute():path=ROOT/path
    if ".." in path.parts or not path.is_relative_to(ROOT):raise ValueError("OUTPUT_OUTSIDE_PROJECT")
    if not (path.is_relative_to(ROOT/"artifacts/datasets") or path.is_relative_to(ROOT/"artifacts/phase2f")
            or path.is_relative_to(ROOT/"tests/fixtures/phase2f")
            or (path.parent==ROOT/"docs" and path.name.startswith("PHASE2F_REPORT_"))):
        raise ValueError("OUTPUT_OUTSIDE_PHASE2F")
    if any(p.is_symlink() for p in (path,*path.parents)):raise ValueError("SYMLINK_OUTPUT")
    return path

def sha_file(path):
    p=Path(path)
    if not p.is_file() or p.is_symlink():raise ValueError("NOT_REGULAR_FILE")
    digest=hashlib.sha256()
    with p.open("rb") as handle:
        for block in iter(lambda:handle.read(1024*1024),b""):digest.update(block)
    return digest.hexdigest()

def fingerprint(path):
    p=Path(path)
    if any(x.is_symlink() for x in (p,*p.parents)):raise ValueError("SYMLINK_INPUT")
    return {"sha256":sha_file(p),"size_bytes":p.stat().st_size}

def json_bytes(value):
    return (json.dumps(value,sort_keys=True,ensure_ascii=False,allow_nan=False,indent=2)+"\n").encode("utf-8")

def write_json(path,value):
    p=safe_output(path)
    with p.open("xb") as f:f.write(json_bytes(value))
    return fingerprint(p)

def archive(source,destination):
    source=Path(source);destination=safe_output(destination)
    with source.open("rb") as f,destination.open("xb") as out:
        for block in iter(lambda:f.read(1024*1024),b""):out.write(block)
    if fingerprint(source)!=fingerprint(destination):raise ValueError("ARCHIVE_BYTE_MISMATCH")

def _files(root):
    paths=[]
    for p in Path(root).rglob("*"):
        if p.is_symlink():raise ValueError("SYMLINK_IN_DATASET")
        if p.is_file() and p.name!="checksums.sha256":paths.append(p)
    return sorted(paths,key=lambda p:p.relative_to(root).as_posix())

def _line(digest,name):return digest+"  "+name+"\n"

def tree_hash(root,manifest=None):
    root=Path(root);entries={}
    for p in _files(root):
        name=p.relative_to(root).as_posix()
        if name!="dataset_manifest.json":entries[name]=sha_file(p)
    if manifest is None:manifest=json.loads((root/"dataset_manifest.json").read_text())
    normalized=copy.deepcopy(manifest);normalized["dataset_tree_hash"]=None
    entries["dataset_manifest.json"]=hashlib.sha256(json_bytes(normalized)).hexdigest()
    payload="".join(_line(value,key) for key,value in sorted(entries.items()))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def seal_dataset(root,manifest):
    root=Path(root)
    if (root/"dataset_manifest.json").exists() or (root/"checksums.sha256").exists():
        raise FileExistsError("DATASET_ALREADY_SEALED")
    manifest=copy.deepcopy(manifest)
    manifest["dataset_tree_hash_definition"]=TREE_DEFINITION
    manifest["dataset_tree_hash"]=None
    manifest["dataset_tree_hash"]=tree_hash(root,manifest)
    write_json(root/"dataset_manifest.json",manifest)
    content="".join(_line(sha_file(p),p.relative_to(root).as_posix()) for p in _files(root))
    with safe_output(root/"checksums.sha256").open("x",encoding="utf-8",newline="") as f:f.write(content)
    return manifest["dataset_tree_hash"]

def verify_checksums(root):
    root=Path(root);records={}
    lines=(root/"checksums.sha256").read_text(encoding="utf-8").splitlines()
    previous=""
    for line in lines:
        digest,name=line.split("  ",1)
        if name in records or name<=previous or name=="checksums.sha256" or ".." in Path(name).parts or Path(name).is_absolute():
            raise ValueError("INVALID_CHECKSUM_PATH")
        if len(digest)!=64 or sha_file(root/name)!=digest:raise ValueError("CHECKSUM_MISMATCH")
        records[name]=digest;previous=name
    actual={p.relative_to(root).as_posix() for p in _files(root)}
    if set(records)!=actual:raise ValueError("CHECKSUM_FILESET_MISMATCH")
    manifest=json.loads((root/"dataset_manifest.json").read_text())
    if tree_hash(root)!=manifest["dataset_tree_hash"]:raise ValueError("DATASET_TREE_HASH_MISMATCH")
    return {"status":"PASS","file_count":len(records),"dataset_tree_hash":manifest["dataset_tree_hash"]}

"""Safely inventory ZIP/.wpress and extract only database, package and uploads."""
import pathlib,zipfile,hashlib,json,sys
from extract import ROOT,WORK,file_sha,dump

backup=pathlib.Path(sys.argv[1]).resolve();WORK.mkdir(exist_ok=True)
assert not (WORK/'archive-inventory.json').exists(),'Already unpacked; use a new working folder'
with zipfile.ZipFile(backup) as z:
 entries=z.infolist();assert len(entries)==1 and entries[0].filename.endswith('.wpress'),'Expected one .wpress archive'
 entry=entries[0];assert not entry.flag_bits&1,'Encrypted ZIP'
 name=pathlib.PurePosixPath(entry.filename);assert len(name.parts)==1
 p=WORK/name.name
 with z.open(entry) as src,p.open('wb') as dst:
  while b:=src.read(1024*1024):dst.write(b)
inventory=[];seen=set()
with p.open('rb') as f:
 while True:
  header=f.read(4377)
  if header==bytes(4377):assert not f.read(1),'Trailing bytes';break
  assert len(header)==4377,'Truncated .wpress header'
  name=header[:255].rstrip(b'\0').decode('utf-8');size=int(header[255:269].rstrip(b'\0'));prefix=header[281:].rstrip(b'\0').decode('utf-8')
  rel=pathlib.PurePosixPath(prefix)/name;key=str(rel)
  assert not rel.is_absolute() and '..' not in rel.parts and ':' not in key,'Unsafe archive path'
  assert key not in seen,'Duplicate path';seen.add(key);assert f.tell()+size<=p.stat().st_size,'Truncated archive entry'
  dest=WORK/'extracted'/key if key in ('package.json','database.sql') or key.startswith('uploads/') else None
  if dest:dest.parent.mkdir(parents=True,exist_ok=True)
  out=dest.open('wb') if dest else None;remaining=size;h=hashlib.sha256()
  while remaining:
   b=f.read(min(1024*1024,remaining));assert b;remaining-=len(b);h.update(b)
   if out:out.write(b)
  if out:out.close()
  inventory.append({'path':key,'size':size,'sha256':h.hexdigest(),'extracted':bool(dest)})
(WORK/'archive-inventory.json').write_text(dump(inventory),encoding='utf-8')
(WORK/'backup-location.json').write_text(dump({'path':str(backup),'sha256':file_sha(backup)}),encoding='utf-8')
print(dump({'archive_entries':len(inventory),'zip_crc':'passed','backup_sha256':file_sha(backup)}))

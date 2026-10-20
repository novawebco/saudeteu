"""Verify every exported row against SQLite and re-read title/body from original SQL."""
import collections,csv,json,pathlib,re,sqlite3,sys
from extract import ROOT,WORK,dump,sha,file_sha,SECRET_VALUE,SECRET_KEY,SERIAL_SECRET,backup_path

OUT=ROOT/'export';c=sqlite3.connect(WORK/'source.sqlite')
m=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))
expected={};source_counts=collections.Counter();source_pairs=collections.Counter();errors=[];seen=set();observed={};checks=0;metadata_checks=0;filechecks=0;flags=collections.Counter();source_features=collections.Counter();duplicates={};title_groups=collections.defaultdict(list);slug_groups=collections.defaultdict(list);reference_issues=[]
for (s,) in c.execute('SELECT data FROM source WHERE kind="posts"'):
 d=json.loads(s);expected[d['ID']]={k:v for k,v in d.items() if k not in ('post_content','post_title','post_password')};source_counts[d['post_type']]+=1;source_pairs[(d['post_type'],d['post_status'])]+=1

for batch in m['batches'].values():
 n=0
 for rel in batch['files']:
  with (OUT/rel).open(encoding='utf-8',newline='') as f:
   for line in f:
    r=json.loads(line);pid=r['ID'];assert pid not in seen,('Duplicate ID',pid);seen.add(pid);n+=1
    assert pid in expected,('Unknown ID',pid)
    for k,v in expected[pid].items():assert r[k]==v,('Source field mismatch',pid,k)
    h=(sha(r['post_title']),sha(r['post_content']));observed[pid]=h
    assert h==(r['integrity']['title_sha256'],r['integrity']['content_sha256'])
    source_features[r['post_type']]+=1
    raw_meta=[json.loads(s) for (s,) in c.execute('SELECT data FROM meta WHERE post_id=? ORDER BY json_extract(data,"$.meta_id")',(pid,))]
    clean=[x for x in raw_meta if not (SECRET_KEY.search(x['meta_key'] or '') or SECRET_VALUE.search(x['meta_value'] or '') or SERIAL_SECRET.search(x['meta_value'] or ''))]
    assert clean==r['postmeta'],('Metadata mismatch',pid);metadata_checks+=len(clean)
    raw_rel=[json.loads(s) for (s,) in c.execute('SELECT data FROM relation WHERE post_id=?',(pid,))]
    assert raw_rel==[{k:x[k] for k in ('object_id','term_taxonomy_id','term_order')} for x in r['taxonomy_relationships']],('Relationship mismatch',pid)
    if r['classification'] in ('standard','page','custom'):
     p=OUT/'posts'/str(pid);assert (p/'content.html').read_bytes()==r['post_content'].encode('utf-8'),('Content file mismatch',pid)
     md=json.loads((p/'metadata.json').read_text(encoding='utf-8'));assert md=={k:v for k,v in r.items() if k!='post_content'},('Metadata file mismatch',pid);filechecks+=1
    for ref in r['body_media_references']:
     if ref.get('available'):assert (OUT/ref['local_path']).is_file(),('Missing claimed media',pid,ref['archive_path'])
    for refid in r['featured_image_ids']+r['body_media_ids']:
     try:target=expected.get(int(refid))
     except (TypeError,ValueError):target=None
     if target is None or target['post_type']!='attachment':reference_issues.append({'ID':pid,'referenced_ID':refid,'issue':'media ID does not resolve to an attachment record'})
    if r['post_type']=='post':title_groups[r['post_title']].append(pid);slug_groups[r['post_name']].append(pid)
    if not r['post_title']:flags['empty_title']+=1
    if not r['post_content']:flags['empty_body']+=1;flags['empty_body_'+r['post_type']]+=1
    if r['integrity']['content_utf8_bytes']>100000:flags['unusually_large_body']+=1
    if r['is_autosave']:flags['autosaves']+=1
    checks+=1
 assert n==batch['count'],('Batch count mismatch',batch)
assert set(expected)==seen,'Source/export ID mismatch'
assert dict(source_counts)==m['record_types']==dict(source_features),'Post type count mismatch'
assert source_pairs==collections.Counter({(x['type'],x['status']):x['count'] for x in m['type_status_counts']}),'Type/status mismatch'

# Independent second SQL tokenizer: regex tokens and separate escape decoding.
token=re.compile(r"\s*('(?:\\[\s\S]|''|[^'\\])*'|NULL|-?\d+)\s*([,)])")
escape={'0':'\x00','n':'\n','r':'\r','t':'\t','b':'\b','Z':'\x1a',"'":"'",'"':'"','\\':'\\','%':'\\%','_':'\\_'}
def decode(s):
 if s.startswith("'"):
  return re.sub(r"\\([\s\S])|''",lambda a:escape.get(a[1],a[1]) if a[1] is not None else "'",s[1:-1])
 return None if s=='NULL' else int(s)
prefix='INSERT INTO `'+m['detected_table_prefix']+'posts` VALUES '
independent=set();independent_pairs=collections.Counter();max_body={'ID':None,'bytes':0}
proof=(OUT/'content-integrity.jsonl').open('w',encoding='utf-8',newline='')
with (WORK/'extracted/database.sql').open(encoding='utf-8',errors='strict',newline='') as f:
 for line in f:
  if not line.startswith(prefix):continue
  text=line[len(prefix):];assert text[0]=='(';pos=1;row=[]
  while True:
   hit=token.match(text,pos);assert hit,('Independent tokenization failed',pos)
   row.append(decode(hit[1]));pos=hit.end()
   if hit[2]==')':break
  assert text[pos:].strip()==';' and len(row)==23
  pid=row[0];assert pid not in independent;independent.add(pid)
  ht=sha(row[5]);hb=sha(row[4]);assert (ht,hb)==observed[pid],('SQL title/body mismatch',pid)
  independent_pairs[(row[20],row[7])]+=1
  nb=len(row[4].encode('utf-8'))
  if nb>max_body['bytes']:max_body={'ID':pid,'bytes':nb}
  proof.write(dump({'ID':pid,'title_sha256':ht,'content_sha256':hb,'content_utf8_bytes':nb,'source_sql_match':True})+'\n')
proof.close();assert independent==seen;assert independent_pairs==source_pairs

with (OUT/'posts-index.csv').open(encoding='utf-8',newline='') as f:
 index_ids=set()
 for r in csv.DictReader(f):
  pid=int(r['ID']);assert pid not in index_ids;index_ids.add(pid);assert sha(r['title'])==observed[pid][0]
 assert len(index_ids)==filechecks

media_count=0;media_hash_checks=0
for p in OUT.glob('media-manifest*.jsonl'):
 with p.open(encoding='utf-8') as f:
  for line in f:
   r=json.loads(line)
   if r['kind']=='archive_file':
    media_count+=1
    if r['preserved']:assert file_sha(OUT/r['local_path'])==r['sha256'];media_hash_checks+=1
   else:
    for x in r['files']:
     if x['available']:assert (OUT/x['local_path']).is_file()
assert media_count==m['media']['upload_files'];assert media_hash_checks==m['media']['preserved_files']
with (OUT/'reference-issues.jsonl').open('w',encoding='utf-8',newline='') as f:
 for issue in reference_issues:f.write(dump(issue)+'\n')
for p in OUT.rglob('*.json'):
 json.loads(p.read_text(encoding='utf-8'))
for p in OUT.rglob('*.jsonl'):
 with p.open(encoding='utf-8') as f:
  for line in f:json.loads(line)

# Duplicate titles/slugs remain distinct IDs; list groups without repeating their content.
with (OUT/'duplicate-groups.jsonl').open('w',encoding='utf-8',newline='') as f:
 for field,groups in [('title',title_groups),('slug',slug_groups)]:
  duplicate=[ids for ids in groups.values() if len(ids)>1];duplicates[field]={'groups':len(duplicate),'records':sum(map(len,duplicate))}
  for ids in duplicate:f.write(dump({'field':field,'IDs':ids})+'\n')

files=list(p for p in OUT.rglob('*') if p.is_file());largest=max(files,key=lambda p:p.stat().st_size)
assert largest.stat().st_size<100*1024*1024,'Oversized GitHub file'
assert not m['credential_content_review'],'Content credential review required'
assert file_sha(WORK/'extracted/database.sql')==m['database_sha256']
assert file_sha(backup_path())==m['backup_sha256']
assert file_sha(next(WORK.glob('*.wpress')))==m['archive_sha256']
v={'state':'passed','source_records':len(expected),'exported_records':checks,'unique_ids':len(seen),'independent_sql_title_body_matches':len(independent),'mismatches':0,'per_record_folders_verified':filechecks,'postmeta_rows_verified':metadata_checks,'media_files_hash_verified':media_hash_checks,'source_type_status_counts_match':True,'all_json_parsed':True,'csv_titles_verified':len(index_ids),'backup_and_database_unchanged':True,'duplicates_preserved':duplicates,'unresolved_media_id_references':len(reference_issues),'flags':dict(flags),'largest_body':max_body,'largest_export_file':{'path':largest.relative_to(OUT).as_posix(),'bytes':largest.stat().st_size},'export_data_bytes_before_reports':sum(p.stat().st_size for p in files)}
m['validation']=v;(OUT/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(WORK/'validation-result.json').write_text(dump(v),encoding='utf-8');print(dump(v))

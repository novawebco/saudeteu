"""Streaming, non-executing WordPress SQL preservation exporter (Python stdlib)."""
import argparse, collections, csv, hashlib, html, json, pathlib, re, shutil, sqlite3, sys, urllib.parse, zipfile

ROOT=pathlib.Path(__file__).resolve().parents[1]
WORK=ROOT/'.work'
def dump(v): return json.dumps(v,ensure_ascii=False,separators=(',',':'))
def sha(s): return hashlib.sha256(s.encode('utf-8')).hexdigest()
def file_sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
 return h.hexdigest()

def backup_path():
 location=WORK/'backup-location.json'
 return pathlib.Path(json.loads(location.read_text(encoding='utf-8'))['path']) if location.exists() else pathlib.Path.home()/'Downloads/saudeteu-info-20260226-132638-v43377afhuxl.zip'

def values(text):
 """Parse MySQL VALUES without evaluating SQL or PHP serialization."""
 i=0; n=len(text); rows=[]
 while i<n:
  while i<n and text[i].isspace(): i+=1
  if i==n or text[i]==';': break
  if text[i]==',': i+=1; continue
  assert text[i]=='(', ('Expected row',i); i+=1; row=[]
  while True:
   while text[i].isspace(): i+=1
   if text[i]=="'":
    i+=1; out=[]
    while True:
     c=text[i];i+=1
     if c=='\\':
      c=text[i];i+=1
      out.append({'0':'\0','n':'\n','r':'\r','t':'\t','b':'\b','Z':'\x1a','%':'\\%','_':'\\_'}.get(c,c))
     elif c=="'":
      if i<n and text[i]=="'":out.append("'");i+=1
      else:break
     else:out.append(c)
    row.append(''.join(out))
   else:
    start=i
    while text[i] not in ',)':i+=1
    raw=text[start:i].strip()
    row.append(None if raw.upper()=='NULL' else int(raw) if re.fullmatch(r'-?\d+',raw) else raw)
   while text[i].isspace():i+=1
   if text[i]==')':i+=1;break
   assert text[i]==',';i+=1
  rows.append(row)
 assert text[i:].strip() in ('',';'), 'Unparsed SQL tail'
 return rows

KEEP={'posts','postmeta','terms','term_taxonomy','term_relationships','termmeta','users','options','rank_math_internal_meta','rank_math_redirections'}
SAFE_OPTIONS={'siteurl','home','permalink_structure','category_base','tag_base','timezone_string','gmt_offset','upload_path','upload_url_path','uploads_use_yearmonth_folders','default_category','show_on_front','page_on_front','page_for_posts','blog_charset','blog_public'}
def import_sql():
 db=WORK/'source.sqlite'
 assert not db.exists(), 'SQLite already exists; use export/verify or a new working folder'
 c=sqlite3.connect(db);c.execute('CREATE TABLE source (kind TEXT, id INTEGER, data TEXT)');c.execute('CREATE TABLE meta (post_id INTEGER, data TEXT)');c.execute('CREATE TABLE relation (post_id INTEGER,data TEXT)')
 schemas={};counts=collections.Counter();prefix=None;current=None;line_count=0
 with (WORK/'extracted/database.sql').open(encoding='utf-8',errors='strict',newline='') as f:
  for line in f:
   line_count+=1
   m=re.match(r'CREATE TABLE `([^`]+)`',line)
   if m:current=m[1];schemas[current]=[];continue
   if current and line.startswith('  `'):schemas[current].append(line.split('`')[1]);continue
   m=re.match(r'INSERT INTO `([^`]+)` VALUES ',line)
   if not m:continue
   table=m[1]
   if table.endswith('_posts'):
    candidate=table[:-5]
    assert prefix in (None,candidate),'Multiple post table prefixes';prefix=candidate
   kind=next((k for k in sorted(KEEP,key=len,reverse=True) if table.endswith('_'+k)),None)
   counts[table]+=1
   if not kind:continue
   rows=values(line[m.end():])
   for row in rows:
    assert len(row)==len(schemas[table]),(table,len(row),len(schemas[table]))
    d=dict(zip(schemas[table],row))
    if kind=='users':d={k:d[k] for k in ('ID','display_name','user_nicename')}
    if kind=='options' and d['option_name'] not in SAFE_OPTIONS:continue
    if kind=='posts':c.execute('INSERT INTO source VALUES (?,?,?)',(kind,d['ID'],dump(d)))
    elif kind=='postmeta':c.execute('INSERT INTO meta VALUES (?,?)',(d['post_id'],dump(d)))
    elif kind=='term_relationships':c.execute('INSERT INTO relation VALUES (?,?)',(d['object_id'],dump(d)))
    else:c.execute('INSERT INTO source VALUES (?,?,?)',(kind,row[0],dump(d)))
   if line_count%10000==0:c.commit()
 c.execute('CREATE UNIQUE INDEX post_ids ON source(id) WHERE kind="posts"');c.execute('CREATE INDEX source_kind ON source(kind)');c.execute('CREATE INDEX meta_id ON meta(post_id)');c.execute('CREATE INDEX relation_id ON relation(post_id)');c.commit()
 info={'prefix':prefix,'insert_statement_counts':dict(counts),'schemas':schemas,'sql_sha256':file_sha(WORK/'extracted/database.sql'),'sql_lines':line_count}
 (WORK/'sql-inspection.json').write_text(dump(info),encoding='utf-8')
 types=collections.Counter();statuses=collections.Counter();keys=collections.Counter()
 for (s,) in c.execute('SELECT data FROM source WHERE kind="posts"'):
  d=json.loads(s);types[d['post_type']]+=1;statuses[d['post_status']]+=1
 for (s,) in c.execute('SELECT data FROM meta'):keys[json.loads(s)['meta_key']]+=1
 print(dump({'types':types,'statuses':statuses,'metadata_keys':keys.most_common(90)}))

SECRET_KEY=re.compile(r'(?i)(?:password|passwd|user_pass|activation_key|(?:api|secret|private|access|auth|refresh|consumer)[_-]?(?:key|token|secret)|authorization|credential|client_secret|session_token|^_?application_passwords$)')
SECRET_VALUE=re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|\b(?:AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|sk-[A-Za-z0-9_-]{32,})\b|(?i:bearer\s+[A-Za-z0-9._~-]{20,})|https?://[^\s/:]+:[^\s/@]+@')
SERIAL_SECRET=re.compile(r'(?i)(?:api[_-]?key|secret[_-]?key|access[_-]?token|refresh[_-]?token|client[_-]?secret|password)["\s:;=]+(?:s:\d+:)?["\s]*[^"\s;]{8,}')

def php_value(text):
 """Decode PHP scalar/array serialization by byte lengths; never instantiate objects."""
 b=text.encode('utf-8');i=0
 def read():
  nonlocal i
  t=chr(b[i]);i+=2
  if t=='N':return None
  if t in 'ibd':
   j=b.index(b';',i);v=b[i:j];i=j+1
   return int(v) if t=='i' else bool(int(v)) if t=='b' else float(v)
  if t=='s':
   j=b.index(b':',i);n=int(b[i:j]);i=j+2;v=b[i:i+n].decode('utf-8');i+=n;assert b[i:i+2]==b'";';i+=2;return v
  if t=='a':
   j=b.index(b':',i);n=int(b[i:j]);i=j+2;v={}
   for _ in range(n):k=read();v[k]=read()
   assert b[i:i+1]==b'}';i+=1;return v
  raise ValueError('Unsupported PHP type')
 v=read();assert i==len(b);return v

class JsonLines:
 def __init__(self,path,limit=32*1024*1024):self.path=path;self.limit=limit;self.f=None;self.part=0;self.bytes=0;self.paths=[];self.count=0
 def write(self,v):
  b=(dump(v)+'\n').encode('utf-8')
  if self.f is None or self.bytes+len(b)>self.limit:
   if self.f:self.f.close()
   self.part+=1;p=self.path if self.part==1 else self.path.with_name(self.path.stem+f'.part-{self.part:04}'+self.path.suffix)
   p.parent.mkdir(parents=True,exist_ok=True);self.f=p.open('wb');self.bytes=0;self.paths.append(p.relative_to(ROOT/'export').as_posix())
  assert len(b)<95*1024*1024,'Record exceeds Git file limit'
  self.f.write(b);self.bytes+=len(b);self.count+=1
 def close(self):
  if self.f:self.f.close()

def export():
 out=ROOT/'export';assert not out.exists(),'Export directory already exists'
 out.mkdir();c=sqlite3.connect(WORK/'source.sqlite')
 def source(kind):return (json.loads(s) for (s,) in c.execute('SELECT data FROM source WHERE kind=? ORDER BY id',(kind,)))
 authors={d['ID']:d for d in source('users')};terms={d['term_id']:d for d in source('terms')};tax={d['term_taxonomy_id']:d for d in source('term_taxonomy')}
 options={d['option_name']:d['option_value'] for d in source('options')}
 inventory=json.loads((WORK/'archive-inventory.json').read_text(encoding='utf-8'));uploads={e['path']:e for e in inventory if e['path'].startswith('uploads/')}
 redactions=[];flags=[];counts=collections.Counter();statuses=collections.Counter();pairs=collections.Counter();features=collections.Counter();writers={};media=JsonLines(out/'media-manifest.jsonl');used=set();body_refs=0;body_missing=0;att_available=0;att_missing=0;att_unresolved=0;hashes={};spot=[];sensitive=[]
 def cleaned(d,path):
  if SECRET_KEY.search(d['meta_key'] or '') or SECRET_VALUE.search(d['meta_value'] or '') or SERIAL_SECRET.search(d['meta_value'] or ''):
   redactions.append({'path':path,'meta_id':d.get('meta_id'),'field':d['meta_key'],'reason':'credential-like metadata key or value'});return None
  return d
 def map_path(path):
  path=urllib.parse.unquote(path).replace('\\','/').lstrip('/')
  if not path.startswith('uploads/'):path='uploads/'+path
  if '..' in pathlib.PurePosixPath(path).parts:return {'archive_path':path,'available':False,'reason':'unsafe reference path'}
  e=uploads.get(path)
  if e:
   used.add(path);return {'archive_path':path,'available':True,'local_path':'media/'+path,'size':e['size'],'sha256':e['sha256']}
  return {'archive_path':path,'available':False,'reason':'not present in archive'}
 index=(out/'posts-index.csv').open('w',encoding='utf-8',newline='');cw=csv.writer(index);cw.writerow(['ID','title','slug','type','status','published','published_gmt','modified','modified_gmt','categories','tags','exported_file'])
 for d in source('posts'):
  pid=d['ID'];typ=d['post_type'];counts[typ]+=1;statuses[d['post_status']]+=1;pairs[(typ,d['post_status'])]+=1
  classification='revision' if typ=='revision' else 'attachment' if typ=='attachment' else 'navigation' if typ in ('nav_menu_item','wp_navigation') else 'standard' if typ=='post' else 'page' if typ=='page' else 'custom'
  eligible=classification in ('standard','page','custom')
  autosave=typ=='revision' and bool(re.search(r'\d+-autosave',d['post_name'] or ''))
  meta=[]
  for (s,) in c.execute('SELECT data FROM meta WHERE post_id=? ORDER BY json_extract(data,"$.meta_id")',(pid,)):
   m=cleaned(json.loads(s),f'records/{pid}/postmeta')
   if m is not None:meta.append(m)
  md=collections.defaultdict(list)
  for m in meta:md[m['meta_key']].append(m['meta_value'])
  relationships=[]
  for (s,) in c.execute('SELECT data FROM relation WHERE post_id=?',(pid,)):
   r=json.loads(s);t=tax.get(r['term_taxonomy_id']);relationships.append({**r,'term_taxonomy':t,'term':terms.get(t['term_id']) if t else None})
  cats=[r for r in relationships if r['term_taxonomy'] and r['term_taxonomy']['taxonomy']=='category'];tags=[r for r in relationships if r['term_taxonomy'] and r['term_taxonomy']['taxonomy']=='post_tag']
  protected=bool(d.pop('post_password',None))
  if protected:redactions.append({'path':f'records/{pid}/post_password','reason':'post access password excluded'})
  content=d['post_content'];title=d['post_title'];h={'title_sha256':sha(title),'content_sha256':sha(content),'content_utf8_bytes':len(content.encode('utf-8'))};hashes[pid]=h
  refs=[]
  urls=set(re.findall(r'''(?:https?://|//)[^\s<>"'\[\]]+''',content))
  urls.update(html.unescape(x) for x in re.findall(r'''(?:src|href|poster|data-src)\s*=\s*["']([^"']+)["']''',content,re.I))
  for url in sorted(urls):
   if '/uploads/' in url:
    try: urlpath=urllib.parse.urlsplit(html.unescape(url)).path
    except ValueError: flags.append({'ID':pid,'issue':'unparseable media URL'});continue
    if '/uploads/' not in urlpath:continue
    rel=urlpath.split('/uploads/',1)[1];mapping=map_path(rel);refs.append({'url':url,**mapping});body_refs+=1;body_missing+=not mapping['available']
  image_ids=sorted({int(x) for x in re.findall(r'(?:wp-image-|"(?:id|mediaId)"\s*:\s*)(\d+)',content)})
  rec={**d,'classification':classification,'is_autosave':autosave,'has_post_password':protected,'author':authors.get(d['post_author']),'categories':cats,'tags':tags,'taxonomy_relationships':relationships,'postmeta':meta,'seo_metadata':[m for m in meta if re.search(r'(?i)(yoast|rank_math|aioseo|seopress|_seo|_aioseop)',m['meta_key'] or '')],'featured_image_ids':md.get('_thumbnail_id',[]),'body_media_references':refs,'body_media_ids':image_ids,'integrity':h}
  if eligible:
   rel=f'posts/{pid}';folder=out/rel;folder.mkdir(parents=True)
   (folder/'content.html').write_bytes(content.encode('utf-8'))
   metadata={k:v for k,v in rec.items() if k!='post_content'}
   (folder/'metadata.json').write_text(dump(metadata)+'\n',encoding='utf-8',newline='')
   cw.writerow([pid,title,d['post_name'],typ,d['post_status'],d['post_date'],d['post_date_gmt'],d['post_modified'],d['post_modified_gmt'],dump([r['term'] for r in cats]),dump([r['term'] for r in tags]),rel+'/content.html'])
  target='posts.jsonl' if typ=='post' else 'pages.jsonl' if typ=='page' else f'classified-records/{classification}.jsonl' if not eligible else f'custom-post-types/{urllib.parse.quote(typ,safe="")}.jsonl'
  if target not in writers:writers[target]=JsonLines(out/target)
  writers[target].write(rec)
  if typ=='attachment':
   paths=[]
   for v in md.get('_wp_attached_file',[]):paths.append(map_path(v))
   for v in md.get('_wp_attachment_metadata',[]):
    try:
     parsed=php_value(v)
     if isinstance(parsed,dict):
      base=parsed.get('file','');paths.append(map_path(base)) if base else None
      for size in (parsed.get('sizes') or {}).values():
       if isinstance(size,dict) and size.get('file'):paths.append(map_path(str(pathlib.PurePosixPath(base).parent/size['file'])))
      if parsed.get('original_image'):paths.append(map_path(str(pathlib.PurePosixPath(base).parent/parsed['original_image'])))
    except (ValueError,AssertionError,IndexError,UnicodeError):flags.append({'ID':pid,'issue':'attachment metadata PHP serialization could not be decoded; raw value preserved'})
   if not paths and '/uploads/' in d['guid']:paths.append(map_path(urllib.parse.urlsplit(d['guid']).path.split('/uploads/',1)[1]))
   if paths:
    if any(p['available'] for p in paths):att_available+=1
    else:att_missing+=1
   else:att_unresolved+=1
   media.write({'kind':'attachment','ID':pid,'guid':d['guid'],'title':title,'mime_type':d['post_mime_type'],'files':paths,'has_any_available_file':any(p['available'] for p in paths)})
  if not title:flags.append({'ID':pid,'issue':'empty title','classification':classification})
  if not content:flags.append({'ID':pid,'issue':'empty body','classification':classification})
  if len(content.encode('utf-8'))>100000:flags.append({'ID':pid,'issue':'body over 100000 UTF-8 bytes','bytes':h['content_utf8_bytes']})
  for name,rx in [('Hindi',r'[\u0900-\u097f]'),('Cyrillic',r'[\u0400-\u04ff]'),('emoji',r'[\U0001f300-\U0001faff]'),('HTML',r'<[A-Za-z][^>]*>'),('Gutenberg',r'<!--\s*wp:'),('shortcodes',r'\[[A-Za-z_][^\]\n]*\]'),('replacement_character',r'\ufffd')]:
   if re.search(rx,title+'\n'+content):features[name]+=1
  if SECRET_VALUE.search(title+'\n'+content):sensitive.append({'ID':pid,'field':'title or body','reason':'high confidence credential pattern; needs review'})
  if eligible and (len(spot)<5 or (typ=='page' and not any(x['type']=='page' for x in spot))):spot.append({'ID':pid,'type':typ,'title':title,'content_start':content[:700],'content_end':content[-300:],'bytes':h['content_utf8_bytes']})
 index.close()
 for w in writers.values():w.close()
 # Preserve actual media formats; generated CSS, forms and plugin files remain in the unchanged source backup.
 media_ext={'.jpg','.jpeg','.png','.gif','.webp','.avif','.svg','.pdf','.mp4','.mp3','.wav','.ogg','.mov','.ico','.tif','.tiff','.bmp'}
 preserved=0;media_bytes=0;excluded=0
 for key,e in uploads.items():
  keep=pathlib.PurePosixPath(key).suffix.lower() in media_ext
  if keep:
   dest=out/'media'/key;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(WORK/'extracted'/key,dest);assert file_sha(dest)==e['sha256'];preserved+=1;media_bytes+=e['size']
  else:excluded+=1
  media.write({'kind':'archive_file','archive_path':key,'size':e['size'],'sha256':e['sha256'],'preserved':keep,'local_path':'media/'+key if keep else None,'referenced':key in used,'exclusion_reason':None if keep else 'generated styles, plugin/support or form-related file; retained only in original backup'})
 media.close()
 for kind in ('terms','term_taxonomy','termmeta','rank_math_internal_meta','rank_math_redirections'):
  w=JsonLines(out/'taxonomies'/f'{kind}.jsonl' if kind.startswith('term') else out/'seo'/f'{kind}.jsonl')
  for d in source(kind):
   if kind=='termmeta':d=cleaned(d,'taxonomies/termmeta')
   if d is not None:w.write(d)
  w.close()
 (out/'site-settings.json').write_text(dump(options)+'\n',encoding='utf-8')
 (out/'redactions.json').write_text(dump(redactions)+'\n',encoding='utf-8')
 fw=JsonLines(out/'record-flags.jsonl')
 for v in flags:fw.write(v)
 fw.close()
 (WORK/'readable-spot-checks.json').write_text(json.dumps(spot,ensure_ascii=False,indent=2),encoding='utf-8')
 inspection=json.loads((WORK/'sql-inspection.json').read_text(encoding='utf-8'))
 manifest={'backup_format':'ZIP containing All-in-One WP Migration .wpress (4377-byte headers)','backup_name':'saudeteu-info-20260226-132638-v43377afhuxl.zip','backup_sha256':file_sha(backup_path()),'archive_sha256':file_sha(next(WORK.glob('*.wpress'))),'database_sha256':inspection['sql_sha256'],'detected_table_prefix':inspection['prefix'],'total_records':sum(counts.values()),'record_types':dict(counts),'statuses':dict(statuses),'type_status_counts':[{'type':t,'status':s,'count':n} for (t,s),n in sorted(pairs.items())],'batches':{k:{'count':v.count,'files':v.paths} for k,v in writers.items()},'media':{'upload_files':len(uploads),'preserved_files':preserved,'preserved_bytes':media_bytes,'excluded_support_files':excluded,'attachment_records_with_available_files':att_available,'attachment_records_without_available_files':att_missing,'attachment_records_without_resolvable_path':att_unresolved,'body_upload_references':body_refs,'body_upload_references_missing':body_missing},'source_content_features':dict(features),'redactions':len(redactions),'flags':len(flags),'credential_content_review':sensitive,'batch_limit_bytes':32*1024*1024,'validation':{'state':'pending'},'limitations':['No live-site or remote URL availability checks; backup is authoritative.','Post passwords and credential-like metadata are excluded and paths recorded.','PHP serialized metadata is retained raw; only media mapping decodes supported scalars/arrays.','GUID and permalink settings preserved; current live permalinks not asserted.','Original database prefix before migration placeholder substitution may be unavailable.']}
 (out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(dump({k:manifest[k] for k in ('total_records','record_types','media','redactions','flags','credential_content_review')}))

if __name__=='__main__':
 if len(sys.argv)>1 and sys.argv[1]=='import':import_sql()
 elif len(sys.argv)>1 and sys.argv[1]=='export':export()

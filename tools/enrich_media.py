"""Add explicit external/relative embedded media references without changing content."""
import json,re,html,urllib.parse,collections,pathlib
from extract import ROOT,WORK,dump,JsonLines

out=ROOT/'export';m=json.loads((out/'manifest.json').read_text(encoding='utf-8'));changed=0;external=0;unresolved=0
media_suffix=re.compile(r'\.(?:jpe?g|png|gif|webp|avif|svg|mp[34]|wav|ogg|mov|pdf)(?:[?#]|$)',re.I)
for batch in m['batches'].values():
 for rel in batch['files']:
  p=out/rel;temp=p.with_suffix('.tmp')
  with p.open(encoding='utf-8') as src,temp.open('w',encoding='utf-8',newline='') as dst:
   for line in src:
    r=json.loads(line);body=r['post_content'];refs=r['body_media_references'];known={html.unescape(x['url']) for x in refs};extra=set()
    for attr,value in re.findall(r'''\b(src|poster|data-src|href|srcset|data-srcset)\s*=\s*["']([^"']*)["']''',body,re.I):
     value=html.unescape(value)
     if attr.lower() in ('srcset','data-srcset'):
      extra.update(x.strip().split()[0] for x in value.split(',') if x.strip())
     elif attr.lower()!='href' or media_suffix.search(value):extra.add(value)
    extra.update(re.findall(r'https?://[^\s<>"\[\]]+\.(?:jpg|jpeg|png|gif|webp|mp4|mp3)(?:\?[^\s<>"\[\]]*)?',body,re.I))
    original_ids=r['body_media_ids'];ids=set(original_ids)
    for value in re.findall(r'''\b(?:ids|include)\s*=\s*["']([\d,\s]+)["']''',body):ids.update(map(int,re.findall(r'\d+',value)))
    for value in re.findall(r'"ids"\s*:\s*\[([\d,\s]+)\]',body):ids.update(map(int,re.findall(r'\d+',value)))
    added=0
    for url in sorted(extra-known):
     if not url or url.startswith(('data:','javascript:','#','mailto:')):continue
     try:parsed=urllib.parse.urlsplit(url)
     except ValueError:continue
     path=parsed.path
     if '/uploads/' in path:
      archive_path='uploads/'+urllib.parse.unquote(path.split('/uploads/',1)[1]);local=out/'media'/archive_path
      available=local.is_file() if '..' not in pathlib.PurePosixPath(archive_path).parts else False
      refs.append({'url':url,'archive_path':archive_path,'available':available,'local_path':'media/'+archive_path if available else None,'reason':None if available else 'not present in exported backup media'})
     else:
      is_external=bool(parsed.netloc);external+=is_external;unresolved+=not is_external
      refs.append({'url':url,'available':False,'kind':'external_reference' if is_external else 'relative_reference','reason':'outside backup uploads; no local file availability claimed'})
     added+=1
    r['body_media_ids']=sorted(ids)
    if added or r['body_media_ids']!=original_ids:
     changed+=1
     if r['classification'] in ('standard','page','custom'):(out/'posts'/str(r['ID'])/'metadata.json').write_text(dump({k:v for k,v in r.items() if k!='post_content'})+'\n',encoding='utf-8',newline='')
    dst.write(dump(r)+'\n')
  temp.replace(p)
m['media']['external_embed_references']=external;m['media']['unresolved_relative_embed_references']=unresolved
pkg=json.loads((WORK/'extracted/package.json').read_text(encoding='utf-8'));m['original_table_prefix_from_package']=pkg['Database']['Prefix'];m['limitations']=[x for x in m['limitations'] if 'Original database prefix' not in x]
(out/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(dump({'records_enriched':changed,'external_refs':external,'relative_refs':unresolved}))

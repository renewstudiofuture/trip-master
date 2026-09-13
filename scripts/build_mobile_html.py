#!/usr/bin/env python3
"""Create a standalone mobile itinerary from the card JSON. No dependencies."""
import argparse, html, json, re
from pathlib import Path

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('input_json',type=Path);ap.add_argument('output_html',type=Path);a=ap.parse_args()
 d=json.loads(a.input_json.read_text());pages=d['pages'];ids=[p['id'] for p in pages]
 if len(ids)!=len(set(ids)) or 'overview' not in ids:ap.error('Unique ids and overview page required')
 if any(not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]*',x) for x in ids):ap.error('Invalid page id')
 def esc(s):return html.escape(str(s),quote=True)
 def anchor(target):
  if target not in ids:raise ValueError('Unknown target: '+target)
  return '#'+target
 dates='<a href="#overview">总览</a>'+''.join(f'<a href="{anchor(x["id"])}">{esc(x["label"].split(".")[-1])}</a>' for x in d.get('days',[]))
 panels=[]
 for p in pages:
  section=f'<section class="panel" id="{esc(p["id"])}" aria-labelledby="heading-{esc(p["id"])}">'
  n=next((x['label'].split('.')[-1] for x in d.get('days',[]) if x['id']==p['id']),None)
  section+='<div class="panel-head">'+(f'<span class="day-number" aria-hidden="true">{esc(n)}</span>' if n else '')+f'<div><p class="kicker">{esc(p.get("kicker",""))}</p><h2 id="heading-{p["id"]}">{esc(p["title"])}</h2><p class="route">{esc(p.get("subtitle",""))}</p></div></div>'
  if p['id']=='overview':
   section+='<ol class="overview-list">'
   for i,c in enumerate(p['cards']):
    title=c['title'];match=re.match(r'\d{1,2}\.(\d+)\s+(.*)',title)
    number,name=(match[1],match[2]) if match else (str(i+1).zfill(2),title)
    section+=f'<li><a href="{anchor(c["target"])}"><span class="n">{esc(number)}</span><span class="name">{esc(name)}</span><span class="arrow" aria-hidden="true">↗</span></a></li>'
   section+='</ol>'
  else:
   section+='<div class="action-row"><span>按顺序查看 · 轻点卡片收起</span><button type="button" data-toggle>收起详情</button></div><div class="stops">'
   for c in p.get('cards',[]):
    label=c.get('label','');cls='stop'+(' hotel' if '住宿' in label else '')+(' warn' if c.get('warn') else '')
    section+=f'<details class="{cls}" open><summary><span class="label">{esc(label)}</span><h3>{esc(c["title"])}</h3></summary><p class="body">{esc(c.get("body",""))}</p>'
    if c.get('url'):
     if not c['url'].startswith(('https://','http://')):ap.error('Invalid source URL')
     section+=f'<a class="source-link" href="{esc(c["url"])}" target="_blank" rel="noopener noreferrer">查看来源 ↗</a>'
    section+='</details>'
   section+='</div>'
  if p.get('note'):section+=f'<p class="note">{esc(p["note"])}</p>'
  panels.append(section+'</section>')
 template=(Path(__file__).resolve().parent.parent/'assets/mobile.html').read_text()
 values={'TITLE':d.get('mobile_title',d['title']),'META':d.get('footer',''),'DATES':dates,'PANELS':''.join(panels),'INTRO':d.get('intro','按日期查看路线，按需展开交通与住宿。'),'STATUS':d.get('status','规划版；历史订单与未核实事项以各卡片标记为准。')}
 for key,val in values.items():template=template.replace('__'+key+'__',val if key in ('DATES','PANELS') else esc(val))
 a.output_html.parent.mkdir(parents=True,exist_ok=True);a.output_html.write_text(template);print(a.output_html)
if __name__=='__main__':main()

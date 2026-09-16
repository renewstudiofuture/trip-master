#!/usr/bin/env python3
"""Derive optional PDF cards from the same validated trip.json."""
import argparse,json
from pathlib import Path
from trip_model import load,validate
p=argparse.ArgumentParser(description=__doc__);p.add_argument('trip',type=Path);p.add_argument('output',type=Path);a=p.parse_args();d=load(a.trip);r=validate(d)
if r['errors']:p.exit(1,'\n'.join(r['errors']))
places={x['id']:x for x in d.get('places',[])};bookings={x['id']:x for x in d.get('bookings',[])}
out={'title':d['title'],'days':[],'pages':[{'id':'overview','title':'行程总览','cards':[]}],'footer':'Trip Master · '+str(d['revision'])}
def pages(key,title,cards):
 cards=cards or [{'title':'本次未安排'}]
 for i in range(0,len(cards),2):out['pages'].append({'id':key if i==0 else key+'-'+str(i),'title':title,'cards':cards[i:i+2]})
for day in d.get('days',[]):
 key='day-'+day['id'];label=day.get('date') or '日期未定';out['days'].append({'id':key,'label':label[5:].replace('-','.') if day.get('date') else '待定'})
 out['pages'][0]['cards'].append({'title':label+' '+day['title'],'target':key})
 cards=[]
 for s in day.get('stops',[]):
  place=places.get(s.get('place_id'),{});cards.append({'title':place.get('name',s.get('title','')),'label':s['status'],'body':' '.join(x for x in [(s.get('start') or '')[11:16],s.get('note','')] if x),'url':place.get('url')})
 for bid in day.get('stay_ids',[]):
  b=bookings.get(bid)
  if b:cards.append({'title':b['title'],'label':'住宿 · '+b.get('status','待确认'),'body':b.get('note','')})
 pages(key,day['title'],cards)
for cat,title in [('sights','景点'),('shopping','购物'),('food','餐饮')]:pages(cat,title,[{'title':x['name'],'label':x['status'],'body':'\n'.join(x.get(k,'') for k in ['reason','hours','reservation'] if x.get(k)),'url':x.get('url')} for x in places.values() if x['category']==cat])
pages('tips','贴士',[{'title':x['title'],'body':x.get('note','')} for x in d.get('tasks',[])])
# Split long overview without changing the primary overview anchor.
root=out['pages'][0];cards=root['cards'];root['cards']=cards[:4]
for i in range(4,len(cards),4):out['pages'].insert(1+i//4,{'id':'overview-'+str(i),'title':'行程总览（续）','cards':cards[i:i+4]})
a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8');print(a.output)

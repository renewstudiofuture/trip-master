#!/usr/bin/env python3
"""Build a five-section standalone handbook from validated trip.json."""
import argparse,html,json
from pathlib import Path
from trip_model import ROOT,load,validate,public_data,DIGITS

def esc(v):return html.escape(str(v or ''),quote=True)
def link(url,label):return f'<a href="{esc(url)}" target="_blank" rel="noopener noreferrer">{esc(label)} ↗</a>' if url else ''
def money(n,c):return f'{c} {n/10**DIGITS[c]:.{DIGITS[c]}f}'
def photo_credit(p,illustration=False):
 caption=p.get('image_caption','')
 if illustration:caption=p.get('illustration_caption','AI纸拼贴转绘 · 基于实景照片；非实时风景')
 return '<figcaption><details class="photo-credit"><summary>图片来源</summary><p>'+esc(caption.replace('，未改图','').replace('；未改图',''))+' · '+link(p.get('image_source'),p.get('image_credit') or '来源')+' '+link(p.get('image_license_url'),'许可')+'</p></details></figcaption>'

def build(d):
 report=validate(d)
 if report['errors']:raise ValueError('\n'.join(report['errors']))
 d=public_data(d);places={p['id']:p for p in d['places']};bookings={b['id']:b for b in d['bookings']}
 def place(p):
  photo=''
  if p.get('image_asset') or p.get('image_url'):
   photo=f'<figure><img loading="lazy" src="{esc(p.get("image_asset") or p.get("image_url"))}" alt="{esc(p["name"])}">'+photo_credit(p)+'</figure>'
  if p.get('image_gallery_url') and not photo:photo='<div class="photo-gallery">'+link(p['image_gallery_url'],'查看实景图集')+'<small>'+esc(p.get('image_gallery_note','历史实景，供了解风景'))+'</small></div>'
  highlights=''.join('<li>'+esc(x)+'</li>' for x in p.get('highlights',[]))
  visit='<p class="visit-plan"><b>建议怎么玩</b><br>'+esc(p.get('visit_plan'))+'</p>' if p.get('visit_plan') else ''
  return f'<article class="place" id="place-{esc(p["id"])}">{photo}<h3>{esc(p["name"])}</h3><p>{esc(p.get("reason"))}</p>'+('<ul class="highlights">'+highlights+'</ul>' if highlights else '')+visit+'<details><summary>到访信息与来源</summary>'+''.join(f'<p>{esc(p.get(k))}</p>' for k in ('address','hours','reservation','price_note') if p.get(k))+f'<div class="actions">{link(p.get("map_url"),"地图")}{link(p.get("url"),"资料来源")}</div></details></article>'
 intro='<p class="intro">'+esc(d.get('introduction'))+'</p>' if d.get('introduction') else ''
 body=intro+'<div id="budget-overview" class="budget-overview" aria-live="polite"></div><section id="itinerary" class="module"><h2>行程</h2><p class="schedule-note">时刻按攻略所在地时区显示；标注“建议”的时段可调整，含必要休息与转场缓冲，不代表班次或营业时间。</p><p id="today" class="notice" aria-live="polite"></p><div class="days">'+''.join(f'<a href="#day-{esc(x["id"])}">{esc(x.get("date") or "第"+str(i+1)+"天")}</a>' for i,x in enumerate(d['days']))+'</div>'
 if report['warnings']:body+='<details class="warnings"><summary>待确认事项 · '+str(len(report['warnings']))+'</summary><ul>'+''.join('<li>'+esc(w)+'</li>' for w in report['warnings'])+'</ul></details>'
 for i,x in enumerate(d['days']):
  body+=f'<article class="day" id="day-{esc(x["id"])}"><header><span class="number">{i+1:02}</span><div><p class="tag">{esc(x.get("date") or "日期未定")}</p><h3>{esc(x.get("title"))}</h3></div></header><ol class="route">'
  for s in x.get('stops',[]):
   p=places.get(s.get('place_id'),{});name=s.get('title') or p.get('name','')
   timing=s.get('time_label') or ((s.get('start') or '')[11:16]) or '时间待安排'
   body+=f'<li id="stop-{esc(s["id"])}" data-stop-id="{esc(s["id"])}"><p class="stop-time">{esc(timing)}</p><h4>{esc(name)}</h4><p>{esc(s.get("note"))}</p><div class="actions">'
   if p.get('category') in ('sights','shopping','food'):body+=f'<a href="#place-{esc(p["id"])}">看景点介绍</a>'
   body+=f'{link(p.get("map_url"),"导航")}{link(p.get("url"),"预约／来源")}'
   if p.get('address'):body+=f'<button type="button" data-copy-address="{esc(p["address"])}">复制地址</button>'
   body+='</div></li>'
  body+='</ol>'
  for bid in x.get('stay_ids',[]):
   b=bookings.get(bid)
   if b:body+=f'<p class="stay">住宿 · {esc(b["title"])}<br>{esc(b.get("check_in"))} → {esc(b.get("check_out"))} · {esc(b.get("status"))}<br>{esc(b.get("note"))}</p>'
  if x.get('note'):body+='<p class="notice day-note">'+esc(x['note'])+'</p>'
  body+='</article>'
 if not d['days']:body+='<p>日期或天数确定后补充逐日安排。</p>'
 body+='<details><summary>规划预算与已提供费用</summary>'
 if d.get('budget'):
  b=d['budget'];body+='<p>'+money(b['amount_minor'],b['currency'])+('／人' if b['scope']=='per_person' else '／全程')+'</p>'
 totals={}
 for c in d['costs']:
  cur=c['currency'];bucket=totals.setdefault(cur,[0,0,0]);bucket[1]+=c.get('paid_minor',0)
  if c.get('amount_minor') is None:bucket[2]+=1
  else:bucket[0]+=c['amount_minor']
  body+='<p>'+esc(c['title'])+' · '+(money(c['amount_minor'],cur) if c.get('amount_minor') is not None else '待确认')+' · '+esc(c['basis'])+'</p>'
 for cur,(total,paid,unknown) in totals.items():
  body+='<p>已知费用合计 '+money(total,cur)+' · 已提供付款 '+money(paid,cur)+(' · 另有 '+str(unknown)+' 项总额待确认，暂不计算剩余应付' if unknown else ' · 剩余规划金额 '+money(total-paid,cur)+'（可能含估算）')+'</p>'
 body+='<p class="notice">规划费用不会自动计入账本。</p></details></section>'
 for cat,title,empty in [('sights','景点','暂无额外景点'),('shopping','购物','本次未安排购物'),('food','餐饮','具体餐厅待补充')]:
  arr=[p for p in d['places'] if p['category']==cat]
  body+=f'<section id="{cat}" class="module"><h2>{title}</h2><div class="grid">'+(''.join(place(p) for p in arr) or '<p>'+empty+'</p>')+'</div></section>'
 body+='<section id="tips" class="module"><h2>贴士</h2><p class="notice">勾选仅表示个人已处理，不代表商家确认。</p>'
 for t in d['tasks']:
  body+=f'<label class="task"><input type="checkbox" data-task="{esc(t["id"])}"><span>{esc(t.get("priority","建议"))} · {esc(t["title"])}<small>{esc(t.get("note"))}</small></span></label>'
 body+='<details><summary>来源与核实日期</summary>'
 for e in d['evidence']:body+='<p>'+link(e.get('url'),e.get('title','来源'))+esc(('' if e.get('url') else e.get('title',''))+' · '+e.get('checked_at',''))+'</p><small>'+esc(e.get('note',''))+'</small>'
 body+='</details></section>'
 guidance={'review':'下一步：浏览新版行程，试改一个活动、记一笔账。满意或想修改，都发回生成攻略的聊天。','published':'下一步：用下方分享按钮发给同行朋友。个人调整与账本只保存在本浏览器，分享链接不会同步它们。','accepted':'已验收。需要公开分享时，回到生成攻略的聊天发送“免费发布”。'}
 stage=d.get('delivery_stage','review');body='<aside class="notice next-step">'+esc(guidance.get(stage,guidance['review']))+'</aside>'+body
 template=(ROOT/'assets/mobile.html').read_text(encoding='utf-8')
 payload=json.dumps(d,ensure_ascii=False).replace('<','\\u003c').replace('&','\\u0026')
 hero_place=next((p for p in d['places'] if p.get('image_asset') or p.get('image_url')),None)
 hero_image=''
 if hero_place:
  hero_image=f'<figure class="hero-photo"><img class="hero-real" src="{esc(hero_place.get("image_asset") or hero_place.get("image_url"))}" alt="{esc(hero_place["name"])}">'
  if hero_place.get('illustration_asset'):
   hero_image+=f'<img class="hero-art" src="{esc(hero_place["illustration_asset"])}" alt="{esc(hero_place["name"])}的纸拼贴艺术转绘">'
  hero_image+='<div class="hero-real-credit">'+photo_credit(hero_place)+'</div>'
  if hero_place.get('illustration_asset'):hero_image+='<div class="hero-art-credit">'+photo_credit(hero_place,True)+'</div>'
  hero_image+='</figure>'
 dates=[x['date'] for x in d['days'] if x.get('date')]
 period=(dates[0][5:].replace('-','.')+' — '+dates[-1][5:].replace('-','.')) if dates else '日期待定'
 cover_title='<h1>'+esc(d.get('cover_title') or d['title'])+'</h1>'
 if d.get('cover_subtitle'):cover_title+='<p class="cover-subtitle">'+esc(d['cover_subtitle'])+'</p>'
 cover_title+='<div class="cover-info"><span class="cover-dates">'+esc(period)+'</span><span class="cover-count">'+esc(str(len(d['days']))+' DAYS / '+str(d['travelers'])+' 人' if d.get('travelers') else str(len(d['days']))+' DAYS')+'</span></div>'
 values={'COVER_TITLE':cover_title,'HERO_IMAGE':hero_image,'TITLE':esc(d['title']),'META':'Trip Master · 版本 '+str(d['revision']),'BODY':body,'DATA':payload,'CSS':(ROOT/'assets/mobile.css').read_text(),'JS':(ROOT/'assets/mobile.js').read_text()}
 # One pass: user-authored strings cannot become template instructions.
 import re
 return re.sub(r'__(TITLE|META|BODY|DATA|CSS|JS|HERO_IMAGE|COVER_TITLE)__',lambda m:values[m[1]],template)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('trip',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
 try:
  data=load(a.trip);result=build(data);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(result,encoding='utf-8')
  import shutil
  for place in data.get('places',[]):
   for key in ('image_asset','illustration_asset'):
    if place.get(key):
     src=a.trip.parent/place[key];dst=a.output.parent/place[key]
     if not src.is_file():raise ValueError('图片文件不存在: '+str(src))
     dst.parent.mkdir(parents=True,exist_ok=True)
     if src.resolve()!=dst.resolve():shutil.copy2(src,dst)
  print(a.output)
 except (ValueError,TypeError,KeyError,OSError) as e:p.exit(1,str(e)+'\n')
if __name__=='__main__':main()

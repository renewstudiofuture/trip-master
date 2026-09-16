#!/usr/bin/env python3
"""Unified trip validation and scoped change requests. Standard library only."""
import argparse,json,re
from pathlib import Path
from datetime import date,datetime,timedelta
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo
ROOT=Path(__file__).resolve().parent.parent
DIGITS={'CNY':2,'USD':2,'EUR':2,'GBP':2,'HKD':2,'TWD':2,'SGD':2,'THB':2,'JPY':0,'KRW':0}
STATUS={'用户提供','截图可辨识','公开核实','估算','待确认'}
def load(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def url(v):
 if not v:return True
 try:
  u=urlsplit(v);return u.scheme in ('http','https') and bool(u.netloc) and not u.username and not u.password
 except (TypeError,ValueError):return False
def validate(d):
 e=[];w=[]
 if not isinstance(d,dict):return {'errors':['根数据须为对象'],'warnings':[]}
 def ident(v):return isinstance(v,str) and re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{0,79}',v)
 def items(key):
  arr=d.get(key,[])
  if not isinstance(arr,list) or any(not isinstance(x,dict) for x in arr):e.append(key+' 须为对象数组');return []
  seen=set()
  for x in arr:
   k=x.get('id')
   if not ident(k) or k in seen:e.append(key+' ID无效或重复: '+str(k))
   if isinstance(k,str):seen.add(k)
  return arr
 def dt(v,label,timestamp=False):
  if v is None:return None
  try:
   t=datetime.fromisoformat(v) if timestamp else date.fromisoformat(v)
   if timestamp and t.tzinfo is None:raise ValueError()
   return t
  except (ValueError,TypeError):e.append(label+' 日期/时间无效，时间须含日期和UTC偏移');return None
 if d.get('schema_version')!=2:e.append('schema_version须为2')
 if not ident(d.get('trip_id')):e.append('trip_id无效')
 if type(d.get('revision')) is not int or d['revision']<1:e.append('revision须为正整数')
 if not d.get('title'):e.append('缺少title')
 try:ZoneInfo(d.get('timezone',''))
 except Exception:e.append('timezone无效')
 people=d.get('travelers')
 if people is not None and (type(people) is not int or people<1):e.append('人数须为正整数或null')
 places=items('places');days=items('days');bookings=items('bookings');costs=items('costs');tasks=items('tasks');sources=items('evidence')
 if e:return {'errors':e,'warnings':w}
 pp={x['id']:x for x in places};bb={x['id']:x for x in bookings};ee={x['id'] for x in sources}
 for x in sources:
  if not url(x.get('url')):e.append('来源URL无效: '+x['id'])
  if x.get('status') not in STATUS:e.append('来源状态无效: '+x['id'])
 for x in places:
  if not x.get('name') or x.get('category') not in ('sights','shopping','food','other'):e.append('地点名称或分类无效: '+x['id'])
  if x.get('status') not in STATUS:e.append('地点状态无效: '+x['id'])
  for k in ('url','map_url','image_url','image_source','image_license_url','image_gallery_url','rating_source'):
   if not url(x.get(k)):e.append('链接无效: '+x['id']+'/'+k)
  if x.get('image_asset') and not re.fullmatch(r'assets/[A-Za-z0-9_-]+\.(?:jpg|jpeg|png|webp)',x['image_asset']):e.append('本地图片路径无效: '+x['id'])
  if (x.get('image_url') or x.get('image_asset')) and not x.get('image_source'):e.append('图片缺少来源: '+x['id'])
  if x.get('illustration_asset') and (not isinstance(x['illustration_asset'],str) or not re.fullmatch(r'assets/[A-Za-z0-9_-]+\.(?:jpg|jpeg|png|webp)',x['illustration_asset']) or not x.get('image_source')):e.append('插画路径或来源无效: '+x['id'])
  if x.get('rating') is not None and not x.get('rating_source'):e.append('评分缺少来源: '+x['id'])
  lat,lon=x.get('lat'),x.get('lon')
  if (lat is None)!=(lon is None):e.append('坐标须成对: '+x['id'])
  elif lat is not None:
   if not(type(lat) in (float,int) and type(lon) in (float,int) and -90<=lat<=90 and -180<=lon<=180):e.append('坐标越界: '+x['id'])
   if x.get('coordinate_system') not in ('WGS84','GCJ02','BD09'):e.append('须注明坐标系: '+x['id'])
  if any(ref not in ee for ref in x.get('evidence_ids',[])):e.append('地点引用未知来源: '+x['id'])
  if x.get('status')=='公开核实' and not x.get('evidence_ids'):e.append('公开核实地点缺少证据引用: '+x['id'])
  if x.get('status')=='待确认':w.append('地点待确认: '+x['name'])
 seen=set();placements={};dates=[];intervals=[]
 for day in days:
  dd=dt(day.get('date'),day['id']);dates.append(dd)
  stops=day.get('stops',[])
  if not isinstance(stops,list) or any(not isinstance(s,dict) for s in stops):e.append('stops须为对象数组');continue
  for s in stops:
   sid=s.get('id')
   if not ident(sid) or sid in seen:e.append('活动ID无效或重复');continue
   seen.add(sid)
   if s.get('place_id') and s['place_id'] not in pp:e.append('未知地点: '+sid)
   if not s.get('place_id') and not s.get('title'):e.append('活动缺名称: '+sid)
   if s.get('status') not in STATUS:e.append('活动状态无效: '+sid)
   if 'time_label' in s and (not isinstance(s['time_label'],str) or len(s['time_label'])>100):e.append('时间说明无效: '+sid)
   bid=s.get('booking_id')
   if bid:
    b=bb.get(bid)
    if not b or b.get('cancelled'):e.append('无效预订引用: '+sid)
    else:
     placements[bid]=placements.get(bid,0)+1
     if b.get('date') and b['date']!=day.get('date'):e.append('预订日期冲突: '+bid)
   a,z=dt(s.get('start'),sid,True),dt(s.get('end'),sid,True)
   if a and z and z<=a:e.append('结束须晚于开始: '+sid)
   if a and dd and a.date()!=dd:e.append('活动日期不符: '+sid)
   gap=s.get('transfer_minutes')
   if gap is not None and (type(gap) is not int or gap<0):e.append('转场分钟无效: '+sid)
   intervals.append((a,z,gap,sid))
  for bid in day.get('stay_ids',[]):
   b=bb.get(bid)
   if not b or b.get('cancelled') or b.get('kind')!='stay':e.append('无效住宿引用');continue
   ci,co=dt(b.get('check_in'),bid),dt(b.get('check_out'),bid)
   if dd and ci and co and not ci<=dd<co:e.append('住宿不覆盖该晚: '+day['id'])
 known=[x for x in dates if x]
 if known!=sorted(known) or len(known)!=len(set(known)):e.append('日期重复或未排序')
 if not days or len(known)!=len(days):w.append('日期或天数待确认，尚不能核实定日预约')
 for (_,end,_,sid),(start,_,gap,nid) in zip(intervals,intervals[1:]):
  if start and end:
   if start<end:e.append('时间重叠: '+nid)
   elif type(gap) is int and start<end+timedelta(minutes=gap):e.append('转场时间不足: '+nid)
   elif gap is None:w.append('部分转场时间待确认，未完成衔接校验')
  else:w.append('部分活动时间缺失，衔接尚未完整校验')
 for day in days[:-1]:
  if not day.get('stay_ids'):w.append('该晚住宿或夜间交通待确认: '+day['id'])
 for b in bookings:
  if b.get('cancelled'):continue
  if b.get('status') not in ('用户提供','截图可辨识','待确认'):e.append('预订来源状态无效: '+b['id'])
  if b.get('kind')=='stay':
   ci,co=dt(b.get('check_in'),b['id']),dt(b.get('check_out'),b['id'])
   if ci and co and co<=ci:e.append('入住退房顺序错误')
   cap=b.get('capacity_total')
   if cap is not None and (type(cap) is not int or cap<1):e.append('住宿容量无效')
   elif cap and people and cap<people:e.append('住宿容量不足')
   elif cap is None:w.append('住宿容量待确认: '+b.get('title',b['id']))
  elif b.get('date'):
   dt(b['date'],b['id'])
   if placements.get(b['id'],0)!=1:e.append('有效定日预订须安排一次: '+b['id'])
 charged=set()
 for c in costs:
  amount,paid=c.get('amount_minor'),c.get('paid_minor',0)
  if c.get('currency') not in DIGITS:e.append('不支持的费用币种')
  if amount is not None and (type(amount) is not int or amount<0):e.append('金额须为非负整数最小单位')
  if type(paid) is not int or paid<0 or(type(amount) is int and paid>amount):e.append('已付金额错误')
  if c.get('basis') not in ('用户提供','报价','估算'):e.append('缺少费用性质')
  bid=c.get('booking_id')
  if bid:
   if bid not in bb or bb[bid].get('cancelled'):e.append('费用引用无效预订')
   if bid in charged:e.append('同一预订重复计费')
   charged.add(bid)
 b=d.get('budget')
 if b is not None and (not isinstance(b,dict) or b.get('currency') not in DIGITS or type(b.get('amount_minor')) is not int or b['amount_minor']<0 or b.get('scope') not in ('total','per_person')):e.append('预算须含币种、整数金额和total/per_person范围')
 return {'errors':e,'warnings':list(dict.fromkeys(w))}
def request_scope(d,r):
 if r.get('trip_id')!=d['trip_id'] or r.get('base_revision')!=d['revision']:raise ValueError('申请行程或版本不符，不能自动覆盖')
 days={x['id']:x for x in d['days']};affected=set();semantic=False
 for op in r.get('operations',[]):
  day=days.get(op.get('day_id'));kind=op.get('type')
  if not day or kind not in ('add','remove','move','note'):raise ValueError('未知日期或操作')
  affected.add(day['id'])
  if kind=='note':semantic=True
  if kind in ('remove','move'):
   s=next((s for s in day['stops'] if s['id']==op.get('stop_id')),None)
   if not s:raise ValueError('未知活动')
   if s.get('locked') or s.get('booking_id'):raise ValueError('涉及锁定项目，需明确变更授权后由Agent更新源数据')
  if kind=='move':
   if op.get('target_day_id') not in days:raise ValueError('未知目标日期')
   affected.add(op['target_day_id'])
 neighbors=set(affected)
 for i,x in enumerate(d['days']):
  if x['id'] in affected:neighbors.update(z['id'] for z in d['days'][max(0,i-1):i+2])
 return {'affected_days':sorted(affected),'check_connections':sorted(neighbors),'needs_semantic_review':semantic,'note':'只复核受影响衔接；自由意见先判断是否需要扩大范围。'}
def public_data(d):
 def pick(x,keys):return {k:x[k] for k in keys.split() if k in x}
 out=pick(d,'schema_version trip_id revision title timezone travelers budget introduction delivery_stage cover_title cover_subtitle');out['currency_digits']=DIGITS
 out['places']=[pick(x,'id name category reason address hours reservation price_note lat lon coordinate_system map_url url image_url image_source image_asset image_caption image_credit image_license_url image_gallery_url image_gallery_note illustration_asset illustration_caption highlights visit_plan rating rating_source status evidence_ids') for x in d.get('places',[])]
 out['days']=[dict(pick(x,'id date title note stay_ids'),stops=[pick(s,'id place_id title start end time_label transfer_minutes note status locked booking_id') for s in x.get('stops',[])]) for x in d.get('days',[])]
 out['bookings']=[pick(x,'id title kind date check_in check_out note status') for x in d.get('bookings',[]) if not x.get('cancelled')]
 out['costs']=[pick(x,'id title amount_minor paid_minor currency basis') for x in d.get('costs',[])]
 out['tasks']=[pick(x,'id title note priority') for x in d.get('tasks',[])]
 out['evidence']=[pick(x,'id title url status checked_at applicable note') for x in d.get('evidence',[])]
 return out
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['validate','request']);p.add_argument('trip',type=Path);p.add_argument('request',nargs='?',type=Path);a=p.parse_args()
 try:
  d=load(a.trip);r=validate(d)
  if a.command=='request' and not r['errors']:
   if not a.request:p.error('缺少申请文件')
   r=request_scope(d,load(a.request))
  print(json.dumps(r,ensure_ascii=False,indent=2));return int(bool(r.get('errors')))
 except (ValueError,TypeError,KeyError,OSError) as e:print('数据错误: '+str(e));return 1
if __name__=='__main__':raise SystemExit(main())

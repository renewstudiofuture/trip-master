#!/usr/bin/env python3
"""Render a concise trip JSON to a phone-friendly PDF; no browser required.
See references/pdf-design.md for the schema and editorial requirements.
"""
import argparse, html, json
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph

W,H=420,740
P={'ink':'#171717','muted':'#55544e','lake':'#164bb8','blue':'#2155CD','bg':'#f7f6f2','white':'#FFFFFF','line':'#cccac4','amber':'#171717','sand':'#f2ce35'}

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('input_json',type=Path);ap.add_argument('output_pdf',type=Path)
 ap.add_argument('--font',type=Path);ap.add_argument('--font-index',type=int,default=0)
 a=ap.parse_args();d=json.loads(a.input_json.read_text())
 candidates=[a.font] if a.font else [Path('/System/Library/Fonts/Supplemental/Arial Unicode.ttf'),Path('/usr/share/fonts/truetype/arphic/uming.ttc'),Path('C:/Windows/Fonts/msyh.ttc')]
 for f in candidates:
  if f and f.is_file():
   try:pdfmetrics.registerFont(TTFont('Body',str(f),subfontIndex=a.font_index));break
   except Exception:continue
 else:ap.error('Supply an embeddable Chinese TrueType font with --font.')
 utility=f.parent/'Arial Narrow.ttf'
 if utility.is_file():pdfmetrics.registerFont(TTFont('Utility',str(utility)))
 else:pdfmetrics.registerFont(TTFont('Utility',str(f),subfontIndex=a.font_index))
 pages=d['pages'];ids=[p['id'] for p in pages]
 if len(ids)!=len(set(ids)):ap.error('Page ids must be unique.')
 if 'overview' not in ids:ap.error('An overview page is required.')
 for ref in d.get('days',[]):
  if ref['id'] not in ids:ap.error('Unknown day navigation target: '+ref['id'])
 for page in pages:
  for item in page.get('cards',[]):
   if item.get('target') and item['target'] not in ids:ap.error('Unknown card target: '+item['target'])
 chars=set(''.join(str(x) for x in [d]))
 missing=[x for x in chars if ord(x)>127 and ord(x) not in pdfmetrics.getFont('Body').face.charToGlyph]
 if missing:ap.error('Font missing glyphs: '+''.join(sorted(missing)))
 a.output_pdf.parent.mkdir(parents=True,exist_ok=True)
 c=canvas.Canvas(str(a.output_pdf),pagesize=(W,H));c.setTitle(d['title']);c.setAuthor('旅行安排')
 def rect(x,y,w,h,color,r=0):
  c.setFillColor(HexColor(P.get(color,color)));c.roundRect(x,H-y-h,w,h,r,fill=1,stroke=0)
 def txt(s,x,y,w,size=11,color='ink',font='Body'):
  style=ParagraphStyle('t',fontName=font,fontSize=size,leading=size*1.5,textColor=HexColor(P[color]),wordWrap='CJK')
  p=Paragraph(html.escape(str(s)).replace('\n','<br/>'),style);_,h=p.wrap(w,H)
  if y+h>(H-10 if y>=H-30 else H-34):raise ValueError(f'Text overflow: {s[:50]}')
  p.drawOn(c,x,H-y-h);return h
 def link(url,x,y,w,h):
  if not url.startswith(('https://','http://')):raise ValueError('Only HTTP(S) source links supported')
  c.linkURL(url,(x,H-y-h,x+w,H-y),relative=0,thickness=0)
 def card(item,y,spine=False):
  x=58 if spine else 24;w=W-24-x
  label=item.get('label','');title=item['title'];body=item.get('body','')
  def ht(s,size):
   p=Paragraph(html.escape(s).replace('\n','<br/>'),ParagraphStyle('m',fontName='Body',fontSize=size,leading=size*1.5,wordWrap='CJK'));return p.wrap(w-28,H)[1]
  hh=ht(title,15)+ht(body,11)+(20 if label else 0)+28
  if y+hh>H-45:raise ValueError('Card exceeds page: '+title+'; split content into another page.')
  rect(x,y,w,hh,'sand' if item.get('warn') else 'white')
  yy=y+12
  if label:txt(label,x+14,yy,w-28,9,'amber' if item.get('warn') else 'lake');yy+=20
  yy+=txt(title,x+14,yy,w-28,15)+3
  if body:txt(body,x+14,yy,w-28,11,'muted')
  if item.get('url'):link(item['url'],x,y,w,hh)
  if item.get('target'):c.linkRect('',item['target'],(x,H-y-hh,x+w,H-y),relative=0,thickness=0)
  if spine:
   c.setFillColor(HexColor(P['lake']));c.circle(38,H-y-21,4,fill=1,stroke=0)
  return y+hh+10
 for i,p in enumerate(pages):
  rect(0,0,W,H,'bg',0);c.bookmarkPage(p['id']);c.addOutlineEntry(p['title'],p['id'],0)
  txt(d.get('eyebrow','旅行随身册'),24,17,290,9,'muted')
  txt(f'{i+1:02d} / {len(pages):02d}',347,17,60,9,'muted','Utility')
  txt(p.get('kicker',''),24,48,370,10,'lake')
  y=69+txt(p['title'],24,69,372,26)
  if p.get('subtitle'):y+=5+txt(p['subtitle'],24,y+5,372,11,'muted')
  y+=19
  if p.get('day'):
   for n,day in enumerate(d.get('days',[])):
    x=24+(n%7)*53;ny=y+(n//7)*34;active=day['id']==p['id'];rect(x,ny,47,27,'lake' if active else 'white',0)
    txt(day['label'],x+6,ny+6,37,9,'white' if active else 'muted')
    c.linkRect('',day['id'],(x,H-ny-27,x+47,H-ny),relative=0,thickness=0)
   y+=34*((len(d.get('days',[]))+6)//7)+8
  if p.get('spine'):
   c.setStrokeColor(HexColor(P['line']));c.setLineWidth(2);c.line(38,H-y-21,38,100)
  for item in p.get('cards',[]):y=card(item,y,p.get('spine',False))
  if p.get('note'):txt(p['note'],24,y+2,372,10,'muted')
  txt(d.get('footer',d['title']),24,H-26,315,8,'muted')
  txt('总览',364,H-27,32,9,'lake');c.linkRect('','overview',(360,12,400,33),relative=0,thickness=0)
  c.showPage()
 c.save();print(f'{len(pages)} pages: {a.output_pdf}')
if __name__=='__main__':main()

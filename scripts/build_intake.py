#!/usr/bin/env python3
"""Copy standalone five-item questionnaire, optionally prefilling known brief fields."""
import argparse,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('output',type=Path);p.add_argument('--brief',type=Path);a=p.parse_args()
s=(Path(__file__).resolve().parent.parent/'assets/questionnaire.html').read_text(encoding='utf-8')
if a.brief:
 d=json.loads(a.brief.read_text(encoding='utf-8'));allowed='destination origin start_date end_date budget budget_scope currency preferences note'.split();d={k:d[k] for k in allowed if k in d};payload=json.dumps(d,ensure_ascii=False).replace('<','\\u003c');s=s.replace('id="prefill" type="application/json">{}','id="prefill" type="application/json">'+payload)
a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(s,encoding='utf-8');print(a.output)

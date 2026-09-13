#!/usr/bin/env python3
"""Render a small, documented Markdown subset to Chinese-capable A4 PDF.

Dependency: reportlab. No browser, network requests, or global settings changes.
"""
import argparse
import html
import re
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input_md', type=Path)
    parser.add_argument('output_pdf', type=Path)
    parser.add_argument('--title', default='旅行攻略')
    parser.add_argument('--font', type=Path)
    parser.add_argument('--font-index', type=int, default=0)
    args = parser.parse_args()
    try:
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.colors import HexColor, white
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
    except ImportError:
        parser.error('缺少reportlab。请使用包含该依赖的Python运行时。')
    fonts = [args.font] if args.font else [
        Path('/System/Library/Fonts/Supplemental/Arial Unicode.ttf'),
        Path('/usr/share/fonts/truetype/arphic/uming.ttc'),
        Path('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'),
        Path('C:/Windows/Fonts/msyh.ttc'),
    ]
    errors = []
    for font in fonts:
        if not font.is_file():
            continue
        try:
            pdfmetrics.registerFont(TTFont('CJK', str(font), subfontIndex=args.font_index))
            if ord('旅') not in pdfmetrics.getFont('CJK').face.charToGlyph:
                raise ValueError('字体不含所需中文字符')
            break
        except Exception as exc:
            errors.append(f'{font}: {exc}')
    else:
        parser.error('未找到可嵌入的中文TrueType字体；请用--font指定。' + '\n'.join(errors))
    pdfmetrics.registerFontFamily('CJK', normal='CJK', bold='CJK', italic='CJK', boldItalic='CJK')
    try:
        source = args.input_md.read_text(encoding='utf-8')
    except OSError as exc:
        parser.error(str(exc))
    if not source.strip():
        parser.error('输入Markdown为空。')
    if '```' in source or re.search(r'!\[.*?\]\(', source):
        parser.error('此轻量导出器不支持代码块或图片，请先简化文档或使用专业导出工具。')

    ink, accent = HexColor('#243c43'), HexColor('#246e70')
    base = dict(fontName='CJK', fontSize=10, leading=16, wordWrap='CJK', textColor=ink, spaceAfter=7)
    styles = {'p': ParagraphStyle('p', **base)}
    for key, size in [('h1', 24), ('h2', 15), ('h3', 12)]:
        styles[key] = ParagraphStyle(key, **{**base, 'fontSize': size, 'leading': size*1.4, 'textColor': accent, 'keepWithNext': True, 'spaceBefore': 8})
    styles['cell'] = ParagraphStyle('cell', **{**base, 'fontSize': 9, 'leading': 13.5, 'spaceAfter': 0})
    styles['bullet'] = ParagraphStyle('bullet', **{**base, 'leftIndent': 10, 'firstLineIndent': -8})

    def inline(text):
        text = html.escape(text)
        text = re.sub(r'\[([^\]]+)\]\((https?://[^\s)]+)\)', lambda m: '<link href="'+m[2]+'" color="#246e70"><u>'+m[1]+'</u></link>', text)
        return re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)

    story, lines, index = [], source.splitlines(), 0
    width = 515.28
    while index < len(lines):
        line = lines[index].strip()
        index += 1
        if not line:
            continue
        if line == '<!-- PAGEBREAK -->':
            if story and not isinstance(story[-1], PageBreak):
                story.append(PageBreak())
            continue
        if line.startswith('|'):
            raw = [line]
            while index < len(lines) and lines[index].strip().startswith('|'):
                raw.append(lines[index].strip()); index += 1
            rows = []
            for row in raw:
                cells = [x.strip().replace('\\|', '|') for x in re.split(r'(?<!\\)\|', row.strip('|'))]
                if all(re.fullmatch(r':?-+:?', x) for x in cells):
                    continue
                rows.append(cells)
            n = len(rows[0])
            if n > 5 or any(len(row) != n for row in rows):
                parser.error('表格列数不一致或超过5列，请调整源文件。')
            weights = [min(28, max(9, max(len(row[c]) for row in rows))) ** .5 for c in range(n)]
            table = Table([[Paragraph(inline(c), styles['cell']) for c in row] for row in rows],
                          colWidths=[width*w/sum(weights) for w in weights], repeatRows=1, hAlign='LEFT')
            table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), HexColor('#d9e9e6')),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('LEFTPADDING', (0,0), (-1,-1), 7), ('RIGHTPADDING', (0,0), (-1,-1), 7),
                ('TOPPADDING', (0,0), (-1,-1), 6), ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [white, HexColor('#f3f6f5')]),
                ('LINEBELOW', (0,0), (-1,0), .6, accent),
            ]))
            # Preserve short tables; allow long tables to split with repeated headers.
            height = table.wrap(width, 750)[1]
            story.extend([KeepTogether([table]) if height < 320 else table, Spacer(1,9)])
            continue
        heading = re.match(r'^(#{1,6})\s+(.*)', line)
        if heading:
            key = 'h'+str(min(3,len(heading[1]))); line = heading[2]
        elif line.startswith('- '):
            key = 'bullet'; line = '· '+line[2:]
        else:
            key = 'p'
        story.append(Paragraph(inline(line), styles[key]))
    while story and isinstance(story[-1], PageBreak):
        story.pop()

    def footer(c, doc):
        c.saveState(); c.setStrokeColor(HexColor('#c8d8d5')); c.line(40,38,555,38)
        c.setFont('CJK',8); c.setFillColor(HexColor('#647276'))
        title = args.title
        while pdfmetrics.stringWidth(title, 'CJK', 8) > 455:
            title = title[:-2]+'…'
        c.drawString(40,25,title); c.drawRightString(555,25,str(doc.page)); c.restoreState()

    args.output_pdf.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(args.output_pdf), pagesize=(595.28,841.89), leftMargin=40, rightMargin=40,
                            topMargin=36, bottomMargin=49, title=args.title, author='旅行规划')
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(f'PDF written: {args.output_pdf.resolve()}')


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Маленький писатель .xlsx без внешних библиотек: листы, ширина колонок, закрепленная шапка,
фильтр, перенос строк, даты и заливка ячеек. Открывается в Excel, Numbers и Google Таблицах.

    write_xlsx(path, [{'name': 'План', 'columns': [('№', 5), ('Тема', 60)],
                       'rows': [[1, ('Текст', 'wrap')]], 'freeze': True, 'filter': True}])

Ячейка: значение (str, int, float, datetime.date, None) или пара (значение, стиль).
Стили: head, wrap, date, num, bold, title, и заливки статусов done, ready, work, hold, plan.
"""
import datetime
import zipfile
from xml.sax.saxutils import escape

NS = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
NSR = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
STAMP = (2026, 1, 1, 0, 0, 0)  # постоянная дата внутри архива: одинаковое содержимое = одинаковый файл
EPOCH = datetime.date(1899, 12, 30)

# порядок совпадает с cellXfs в styles.xml
STYLES = {None: 0, 'head': 1, 'wrap': 2, 'date': 3, 'num': 4, 'done': 5, 'ready': 6, 'work': 7, 'hold': 8,
          'plan': 9, 'title': 10, 'bold': 11}
FILLS = ['EEF0FE', 'DFF5E3', 'E3E8FE', 'FFF4BF', 'FBE0E0']  # шапка, вышла, готова, в работе, отложена

STYLES_XML = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="{NS}">
<numFmts count="1"><numFmt numFmtId="164" formatCode="dd.mm.yyyy"/></numFmts>
<fonts count="3">
<font><sz val="11"/><name val="Arial"/><family val="2"/></font>
<font><b/><sz val="11"/><name val="Arial"/><family val="2"/></font>
<font><b/><sz val="14"/><name val="Arial"/><family val="2"/></font>
</fonts>
<fills count="{2 + len(FILLS)}">
<fill><patternFill patternType="none"/></fill>
<fill><patternFill patternType="gray125"/></fill>
{''.join(f'<fill><patternFill patternType="solid"><fgColor rgb="FF{c}"/><bgColor indexed="64"/></patternFill></fill>' for c in FILLS)}
</fills>
<borders count="2">
<border><left/><right/><top/><bottom/><diagonal/></border>
<border><left/><right/><top/><bottom style="thin"><color rgb="FFC9CCE0"/></bottom><diagonal/></border>
</borders>
<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
<cellXfs count="12">
<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
<xf numFmtId="0" fontId="1" fillId="2" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1"><alignment vertical="center" wrapText="1"/></xf>
<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0" applyAlignment="1"><alignment vertical="top" wrapText="1"/></xf>
<xf numFmtId="164" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1" applyAlignment="1"><alignment vertical="top"/></xf>
<xf numFmtId="3" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1" applyAlignment="1"><alignment vertical="top"/></xf>
<xf numFmtId="0" fontId="0" fillId="3" borderId="0" xfId="0" applyFill="1" applyAlignment="1"><alignment vertical="top" wrapText="1"/></xf>
<xf numFmtId="0" fontId="0" fillId="4" borderId="0" xfId="0" applyFill="1" applyAlignment="1"><alignment vertical="top" wrapText="1"/></xf>
<xf numFmtId="0" fontId="0" fillId="5" borderId="0" xfId="0" applyFill="1" applyAlignment="1"><alignment vertical="top" wrapText="1"/></xf>
<xf numFmtId="0" fontId="0" fillId="6" borderId="0" xfId="0" applyFill="1" applyAlignment="1"><alignment vertical="top" wrapText="1"/></xf>
<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0" applyAlignment="1"><alignment vertical="top" wrapText="1"/></xf>
<xf numFmtId="0" fontId="2" fillId="0" borderId="0" xfId="0" applyFont="1"/>
<xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0" applyFont="1" applyAlignment="1"><alignment vertical="top" wrapText="1"/></xf>
</cellXfs>
<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>
</styleSheet>'''


def col(i):
    """0 -> A, 25 -> Z, 26 -> AA."""
    s = ''
    i += 1
    while i:
        i, r = divmod(i - 1, 26)
        s = chr(65 + r) + s
    return s


def clean(text):
    return escape(''.join(ch for ch in str(text) if ch in '\t\n' or ord(ch) >= 32))


def cell(ref, v):
    v, st = v if isinstance(v, tuple) else (v, None)
    s = STYLES[st]
    if v is None or v == '':
        return f'<c r="{ref}" s="{s}"/>' if s else ''
    if isinstance(v, datetime.date):
        return f'<c r="{ref}" s="{s or STYLES["date"]}"><v>{(v - EPOCH).days}</v></c>'
    if isinstance(v, bool):
        v = 'да' if v else 'нет'
    if isinstance(v, (int, float)):
        return f'<c r="{ref}" s="{s}"><v>{v}</v></c>'
    return f'<c r="{ref}" s="{s}" t="inlineStr"><is><t xml:space="preserve">{clean(v)}</t></is></c>'


def sheet_xml(sh, first):
    cols, rows = sh['columns'], sh['rows']
    head = [(c[0], 'head') for c in cols] if sh.get('header', True) else None
    data = ([head] if head else []) + rows
    selected = ' tabSelected="1"' if first else ''
    out = [f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<worksheet xmlns="{NS}" xmlns:r="{NSR}">',
           f'<sheetViews><sheetView workbookViewId="0"{selected}>']
    if sh.get('freeze') and head:
        out.append('<pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/>')
    out.append('</sheetView></sheetViews><sheetFormatPr defaultRowHeight="15"/><cols>')
    out += [f'<col min="{i}" max="{i}" width="{w}" customWidth="1"/>' for i, (_, w) in enumerate(cols, 1)]
    out.append('</cols><sheetData>')
    for r, row in enumerate(data, 1):
        cells = ''.join(cell(f'{col(i)}{r}', v) for i, v in enumerate(row))
        ht = ' ht="30" customHeight="1"' if head and r == 1 else ''
        out.append(f'<row r="{r}"{ht}>{cells}</row>')
    out.append('</sheetData>')
    if sh.get('filter') and head and rows:
        out.append(f'<autoFilter ref="A1:{col(len(cols) - 1)}{len(data)}"/>')
    out.append('</worksheet>')
    return ''.join(out)


def write_xlsx(path, sheets):
    names = [s['name'][:31] for s in sheets]
    defined = ''.join(
        f'<definedName name="_xlnm._FilterDatabase" localSheetId="{i}" hidden="1">'
        f'\'{clean(names[i])}\'!$A$1:${col(len(s["columns"]) - 1)}${len(s["rows"]) + 1}</definedName>'
        for i, s in enumerate(sheets) if s.get('filter') and s['rows'])
    workbook = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<workbook xmlns="{NS}" xmlns:r="{NSR}"><sheets>'
                + ''.join(f'<sheet name="{clean(n)}" sheetId="{i}" r:id="rId{i}"/>' for i, n in enumerate(names, 1))
                + '</sheets>' + (f'<definedNames>{defined}</definedNames>' if defined else '') + '</workbook>')
    n = len(sheets)
    rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            + ''.join(f'<Relationship Id="rId{i}" Type="{NSR}/worksheet" Target="worksheets/sheet{i}.xml"/>' for i in range(1, n + 1))
            + f'<Relationship Id="rId{n + 1}" Type="{NSR}/styles" Target="styles.xml"/></Relationships>')
    types = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
             '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
             '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
             '<Default Extension="xml" ContentType="application/xml"/>'
             '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
             + ''.join(f'<Override PartName="/xl/worksheets/sheet{i}.xml" '
                       'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>' for i in range(1, n + 1))
             + '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
             '</Types>')
    root = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            f'<Relationship Id="rId1" Type="{NSR}/officeDocument" Target="xl/workbook.xml"/></Relationships>')
    parts = [('[Content_Types].xml', types), ('_rels/.rels', root), ('xl/workbook.xml', workbook),
             ('xl/_rels/workbook.xml.rels', rels), ('xl/styles.xml', STYLES_XML)]
    parts += [(f'xl/worksheets/sheet{i}.xml', sheet_xml(s, i == 1)) for i, s in enumerate(sheets, 1)]
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, data in parts:
            info = zipfile.ZipInfo(name, STAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, data.encode('utf-8'))

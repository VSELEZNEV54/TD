# -*- coding: utf-8 -*-
"""Шаблоны Excel для бесплатных инструментов. Пишем xlsx стандартной библиотекой: это zip с XML.
Файлы кладутся в site/assets/files/ при каждой сборке."""
import zipfile
from xml.sax.saxutils import escape

COLS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

# стили: 0 обычный, 1 шапка, 2 деньги, 3 итог, 4 подсказка, 5 время, 6 ячейка расписания
STYLES = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<numFmts count="1"><numFmt numFmtId="164" formatCode="#,##0"/></numFmts>
<fonts count="4"><font><sz val="11"/><name val="Arial"/></font><font><b/><sz val="11"/><color rgb="FFFFFFFF"/><name val="Arial"/></font><font><b/><sz val="11"/><name val="Arial"/></font><font><i/><sz val="10"/><color rgb="FF676A82"/><name val="Arial"/></font></fonts>
<fills count="5"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill><fill><patternFill patternType="solid"><fgColor rgb="FF445BF6"/></patternFill></fill><fill><patternFill patternType="solid"><fgColor rgb="FFF4EA00"/></patternFill></fill><fill><patternFill patternType="solid"><fgColor rgb="FFF0F2FF"/></patternFill></fill></fills>
<borders count="2"><border/><border><left style="thin"><color rgb="FFD9DCEB"/></left><right style="thin"><color rgb="FFD9DCEB"/></right><top style="thin"><color rgb="FFD9DCEB"/></top><bottom style="thin"><color rgb="FFD9DCEB"/></bottom></border></borders>
<cellStyleXfs count="1"><xf/></cellStyleXfs>
<cellXfs count="7">
<xf fontId="0" fillId="0" borderId="1" applyBorder="1"/>
<xf fontId="1" fillId="2" borderId="1" applyFont="1" applyFill="1" applyBorder="1"><alignment vertical="center" wrapText="1"/></xf>
<xf fontId="0" fillId="0" borderId="1" numFmtId="164" applyNumberFormat="1" applyBorder="1"/>
<xf fontId="2" fillId="3" borderId="1" numFmtId="164" applyFont="1" applyFill="1" applyNumberFormat="1" applyBorder="1"/>
<xf fontId="3" fillId="0" borderId="0" applyFont="1"/>
<xf fontId="2" fillId="4" borderId="1" applyFont="1" applyFill="1" applyBorder="1"><alignment horizontal="center"/></xf>
<xf fontId="0" fillId="0" borderId="1" applyBorder="1"><alignment wrapText="1" vertical="top"/></xf>
</cellXfs>
</styleSheet>'''


def cell(ref, v, s=0):
    if v is None or v == '':
        return f'<c r="{ref}" s="{s}"/>'
    if isinstance(v, str) and v.startswith('='):
        return f'<c r="{ref}" s="{s}"><f>{escape(v[1:])}</f></c>'
    if isinstance(v, (int, float)):
        return f'<c r="{ref}" s="{s}"><v>{v}</v></c>'
    return f'<c r="{ref}" s="{s}" t="inlineStr"><is><t xml:space="preserve">{escape(v)}</t></is></c>'


def sheet(rows, widths, freeze=1, heights=None):
    cols = ''.join(f'<col min="{i + 1}" max="{i + 1}" width="{w}" customWidth="1"/>' for i, w in enumerate(widths))
    xml_rows = []
    for r, row in enumerate(rows, 1):
        ht = f' ht="{heights[r]}" customHeight="1"' if heights and r in heights else ''
        cells = ''.join(cell(f'{COLS[c]}{r}', v, s) for c, (v, s) in enumerate(row))
        xml_rows.append(f'<row r="{r}"{ht}>{cells}</row>')
    pane = f'<sheetViews><sheetView workbookViewId="0"><pane ySplit="{freeze}" topLeftCell="A{freeze + 1}" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>' if freeze else ''
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            f'{pane}<cols>{cols}</cols><sheetData>{"".join(xml_rows)}</sheetData></worksheet>')


def book(path, sheets):
    """sheets: [(название, xml листа)]"""
    names = ''.join(f'<sheet name="{escape(n)}" sheetId="{i + 1}" r:id="rId{i + 1}"/>' for i, (n, _) in enumerate(sheets))
    rels = ''.join(f'<Relationship Id="rId{i + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i + 1}.xml"/>' for i in range(len(sheets)))
    rels += f'<Relationship Id="rId{len(sheets) + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
    over = ''.join(f'<Override PartName="/xl/worksheets/sheet{i + 1}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>' for i in range(len(sheets)))
    files = {
        '[Content_Types].xml': '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>' + over + '</Types>',
        '_rels/.rels': '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>',
        'xl/workbook.xml': '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>' + names + '</sheets><calcPr calcId="191029" fullCalcOnLoad="1"/></workbook>',
        'xl/_rels/workbook.xml.rels': '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' + rels + '</Relationships>',
        'xl/styles.xml': STYLES,
    }
    for i, (_, xml) in enumerate(sheets):
        files[f'xl/worksheets/sheet{i + 1}.xml'] = xml
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, data in files.items():
            info = zipfile.ZipInfo(name, date_time=(2026, 10, 23, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, data)


def ledger(path):
    """Таблица учета: ученики с формулами из журнала уроков, журнал уроков и оплат."""
    H, M, T, N, G = 1, 2, 3, 4, 0
    students = [('Марина Кузнецова', 'Алгебра, 9 класс', 'Елена Кузнецова', '', 1800),
                ('Артем Дроздов', 'Физика', '', '', 1300),
                ('Соня Ветрова', 'ОГЭ, математика', '', '', 1400)]
    rows = [[('Ученик', H), ('Предмет', H), ('Родитель', H), ('Телефон', H), ('Ставка, руб.', H), ('Уроков проведено', H), ('Начислено, руб.', H), ('Оплачено, руб.', H), ('Долг, руб.', H), ('Заметки', H)]]
    for i in range(30):
        r = i + 2
        s = students[i] if i < len(students) else ('', '', '', '', '')
        rows.append([(s[0], G), (s[1], G), (s[2], G), (s[3], G), (s[4], M),
                     (f'=IF(A{r}="","",COUNTIFS(\'Журнал уроков\'!B:B,A{r},\'Журнал уроков\'!E:E,"был"))', G),
                     (f'=IF(A{r}="","",E{r}*F{r})', M),
                     (f'=IF(A{r}="","",SUMIF(\'Журнал уроков\'!B:B,A{r},\'Журнал уроков\'!F:F))', M),
                     (f'=IF(A{r}="","",G{r}-H{r})', M), ('', G)])
    rows.append([('Итого', T), ('', T), ('', T), ('', T), ('', T), ('=SUM(F2:F31)', T), ('=SUM(G2:G31)', T), ('=SUM(H2:H31)', T), ('=SUM(I2:I31)', T), ('', T)])
    rows.append([('', 0)])
    rows.append([('Как пользоваться: впишите учеников и ставку, а уроки и оплаты отмечайте на листе «Журнал уроков». Начисления и долг считаются сами.', N)])
    rows.append([('Шаблон от TeacherDesk, teacherdesk.ru. Когда учеников станет больше, перенесите их в кабинет: баланс будет считаться после каждого урока.', N)])
    s1 = sheet(rows, [24, 20, 22, 18, 13, 16, 16, 16, 13, 30])
    log = [[('Дата', H), ('Ученик', H), ('Тема урока', H), ('Задано', H), ('Статус (был, пропуск, перенос)', H), ('Оплата, руб.', H)]]
    demo = [('2026-09-23', 'Марина Кузнецова', 'Неравенства', 'Вариант 1', 'был', 1800), ('2026-09-24', 'Артем Дроздов', 'Законы Ньютона', 'Задачи 1-5', 'был', 1300),
            ('2026-09-25', 'Соня Ветрова', 'ОГЭ, задание 20', '5 задач', 'был', 1400), ('2026-09-28', 'Артем Дроздов', 'Импульс', '', 'пропуск', 0)]
    for i in range(200):
        dmo = demo[i] if i < len(demo) else ('', '', '', '', '', '')
        log.append([(dmo[0], G), (dmo[1], G), (dmo[2], G), (dmo[3], G), (dmo[4], G), (dmo[5] if dmo[5] != '' else '', M)])
    s2 = sheet(log, [12, 24, 28, 22, 22, 14])
    book(path, [('Ученики и оплаты', s1), ('Журнал уроков', s2)])


def schedule(path):
    """Шаблон расписания: неделя по получасам и список учеников."""
    H, TM, C = 1, 5, 6
    days = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
    rows = [[('Время', H)] + [(d, H) for d in days]]
    heights = {1: 22}
    for i in range(27):
        h, m = 8 + i // 2, '00' if i % 2 == 0 else '30'
        rows.append([(f'{h}:{m}', TM)] + [('', C)] * 7)
        heights[i + 2] = 30
    s1 = sheet(rows, [9] + [18] * 7, 1, heights)
    st = [[('Ученик', H), ('Предмет', H), ('День', H), ('Время', H), ('Длительность, мин', H), ('Ставка, руб.', H), ('Контакт родителя', H)]]
    for _ in range(30):
        st.append([('', 0)] * 5 + [('', 2), ('', 0)])
    s2 = sheet(st, [24, 18, 14, 10, 16, 13, 24])
    book(path, [('Неделя', s1), ('Ученики', s2)])


def build_all(site):
    files = site / 'assets' / 'files'
    ledger(files / 'tablica-ucheta.xlsx')
    schedule(files / 'shablon-raspisaniya.xlsx')

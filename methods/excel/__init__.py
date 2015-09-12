# coding:utf-8
__author__ = 'dvpermyakov'

import lxml.html
import xlwt
from datetime import datetime
from collections import defaultdict
from webapp2_extras import jinja2


def send_excel_file(request_handler, name, template_name,  **values):
    values['btn_type'] = 'xls'
    html_body = jinja2.get_jinja2().render_template('mt/reports/' + template_name, **values)
    page = lxml.html.fromstring(html_body)
    book = xlwt.Workbook()
    sheet = book.add_sheet(name)
    cells_used = defaultdict(set)

    style = xlwt.XFStyle()
    style.borders.left = style.borders.right = style.borders.top = style.borders.bottom = xlwt.Borders.THIN

    if page.xpath("body/table"):
        array = page.xpath("body/table")[0].findall("tr")
    elif page.xpath("body/form/table"):
        array = page.xpath("body/form/table")[0].findall("tr")
    else:
        array = None
    if not array:
        return None

    for i, tr in enumerate(array):
        for j, td in enumerate(tr.getchildren()):
            while j in cells_used[i]:
                j += 1

            if i == 0 and "data-no-excel" in td.attrib:
                sheet.col(j).width = 0

            value = u''.join(td.text) if td.text else u''
            try:
                value = float(value)
            except ValueError:
                pass

            rowspan = int(td.attrib.get("rowspan", "1"))
            colspan = int(td.attrib.get("colspan", "1"))
            if rowspan > 1 or colspan > 1:
                sheet.write_merge(i, i + rowspan - 1, j, j + colspan - 1, value, style)
            else:
                sheet.write(i, j, value, style)
            for row in xrange(i, i + rowspan):
                for col in range(j, j + colspan):
                    cells_used[row].add(col)

    if request_handler:
        request_handler.response.headers['Content-Type'] = 'application/ms-excel'
        request_handler.response.headers['Content-Transfer-Encoding'] = 'Binary'
        request_handler.response.headers['Content-disposition'] = 'attachment; filename="%s-%s.xls"' % (datetime.now().date(), name)
        book.save(request_handler.response.out)
    return book

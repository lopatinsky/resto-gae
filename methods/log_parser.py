# coding=utf-8

import ast
import json
import re
from collections import namedtuple, defaultdict, Counter
import datetime

# download logs with:
# appcfg.py request_logs -n <num_days> --severity=0 . <filename>


LogRecord = namedtuple("LogRecord", (
    "ip",
    "unknown1",
    "unknown2",
    "date",
    "method",
    "path",
    "status",
    "size",
    "useragent",
    "lines"))
_first_re = re.compile('^(\S+) (\S+) (\S+) \[([^\]]+) -0700\] "([A-Z]+) (\S+) HTTP/1.1" (\d+) (\d+) \S+ (?:-|"([^"]+)")\n$')
_dct_re = re.compile("UnicodeMultiDict\((.*)\)\n$")


class UserDayLog(object):
    successes = 0
    failures = 0


DayStat = namedtuple("DayStat", (
    "successes",
    "failures",
    "unique_users",
    "unique_successes",
    "unique_failures",
    "failures_only"))


class DayLog(object):
    _dct = None

    def __init__(self):
        self._dct = defaultdict(UserDayLog)

    def add(self, record):
        phone = get_phone(record)
        item = self._dct[phone]
        if record.status >= 400:
            item.failures += 1
        else:
            item.successes += 1

    def get_stats(self):
        successes = failures = unique_successes = unique_failures = failures_only = 0
        for item in self._dct.values():
            if item.successes:
                successes += item.successes
                unique_successes += 1
            if item.failures:
                failures += item.failures
                unique_failures += 1
            if item.failures and not item.successes:
                failures_only += 1
        return DayStat(successes, failures, len(self._dct), unique_successes, unique_failures, failures_only)


def parse_first(first):
    match = _first_re.match(first)
    date = datetime.datetime.strptime(match.group(4), "%d/%b/%Y:%H:%M:%S") + datetime.timedelta(hours=7)
    return LogRecord(
        ip=match.group(1),
        unknown1=match.group(2),
        unknown2=match.group(3),
        date=date,
        method=match.group(5),
        path=match.group(6),
        status=int(match.group(7)),
        size=int(match.group(8)),
        useragent=match.group(9),
        lines=[]
    )


def get_phone(record):
    line1 = record.lines[0]
    request_dict_list, = _dct_re.findall(line1)
    request_dict = dict(ast.literal_eval(request_dict_list))
    return request_dict['phone']


def get_error(record):
    assert record.status >= 400
    if record.status == 500:
        if "deadline" in record.lines[-1].lower():
            return "deadline"
        elif "%28null%29" in record.path:
            return "null venue"
        return "500"
    else:
        msg = record.lines[-1][21:-1]
        if "время доставки" in msg or "будут доступны" in msg:
            return "time"
        elif "стоп-лист" in msg:
            return "stop-list"
        elif msg.startswith('{'):
            return "alfa"
        elif "pre check" in msg:
            iiko_resp = json.loads(record.lines[-2][21:-1])
            if "unregistered or deleted" in iiko_resp["message"]:
                return "pre-check: delivery terminal"
            elif "has invalid format" in iiko_resp["message"]:
                return "pre-check: invalid phone"
            return "pre-check: %s" % iiko_resp["message"]
        return msg


def main():
    with open("log2.log") as log:
        lines = log.readlines()

    records = []
    i = 0
    while i < len(lines):
        first_line = lines[i]
        record = parse_first(first_line)
        if i % 1000 < 5:
            print record.date
        while i + 1 < len(lines) and lines[i + 1][0] == "\t":
            record.lines.append(lines[i + 1])
            i += 1
        i += 1
        if record.path.endswith("order/new"):
            records.append(record)
    del lines

    print "Date\tTotal successes\tTotal failures\tUnique users\tUnique successes\tUnique failures\tWithout success"
    dct = defaultdict(DayLog)
    for record in records:
        dct[record.date.date()].add(record)
    for date, stat in sorted(dct.items()):
        print "%s\t%s\t%s\t%s\t%s\t%s\t%s" % ((date,) + stat.get_stats())

    log_start = records[0].date.date()
    week_start = log_start
    week_end = log_start + datetime.timedelta(7)
    errors = defaultdict(lambda: defaultdict(set))
    for record in records:
        if record.status < 400:
            continue
        if record.date.date() >= week_end:
            week_start = week_end
            week_end = week_end + datetime.timedelta(7)
        errors[week_start][get_error(record)].add(get_phone(record))
    for week_start, error_info in sorted(errors.items()):
        print ""
        print week_start
        for msg, phones in sorted(error_info.items(), key=lambda x: len(x[1]), reverse=True):
            print len(phones), msg


if __name__ == "__main__":
    main()

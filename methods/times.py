import time


def timestamp(datetime_object):
    return int(time.mktime(datetime_object.timetuple()))
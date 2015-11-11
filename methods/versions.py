# coding=utf-8

import re
from models.iiko.customer import IOS_DEVICE, ANDROID_DEVICE


def get_platform_and_version(ua):
    match = re.match('[^/]+/([0-9.]+)', ua)
    if not match:
        return None, 0

    parts = match.group(1).split('.') + ['0', '0', '0']
    version = int(parts[0]) * 1000000 + int(parts[1]) * 10000 + int(parts[2]) * 100 + int(parts[3])

    if 'iOS' in ua:
        return IOS_DEVICE, version
    elif 'Android' in ua:
        return ANDROID_DEVICE, version
    else:
        return None, version


def supports_review(ua):
    platform, version = get_platform_and_version(ua)
    if platform == IOS_DEVICE:
        return version >= 2000700
    if platform == ANDROID_DEVICE:
        return version >= 1020200
    return False

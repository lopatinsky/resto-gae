# coding=utf-8

import re

from models.iiko.company import CompanyNew
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


def supports_review(org_id, ua):
    platform, version = get_platform_and_version(ua)
    min_versions = {
        (CompanyNew.ORANGE_EXPRESS, IOS_DEVICE): 2000700,
        (CompanyNew.ORANGE_EXPRESS, ANDROID_DEVICE): 1020200,

        (CompanyNew.PANDA, IOS_DEVICE): 1000100,
        (CompanyNew.PANDA, ANDROID_DEVICE): 1060000,
    }
    if (org_id, platform) in min_versions:
        return version > min_versions[org_id, platform]
    return False

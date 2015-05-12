# coding=utf-8


def filter_phone(phone, check=False):
    phone = ''.join(c for c in phone if '0' <= c <= '9')
    if len(phone) == 10 and phone[0] != '7':
        phone = '7' + phone
    elif len(phone) == 11 and phone[0] == '8':
        phone = '7' + phone[1:]
    if check and (len(phone) != 11 or phone[0] not in '78'):
        return None
    return '+' + phone

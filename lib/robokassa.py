from hashlib import md5
import urllib

__author__ = 'phil'


# TODO normal
merch_login = ""
password1 = ""

def get_url(sum, order_number, desc):
    signature = md5(':'.join([merch_login, str(sum), str(order_number), password1])).hexdigest().upper()

    params = {"MrchLogin": merch_login,
              "OutSum": sum,
              "InvId": order_number,
              "Desc": desc,
              "SignatureValue": signature,
              "Culture": "ru",
              "Email": "phil.ficus@gmail.com",
              "Encoding": "utf-8"}

    url = "https://merchant.roboxchange.com/Index.aspx?"+urllib.urlencode(params)

    return url

# print get_url(500, 12354, "yeah")

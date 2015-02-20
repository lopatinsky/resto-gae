#coding=utf-8
__author__ = 'dvpermyakov'

from models.iiko import Venue


ALCOHOL_IDS_MAP = {
        Venue.SUSHILAR: [
            '5f241214-de73-48b9-9dbd-f118150b4ebd',  # Пиво разливное светлое 1л
            'f2c2f3af-39ea-4c3a-ae62-269c488e10ed',  # Пиво разливное темное 1л
        ],
        Venue.MIVAKO: [
            '25ba7f13-5ed1-46c9-bd57-e9fcb4adb283',  # Bud
            '050e6c7f-6c35-414e-82f4-62c87009a9b5',  # Балтика №0
            'cfc6901d-41be-4bb7-b421-913f74440acb',  # Hoegaarden
            '1cfad920-453d-49c4-80a1-286055d3e2fe',  # Крушовице светлое
            'c1235be2-e9c8-48de-a5e0-87ca374919ef',  # Крушовице темное
            '643cbbf9-f438-4f95-b4f1-ef18275735de',  # Сибирская корона лайм
            '04c5a8c8-9013-4ce4-b93f-1b0314b178b6',  # Хейнекен
            'e3b91c1b-6a50-485c-adcb-713ee86a09cd',  # Балтика №7
            '772b9250-becf-48fb-8ba2-bd819558516c',  # Велкопоповицкий козел (светлое)
            '1d5294ff-e5f2-465d-8fcf-7bc0b102a30a',  # Велкопоповицкий козел (темное)
        ]
    }


def check_alcohol(order_dict):
    pass
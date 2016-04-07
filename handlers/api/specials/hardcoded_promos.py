# coding=utf-8
from models.iiko.company import CompanyNew

HARDCODED_PROMOS = {
    CompanyNew.MIVAKO: [
        {
            "name": u"Первый заказ",
            "description": u"Скидка 10% на первый заказ",
            "start": None,
            "end": None,
            "image_url": "http://mivako.ru/local/templates/mivako/img/promo1.png",
            "id": "0",
            "display_type": 1,
        },
        {
            "name": u"Бонусная программа",
            "description": u"При каждом заказе Вы получаете от 3% до 10% от суммы заказа на свой бонусный счет.",
            "start": None,
            "end": None,
            "image_url": "http://mivako.ru/local/templates/mivako/img/promo2.png",
            "id": "1",
            "display_type": 1,
        },
        {
            "name": u"День рождения",
            "description": u"Если Вы именинник, то для вас мы сделаем скидку 15% на весь заказ. "
                           u"Сообщите о своем дне рождении оператору и приготовьте паспорт — "
                           u"его необходимо показать курьеру при доставке.",
            "start": None,
            "end": None,
            "image_url": "http://mivako.ru/local/templates/mivako/img/promo6.png",
            "id": "3",
            "display_type": 1,
        }
    ],
    CompanyNew.TYKANO: [
        {
            "name": u"Первый заказ",
            "description": u"Ролл Калифорния в подарок при первом заказе! "
                           u"Операторы добавят подарок в Ваш заказ.",
            "start": None,
            "end": None,
            "image_url": None,
            "id": "0",
            "display_type": 0,
        },
        {
            "name": u"Скидка на вынос и доставку",
            "description": u"Скидка 10% на все блюда при заказе с собой или на доставку. "
                           u"Цены в приложении указаны без учета скидок.",
            "start": None,
            "end": None,
            "image_url": None,
            "id": "1",
            "display_type": 0,
        }
    ],
    CompanyNew.DIMASH: [
        {
            "name": u"Доставим за 39 минут или бесплатно!",
            "description": u"Предложение действует при заказе Ассорти-сета \"Hollywood\" и не распространяется на "
                           u"заказы, в которые входят другие блюда, кроме данного.",
            "start": None,
            "end": None,
            "image_url": None,
            "id": "0",
            "display_type": 3
        },
        {
            "name": u"Время подарков!",
            "description": u"Оформите заказ с ПН по ЧТ с 14:00 до 17:00 и получите подарок! Актуальный спиок подарков "
                           u"уточняйте у оператора.",
            "start": None,
            "end": None,
            "image_url": None,
            "id": "1",
            "display_type": 3
        },
        {
            "name": u"1+1=3",
            "description": u"Закажите две пиццы одинакового размера на одинаковом тесте и получите пиццу на размер "
                           u"меньше в подарок!",
            "start": None,
            "end": None,
            "image_url": None,
            "id": "2",
            "display_type": 3
        },
        {
            "name": u"День рождения с DimAsh - скидка 10%!",
            "description": u"Вы можете воспользоваться скидкой в течение недели после даты рождения при предъявлении "
                           u"паспорта.",
            "start": None,
            "end": None,
            "image_url": None,
            "id": "3",
            "display_type": 3
        },
        {
            "name": u"Super подарки!",
            "description": u"При заказе от 600р Сложный ролл \"Цезарь\" в подарок.\n"
                           u"При заказе от 800р Гречневая WOK - лапша \"Соба с Курицей\" в подарок.\n"
                           u"При заказе от 1000р Пицца \"Четыре Сезона 24см Американо\" (Пышное тесто) в подарок.\n"
                           u"Акция не суммируется с другими акциями, бонусами и скидочными программами.",
            "start": None,
            "end": None,
            "image_url": None,
            "id": "4",
            "display_type": 3
        }
    ],
    CompanyNew.CHAIHANA_LOUNGE: [
        {
            "name": u"Скидка 25% на первый заказ",
            "description": u"Сделайте первый заказ через наше мобильное приложение и получите скидку 25%",
            "start": None,
            "end": None,
            "image_url": None,
            "id": "0",
            "display_type": 3
        },
        {
            "name": u"Скидка 5% на повторный заказ",
            "description": u"Заказывайте через наше мобильное приложение с 5% скидкой!",
            "start": None,
            "end": None,
            "image_url": None,
            "id": "1",
            "display_type": 3
        },
    ],
    CompanyNew.HLEB: [
    ],
}

# coding=utf-8

import logging
from translations import LANGUAGES, TEXTS

DEFAULT_LANGUAGE = 'ru'

_getters_cache = {}


class _TextGetter(object):
    _lang = None

    def __init__(self, lang):
        self._lang = lang

    def __getitem__(self, item):
        # returns the text with given identifier for current language

        # all texts must be defined in default language
        # otherwise text is not found, even if it is defined in current language
        if item in TEXTS[DEFAULT_LANGUAGE]:
            if item in TEXTS[self._lang]:
                return TEXTS[self._lang][item]
            else:
                logging.warning("i18n: %s not translated into %s", item, self._lang)
                return TEXTS[DEFAULT_LANGUAGE][item]
        else:
            logging.warning("i18n: %s does not exist in default lang", item)
            raise KeyError(item)


def make_getter(lang):
    if lang not in _getters_cache:
        _getters_cache[lang] = _TextGetter(lang)
    return _getters_cache[lang]


def lang_selector(request):
    header = request.headers.get('Accept-Language')
    if header:
        header = header.replace(' ', '')
        locales = []
        for locale_str in header.split(','):
            locale_parts = locale_str.split(';q=')
            locale = locale_parts[0].lower()
            if len(locale_parts) > 1:
                locale_q = float(locale_parts[1])
            else:
                locale_q = 1.0
            locales.append((locale, locale_q))

        locales.sort(key=lambda locale_tuple: locale_tuple[1], reverse=True)
        for locale, _ in locales:
            if locale in LANGUAGES:
                return LANGUAGES[locale]
            lang = locale[:2]
            if lang in LANGUAGES:
                return LANGUAGES[lang]

    return DEFAULT_LANGUAGE

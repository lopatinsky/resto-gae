# coding=utf-8

# contains all supported localizations, one entry per locale
TEXTS = {}

# contains all supported locales
# filled automatically, aliases can be added manually
LANGUAGES = {}

from . import en
from . import ru

LANGUAGES.update({lang: lang for lang in TEXTS})

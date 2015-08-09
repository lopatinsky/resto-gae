from methods.specials.cat import fix_syrop, fix_modifiers_by_own

__author__ = 'dvpermyakov'


def fix_cat_items(items):
    fix_syrop.set_syrop_items(items)
    fix_modifiers_by_own.set_modifier_by_own(company.iiko_org_id, items)
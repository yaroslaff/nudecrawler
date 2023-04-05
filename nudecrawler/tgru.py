from transliterate.base import TranslitLanguagePack, registry

class TgRuLanguagePack(TranslitLanguagePack):
    language_code = "tgru"
    language_name = "tgru"

    character_ranges = ((0x0400, 0x04FF), (0x0500, 0x052F))

    mapping = (
        u"abvgdezijklmnoprstufhcC'y'ABVGDEZIJKLMNOPRSTUFH'Y'",
        u"абвгдезийклмнопрстуфхцЦъыьАБВГДЕЗИЙКЛМНОПРСТУФХЪЫЬ",
    )

    #reversed_specific_mapping = (
    #    u"ъьЪЬ",
    #    u"''''"
    #)

    pre_processor_mapping = {
        u"zh": u"ж",
        "yo": 'ё',
        u"ch": u"ч",
        u"sh": u"ш",
        u"sch": u"щ",
        u"yu": u"ю",
        u"ya": u"я",
        "Yo": 'Ё',
        u"Zh": u"Ж",
        u"Ts": u"Ц",
        u"Ch": u"Ч",
        u"Sh": u"Ш",
        u"Sch": u"Щ",
        u"Yu": u"Ю",
        u"Ja": u"Я",
        u"EH": u"Э",
        u"eh": u"э"
    }


registry.register(TgRuLanguagePack)


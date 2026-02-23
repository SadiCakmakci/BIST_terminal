def get_t(key, lang="tr"):
    translations = {
        "tr": {
            "income_statement": "Gelir Tablosu",
            "balance_sheet": "Bilanço",
            "cash_flow": "Nakit Akışı",
            "annual": "Yıllık",
            "quarterly": "Çeyreklik",
        },
        "en": {
            "income_statement": "Income Statement",
            "balance_sheet": "Balance Sheet",
            "cash_flow": "Cash Flow",
            "annual": "Annual",
            "quarterly": "Quarterly",
        }
    }

    return translations.get(lang, {}).get(key, key)

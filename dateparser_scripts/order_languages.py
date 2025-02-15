import json
import os
from collections import OrderedDict

import regex as re

from dateparser_scripts.utils import get_raw_data

os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Languages with insufficient translation data are excluded
avoid_languages = {'cu', 'kkj', 'nds', 'prg', 'tk', 'vai', 'vai-Latn', 'vai-Vaii', 'vo'}

# Order from https://w3techs.com/technologies/overview/content_language
# Last updated on 30.10.2020
most_common_locales = [
    'en', 'ru', 'es', 'tr', 'fa', 'fr', 'de', 'ja', 'pt', 'vi', 'zh', 'ar', 'it', 'pl', 'id', 'el',
    'nl', 'ko', 'th', 'he', 'uk', 'cs', 'sv', 'ro', 'hu', 'da', 'sr', 'sk', 'fi', 'bg', 'hr', 'lt',
    'hi', 'nb', 'sl', 'nn', 'et', 'lv'
]


def _get_language_locale_dict():
    cldr_dates_full_dir = "../raw_data/cldr_dates_full/main/"
    available_locale_names = os.listdir(cldr_dates_full_dir)
    available_language_names = [shortname for shortname in available_locale_names
                                if not re.search(r'-[A-Z0-9]+$', shortname)]
    available_language_names.remove('root')
    language_locale_dict = {}
    for language_name in available_language_names:
        language_locale_dict[language_name] = []
        for locale_name in available_locale_names:
            if re.match(language_name + '-[A-Z0-9]+$', locale_name):
                language_locale_dict[language_name].append(locale_name)

    for language in avoid_languages:
        if language in language_locale_dict:
            del language_locale_dict[language]
    return language_locale_dict


def _get_language_order(language_locale_dict):
    territory_info_file = "../raw_data/cldr_core/supplemental/territoryInfo.json"
    with open(territory_info_file) as f:
        territory_content = json.load(f)
    territory_info_data = territory_content["supplemental"]["territoryInfo"]

    language_population_dict = {}
    for territory in territory_info_data:
        population = int(territory_info_data[territory]["_population"])
        try:
            lang_dict = territory_info_data[territory]["languagePopulation"]
            for language in lang_dict:
                language_population = float(lang_dict[language]["_populationPercent"]) * population
                if language in language_population_dict:
                    language_population_dict[language] += language_population
                else:
                    language_population_dict[language] = language_population
        except Exception:
            pass

    language_order_with_duplicates = (
        most_common_locales
        + sorted(
            language_population_dict.keys(),
            key=lambda x: (language_population_dict[x], x), reverse=True
        )
    )
    language_order = sorted(
        set(language_order_with_duplicates),
        key=lambda x: language_order_with_duplicates.index(x)
    )

    for index in range(0, len(language_order)):
        language_order[index] = re.sub(r'_', r'-', language_order[index])

    cldr_languages = language_locale_dict.keys()
    supplementary_date_directory = "../dateparser_data/supplementary_language_data/date_translation_data"
    supplementary_languages = [x[:-5] for x in os.listdir(supplementary_date_directory)]
    available_languages = set(cldr_languages).union(set(supplementary_languages))
    language_order = [shortname for shortname in language_order if shortname in available_languages]
    absent_languages = set(available_languages) - set(language_order)
    remaining_languages = []
    for language in absent_languages:
        parent_language = re.sub(r'-\w+', '', language)
        if parent_language in language_order:
            language_order.insert(language_order.index(parent_language) + 1, language)
        else:
            remaining_languages.append(language)
    language_order = language_order + sorted(remaining_languages)
    language_order = list(map(str, language_order))
    return language_order


def main():
    get_raw_data()
    language_locale_dict = _get_language_locale_dict()
    language_order = _get_language_order(language_locale_dict)

    parent_directory = "../dateparser/data/"
    filename = "../dateparser/data/languages_info.py"
    if not os.path.isdir(parent_directory):
        os.mkdir(parent_directory)
    language_order_string = 'language_order = ' + json.dumps(
        language_order, separators=(',', ': '), indent=4
    )

    complete_language_locale_dict = OrderedDict()
    for key in language_order:
        if key in language_locale_dict.keys():
            complete_language_locale_dict[key] = sorted(language_locale_dict[key])
        else:
            complete_language_locale_dict[key] = []

    language_locale_dict_string = 'language_locale_dict = ' + json.dumps(
        complete_language_locale_dict, separators=(',', ': '), indent=4
    )
    languages_info_string = language_order_string + '\n\n' + language_locale_dict_string + '\n'
    with open(filename, 'w') as f:
        f.write(languages_info_string)


if __name__ == '__main__':
    main()

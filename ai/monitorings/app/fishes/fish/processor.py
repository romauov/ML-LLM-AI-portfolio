import json
import re
from nltk.tokenize import word_tokenize

from app.fishes.fish.data import cuttings, fish_dict, fish_mapping_ext, freeze_state, prod_dict, size_range, \
    sort_quality, stemmed_fish_list, stemmed_prod_list, stemmer


def stem_text(text):
    words = word_tokenize(text.lower())
    stemmed_words = [stemmer.stem(word) for word in words]
    return " ".join(stemmed_words)


def classify_advertisement(text):
    stemmed_text = stem_text(text)
    found_stemmed_fish = [
        fish for fish in stemmed_fish_list if fish in stemmed_text]
    found_fish = [
        fish_dict[fish] for fish in found_stemmed_fish
    ]

    return found_fish


def get_fish_type(text):
    found_fish = classify_advertisement(text)
    if len(found_fish) > 1:
        for fish in fish_mapping_ext.keys():
            fishes = fish_mapping_ext[fish]
            if set(found_fish).issubset(set(fish_mapping_ext[fish])):
                return fish
        return 'multiple_values'

    elif len(found_fish) == 1:
        for fish in fish_mapping_ext.keys():
            fishes = fish_mapping_ext[fish]
            if found_fish in fishes:
                return fish
        return found_fish[0]


def get_alias(fish_type):
    if fish_type is not None:
        fish_type = fish_type.lower()
        if fish_type in fish_mapping_ext.keys():
            return json.dumps(fish_mapping_ext[fish_type], ensure_ascii=False)


def get_freeze_state(text):
    fr_states = []
    for state in freeze_state:
        if state in text.lower():
            fr_states.append(state)
    if len(fr_states) > 1:
        return 'multiple_values'
    elif len(fr_states) == 1:
        return fr_states[0]


def pick_size_range(fish_type, text):
    if fish_type is not None:
        fish_type = fish_type.lower()
        if fish_type in size_range.keys():
            sizes_list = size_range[fish_type]
            sizes = []
            for size in sizes_list:
                if size in text:
                    sizes.append(size)
            if len(sizes) > 1:
                return 'multiple_values'
            elif len(sizes) == 1:
                return sizes[0]


def get_cuttings(text):
    cleaned_text = re.sub(r'[^\w\s/]', ' ', text.lower())
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
    cleaned_text = " " + cleaned_text + " "

    cuts = []
    for key, aliases in cuttings.items():
        variants = [key] + [alias for alias in aliases]
        found = any(
            f" {variant} " in cleaned_text
            for variant in variants
        )
        if found:
            cuts.append(key)

    if cuts == []:
        return None
    return json.dumps(cuts, ensure_ascii=False)


def get_sort(text):
    sorts = []
    for s in sort_quality:
        if s in text:
            sorts.append(s)
    if len(sorts) == 1:
        return sorts[0]
    elif len(sorts) > 1:
        return 'multiple values'


def get_product_type(text):
    stemmed_text = stem_text(text)
    found_stemmed_prods = [
        prod for prod in stemmed_prod_list if prod in stemmed_text]

    exclusion_rules = {
        stemmer.stem('головы'): [stem_text('без головы')]
    }

    for stemmed_prod in found_stemmed_prods[:]:
        if stemmed_prod in exclusion_rules:
            for phrase in exclusion_rules[stemmed_prod]:
                if phrase in stemmed_text:
                    found_stemmed_prods.remove(stemmed_prod)
                    break

    found_prods = [prod_dict[prod] for prod in found_stemmed_prods]

    if len(found_prods) == 1:
        return found_prods[0]
    elif len(found_prods) > 1:
        return 'multiple values'


def process_fish_dataframe_cols(df):
    df = df[df['description'].notna()]
    df['fish_type'] = df['description'].apply(get_fish_type)
    df['fish_type_alias'] = df['fish_type'].apply(get_alias)
    df['temperature_state'] = df['description'].apply(get_freeze_state)
    df['size_range'] = df.apply(lambda row: pick_size_range(
        row['fish_type'], row['description']), axis=1)
    df['cutting'] = df['description'].apply(get_cuttings)
    df['sort'] = df['description'].apply(get_sort)
    df['product_type'] = df['description'].apply(get_product_type)
    return df

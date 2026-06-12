import re

import pandas as pd
from nltk.stem.snowball import SnowballStemmer
from nltk.corpus import stopwords

from app.fishes.semiprocessed.data import mapping_dict, fish_type_mapping, fish_type_alias_mapping, \
    product_type_mapping, smoking_mapping, cutting_mapping, cook_method_mapping, \
    filling_mapping, boxing_mapping


# text preprocessing func =====================================================

def process_raw_dataframe(text, mapping_dict):
    nltk_stopwords = set(stopwords.words('russian'))
    nltk_stopwords -= set(['без', 'на', 'с'])

    if pd.isna(text):
        return " "

    text = text.lower()

    processed_text = re.sub(r"[^a-zA-Zа-яА-Я/\s]", " ", str(text))
    processed_text = re.sub(r"(?<![а-яА-Яa-zA-Z])/|/(?![а-яА-Яa-zA-Z])", " ", processed_text)
    processed_text = re.sub(r"\d+", " ", processed_text)
    processed_text = re.sub(r"\s+", " ", processed_text).strip()

    words = processed_text.split()

    russian_stemmer = SnowballStemmer("russian")

    stemmed_words = []
    for word in words:
        stemmed_word = russian_stemmer.stem(word)
        stemmed_words.append(stemmed_word)

    allowed_words = {k.lower(): v for k, v in mapping_dict.items()}
    replaced_words = []
    for word in stemmed_words:
        replacement = allowed_words.get(word, "")
        if replacement:
            replaced_words.append(replacement)
        else:
            replaced_words.append(word)

    filtered_words = [
        word for word in replaced_words
        if word.lower() not in nltk_stopwords and (len(word) > 2 or word in ["ух", "яз", "на", "с", 'су', 'ст', "хк"])
    ]

    return " ".join(filtered_words)


# extract_type ===========================================================

def extract_type(text, mapping, check_multiple=True):
    found_values = []
    for pattern, value in mapping.items():
        if re.search(pattern, text):
            found_values.append(value)

    if check_multiple and len(found_values) > 1:
        return 'multiple values'
    elif found_values:
        return found_values[0]
    else:
        return None


# main processing ======================================================================
def process_semiprocessed_dataframe_cols(df):
    df['cleaned_description'] = df.loc[:, 'description'].apply(process_raw_dataframe, mapping_dict=mapping_dict)
    df.dropna(subset=["description"], inplace=True)
    df.drop_duplicates(inplace=True)
    df.reset_index(drop=True, inplace=True)
    df.index = range(1, len(df) + 1)
    df = df.copy()

    df["fish_type"] = df.loc[:, 'cleaned_description'].apply(extract_type, mapping=fish_type_mapping)
    df["fish_type_alias"] = df.loc[:, 'cleaned_description'].apply(extract_type, mapping=fish_type_alias_mapping)
    df["product_type"] = df.loc[:, 'cleaned_description'].apply(extract_type, mapping=product_type_mapping)
    df["smoking"] = df.loc[:, 'cleaned_description'].apply(extract_type, mapping=smoking_mapping)
    df['cutting'] = df.loc[:, 'cleaned_description'].apply(extract_type, mapping=cutting_mapping)
    df['cook_method'] = df.loc[:, 'cleaned_description'].apply(extract_type, mapping=cook_method_mapping)
    df['filling'] = df.loc[:, 'cleaned_description'].apply(extract_type, mapping=filling_mapping, check_multiple=False)
    df['boxing'] = df.loc[:, 'cleaned_description'].apply(extract_type, mapping=boxing_mapping)

    return df.drop(columns=['cleaned_description'], axis=1, errors='ignore')

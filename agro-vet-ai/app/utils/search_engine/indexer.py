import string
import pymorphy3
from collections import defaultdict


# https://github.com/stopwords-iso/stopwords-ru/blob/master/stopwords-ru.txt

try:
    with open("knowledge/search_engine/stopwords-ru.txt", 'r', encoding='utf-8') as f:
        RUSSIAN_STOPWORDS = {line.strip() for line in f if line.strip()}

except FileNotFoundError:
    RUSSIAN_STOPWORDS = set()


morph_analyzer = pymorphy3.MorphAnalyzer()


def preprocess_text(text):
    if not text:
        return []

    text = text.lower()

    text = text.translate(str.maketrans('', '', string.punctuation))

    tokens = text.split()

    processed_tokens = []
    for token in tokens:

        if token in RUSSIAN_STOPWORDS:
            continue

        parsed_token = morph_analyzer.parse(token)[0]
        lemma = parsed_token.normal_form

        processed_tokens.append(lemma)

    return processed_tokens


def flatten_list_items(items):
    """Recursively flatten list items to extract all text content."""
    if not items:
        return ''
    
    texts = []
    if isinstance(items, list):
        for item in items:
            if isinstance(item, str):
                texts.append(item)
            elif isinstance(item, list):
                # Handle nested lists
                texts.append(flatten_list_items(item))
            elif isinstance(item, dict):
                # Handle dictionaries by extracting their values
                for key, value in item.items():
                    texts.append(flatten_list_items(value))
    elif isinstance(items, dict):
        # Handle dictionaries by extracting their values
        for key, value in items.items():
            texts.append(flatten_list_items(value))
    else:
        texts.append(str(items))
    
    return ' '.join(texts)


def build_search_index(diseases):
    index = defaultdict(list)
    for disease in diseases:
        first_key = list(disease.keys())[0]
        disease = disease[first_key]

        # Handle both string and list values for clinical_findings and postmortem_findings
        clinical_findings = disease.get('clinical_findings', '')
        clinical_findings_text = flatten_list_items(clinical_findings)
        
        postmortem_findings = disease.get('postmortem_findings', '')
        postmortem_findings_text = flatten_list_items(postmortem_findings)

        content = ' '.join([clinical_findings_text, postmortem_findings_text])

        tokens = preprocess_text(content)
        for token in set(tokens):
            index[token].append({
                'disease_name': disease.get('disease_name', first_key),
                'score': tokens.count(token)
            })
    return index

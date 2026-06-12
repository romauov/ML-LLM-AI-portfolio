import math
from collections import defaultdict
from app.utils.search_engine.indexer import build_search_index, preprocess_text
from app.utils.search_engine.parser import parse_yml_files


class DiseaseSearchEngine:
    def __init__(self, diseases):
        self.diseases = diseases
        self.index = build_search_index(diseases)
        self.total_diseases = len(diseases)

    def calculate_tfidf(self, query):
        query_terms = preprocess_text(query)
        scores = defaultdict(float)

        for term in query_terms:
            if term not in self.index:
                continue

            # IDF calculation
            idf = math.log(self.total_diseases / len(self.index[term]))

            # TF-IDF для каждого заболевания
            for disease_info in self.index[term]:
                tf = disease_info['score']
                scores[disease_info['disease_name']] += tf * idf

        return scores

    def search(self, query, top_n=5):
        scores = self.calculate_tfidf(query)
        # Сортировка по убыванию релевантности
        sorted_scores = sorted(
            scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_scores[:top_n]


def create_search_engine(disease_path) -> DiseaseSearchEngine:
    return DiseaseSearchEngine(parse_yml_files(disease_path))

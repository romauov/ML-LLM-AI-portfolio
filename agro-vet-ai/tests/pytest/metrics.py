import math
import os
import re
import time
import pymorphy3
import requests
from dotenv import load_dotenv

load_dotenv()

_morph = pymorphy3.MorphAnalyzer()

TIMEOUT = 300
_THIN = "─" * 80


def _indent(text: str, prefix: str = "  ") -> str:
    return "\n".join(prefix + line for line in text.splitlines())


def _out(text: str) -> None:
    print(text)


def _lemma(word: str) -> str:
    normalized = word.lower().replace('ё', 'е')
    parses = _morph.parse(normalized)
    return parses[0].normal_form.replace('ё', 'е') if parses else normalized


def _text_lemmas(text: str) -> list[str]:
    return [_lemma(w) for w in re.findall(r'\w+', text, re.UNICODE)]


def _keyword_matches(keyword: str, text_lemmas: list[str]) -> bool:
    kw_tokens = [_lemma(w) for w in re.findall(r'\w+', keyword, re.UNICODE)]
    if not kw_tokens:
        return False
    if len(kw_tokens) == 1:
        return kw_tokens[0] in text_lemmas
    n = len(kw_tokens)
    for i in range(len(text_lemmas) - n + 1):
        if text_lemmas[i:i + n] == kw_tokens:
            return True
    return False



def assert_contains(data: dict, keywords: list[str], *, require_all: bool = False):
    lemmas = _text_lemmas(data["response"])
    if require_all:
        missing = [kw for kw in keywords if not _keyword_matches(kw, lemmas)]
        assert not missing, (
            f"Ответ не содержит обязательных слов {missing}.\n"
            f"Ответ: {data['response'][:500]}"
        )
    else:
        found = [kw for kw in keywords if _keyword_matches(kw, lemmas)]
        assert found, (
            f"Ответ не содержит ни одного из ожидаемых слов {keywords}.\n"
            f"Ответ: {data['response'][:500]}"
        )


def assert_not_contains(data: dict, keywords: list[str]):
    lemmas = _text_lemmas(data["response"])
    bad = [kw for kw in keywords if _keyword_matches(kw, lemmas)]
    assert not bad, (
        f"Ответ содержит запрещённые слова {bad}.\n"
        f"Ответ: {data['response'][:500]}"
    )


def _vectorize(text: str) -> list[float]:
    base_url = os.environ["OPENROUTER_BASE_URL"].rstrip("/")
    api_key = os.environ["OPENROUTER_API_KEY"]
    model = os.environ.get("EMBEDDING_MODEL")
    max_attempts = 3
    for attempt in range(max_attempts):
        response = requests.post(
            f"{base_url}/embeddings",
            json={"model": model, "input": text, "encoding_format": "float"},
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            timeout=TIMEOUT,
        )
        if response.status_code == 429:
            if attempt == max_attempts - 1:
                raise ValueError(f"Embeddings API вернул 429 после {max_attempts} попыток: {response.text}")
            delay = 2 ** attempt
            _out(f"Embeddings API 429 — повтор через {delay}s (попытка {attempt + 1}/{max_attempts})")
            time.sleep(delay)
            continue
        if not response.ok:
            raise ValueError(f"Embeddings API {response.status_code}: {response.text}")
        body = response.json()
        assert "data" in body, f"Неожиданный ответ от embeddings API: {body}"
        return body["data"][0]["embedding"]


def cosine_similarity(data: dict, reference: str) -> float:
    vec_a = _vectorize(data["response"])
    vec_b = _vectorize(reference)
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def assert_cosine_similarity(data: dict, reference: str, threshold: float = 0.8) -> float:
    score = cosine_similarity(data, reference)
    _out("ЭТАЛОН:")
    _out(_indent(reference))
    _out(_THIN)
    _out(f"cosine_similarity = {score:.3f}  (threshold={threshold})")
    assert score >= threshold, f"Косинусное сходство {score:.3f} ниже порога {threshold}."
    return score

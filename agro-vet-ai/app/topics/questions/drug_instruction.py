from typing import Dict, List
from app.llm.prompts.drug_instruction.system import DRUG_INSTRUCTION_SYSTEM_PROMPT
from app.llm.prompts.drug_instruction.extraction import DRUG_INSTRUCTION_EXTRACTOR_PROMPT
from app.topics.questions.base import BaseTopic
from app.topics.models import DrugSearchCriteria, DrugLLMResponse
from app.topics.utils import text_utils
from sqlalchemy import create_engine, text
from app.db.db import build_db_url
from config.config import Config
from app.utils.logger import get_logger

cfg = Config.from_yaml()


class DrugInstruction(BaseTopic):
    """
    Обработчик вопросов о лекарственных препаратах.
    Реализованы 2 типа поиска, векторный и по ключевым словам
    """

    # Флаг для включения векторного поиска
    VECTOR_SEARCH = True

    def __init__(self):
        super().__init__()
        self.logger = get_logger(__name__)
        self.topic_name = "drug_instruction"
        self.description = "Инструкции по лекарственным препаратам"
        self.db_engine = create_engine(build_db_url())
        self._drug_names_cache = None
        self._generic_names_cache = None

    def process(self, question: str, context: dict = None, dialog_history: list[dict[str, str]] = None) -> Dict[str, str]:
        """
        Обрабатывает вопрос о лекарственных препаратах через следующие этапы:
        1. Поиск релевантных препаратов (векторный или keyword - зависит от флага VECTOR_SEARCH)
        2. Форматирование найденных препаратов в таблицу
        3. Генерация финального ответа с помощью LLM
        """
        # ВЫБОР МЕТОДА
        try:
            if self.VECTOR_SEARCH:
                self.logger.info("[DRUG_SEARCH] Использую векторный поиск")
                relevant_drugs = self._search_drugs_by_vector(question, limit=5, threshold=0.75)
            else:
                self.logger.info("[DRUG_SEARCH] Использую keyword поиск")
                search_keywords = self._extract_keywords(question, dialog_history)
                relevant_drugs = self._search_drugs_by_keywords(search_keywords)

            if not relevant_drugs:
                return {
                    "tag": self.topic_name,
                    "content": "К сожалению, в базе данных не найдено препаратов, соответствующих вашему запросу. Рекомендую обратиться к ветеринарному врачу для получения профессиональной консультации.",
                    "context": "Empty context"
                }

            drugs_table_content = self._format_drugs_table(relevant_drugs)

            # Генерация финального ответа
            system_prompt = DRUG_INSTRUCTION_SYSTEM_PROMPT
            user_prompt = f"Контекст из базы данных: {drugs_table_content}\n\nВопрос пользователя: {question}" # DRUG_INSTRUCTION_USER_PROMPT.format(message=question, drug_instructions=drugs_table_content)
            messages = self.prompts_to_messages(system_prompt, user_prompt, dialog_history)
            response = self.ask_llm(messages=messages).content

            final_response = text_utils.parse_llm_json_response(response, DrugLLMResponse, "final_answer")
            if final_response:
                if final_response.confidence_reasoning:
                    self.logger.info(f"[LLM ANSWER CONFIDENCE] {final_response.confidence_reasoning}")
                if final_response.completeness_score > 0:
                    self.logger.info(f"[LLM COMPLETENESS SCORE] {final_response.completeness_score}")
                return {"tag": self.topic_name, "content": final_response.answer, "context": drugs_table_content}

            return {"tag": self.topic_name, "content": response, "context": drugs_table_content}

        except Exception as e:
            self.logger.error(f"[DRUG_INSTRUCTION ERROR]: {e}")
            return {
                "tag": self.topic_name,
                "content": "Произошла ошибка при обработке вопроса о препаратах. Рекомендую обратиться к ветеринарному врачу для получения профессиональной консультации по лекарственным препаратам.",
                "context": "Empty context"
            }

    def _extract_keywords(self, question: str, dialog_history: list[dict[str, str]] = None) -> DrugSearchCriteria:
        """Извлечение ключевых слов для поиска из вопроса пользователя"""
        drug_dictionaries = self._load_drug_dictionaries()
        trade_names_full = ', '.join(drug_dictionaries['trade_names'])
        generic_names_full = ', '.join(drug_dictionaries['generic_names'])
        initial_prompt = DRUG_INSTRUCTION_EXTRACTOR_PROMPT.format(
            message=question,
            trade_names_sample=trade_names_full,
            generic_names_sample=generic_names_full
        )
        messages = self.prompts_to_messages("", initial_prompt, dialog_history)
        response = self.ask_llm(messages=messages).content

        parsed_response = text_utils.parse_llm_json_response(response, DrugLLMResponse, "keywords")
        if parsed_response:
            if parsed_response.field_analysis:
                self.logger.info(f"[LLM FIELD ANALYSIS] {parsed_response.field_analysis}")
            if parsed_response.confidence_score > 0:
                self.logger.info(f"[LLM SEARCH CONFIDENCE] {parsed_response.confidence_score}")

            # Логирование извлеченных критериев поиска
            criteria = parsed_response.search_criteria
            self.logger.info(f"[SEARCH CRITERIA] Извлечены критерии: "
                           f"trade_name={criteria.trade_name}, "
                           f"generic_name={criteria.generic_name}, "
                           f"drug_class={criteria.drug_class}, "
                           f"target_animals={criteria.target_animals}, "
                           f"dosage_form={criteria.dosage_form}, "
                           f"route={criteria.route}")

            return criteria

        self.logger.warning("[SEARCH CRITERIA] Не удалось извлечь критерии поиска, используем пустые")
        return DrugSearchCriteria()

    def _load_drug_dictionaries(self) -> Dict[str, List[str]]:
        """Загрузка и кэширование торговых названий и действующих веществ"""
        if self._drug_names_cache is None or self._generic_names_cache is None:
            try:
                with self.db_engine.connect() as conn:
                    result = conn.execute(text("SELECT DISTINCT trade_name FROM drugs WHERE trade_name IS NOT NULL ORDER BY trade_name"))
                    self._drug_names_cache = [row[0] for row in result.fetchall()]
                    result = conn.execute(text("SELECT DISTINCT generic_name FROM drugs WHERE generic_name IS NOT NULL ORDER BY generic_name"))
                    self._generic_names_cache = [row[0] for row in result.fetchall()]

            except Exception as e:
                self.logger.error(f"[DRUG CACHE ERROR] Ошибка загрузки справочников: {e}")
                self._drug_names_cache = []
                self._generic_names_cache = []

        return {
            'trade_names': self._drug_names_cache,
            'generic_names': self._generic_names_cache
        }

    def _search_drugs_by_vector(
        self,
        question: str,
        limit: int = 5,
        threshold: float = 0.3
    ) -> list:
        """
        Векторный поиск препаратов по запросу пользователя.

        :param question: Вопрос пользователя для векторизации
        :param limit: Максимальное количество результатов
        :param threshold: Порог косинусного расстояния (меньше = ближе)
        :return: Список найденных препаратов
        """
        try:
            # 1. Векторизация вопроса
            self.logger.info(f"[VECTOR_SEARCH] Векторизация вопроса: {question[:100]}...")
            question_embedding = self.llm_provider.vectorize(question)

            # 2. Форматирование вектора для SQL
            embedding_literal = self._vector_literal(question_embedding)

            # 3. SQL запрос с косинусным расстоянием
            sql = text(f"""
                SELECT
                    *,
                    embedding <=> '{embedding_literal}' AS distance
                FROM drugs
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> '{embedding_literal}' ASC
                LIMIT :limit
            """)

            # 4. Выполнение запроса
            with self.db_engine.connect() as conn:
                result = conn.execute(sql, {"limit": limit})
                rows = result.fetchall()

            # 5. Фильтрация по порогу
            filtered_results = []
            for row in rows:
                self.logger.info(
                    f"[VECTOR_SEARCH] Кандидат: {row.trade_name} "
                    f"(distance={row.distance:.4f}, threshold={threshold})"
                )

                if row.distance <= threshold:
                    self.logger.info(
                        f"[VECTOR_SEARCH] ✓ Принят: {row.trade_name}"
                    )
                    filtered_results.append(row)
                else:
                    self.logger.info(
                        f"[VECTOR_SEARCH] ✗ Отсеян: {row.trade_name} "
                        f"(distance={row.distance:.4f} > {threshold})"
                    )

            self.logger.info(
                f"[VECTOR_SEARCH] Найдено {len(filtered_results)} препаратов "
                f"(из {len(rows)} до фильтрации)"
            )
            return filtered_results

        except Exception as e:
            self.logger.error(f"[VECTOR_SEARCH ERROR] {e}")
            return []

    @staticmethod
    def _vector_literal(vec: list[float]) -> str:
        """
        Форматирование вектора для pgvector SQL.
        """
        return "[" + ", ".join(f"{x:.10f}" for x in vec) + "]"

    def _search_drugs_by_keywords(self, keywords: DrugSearchCriteria) -> list:
        """Поиск препаратов в БД по ключевым словам"""
        if not any(
            [
                keywords.trade_name,
                keywords.generic_name,
                keywords.drug_class,
                keywords.target_animals,
                keywords.symptoms_keywords,
                keywords.dosage_form,
                keywords.route
            ]
        ):
            return []

        conditions = []
        params = {}
        param_counter = 0
        priority_conditions = []

        field_mapping = {
            'trade_name': 'trade_name',
            'generic_name': 'generic_name',
            'drug_class': 'drug_class',
            'target_animals': 'target_animals',
            # 'symptoms_keywords': 'instruction',
            'dosage_form': 'dosage_form',
            'route': 'route'
        }

        # Проходим по полям критериев и их колонкам БД; накапливаем условия для WHERE
        # и приоритетные условия (для сортировки по совпадениям названий)
        for keyword_field, db_field in field_mapping.items():
            field_values = getattr(keywords, keyword_field, [])
            if field_values:
                field_conditions = []
                # Для каждого значения поля добавляем условие и параметр;
                # для названий (generic/trade) дополнительно накапливаем приоритет
                for word in field_values:
                    param_name = f"param_{param_counter}"
                    if db_field == 'target_animals':
                        # Поиск в массиве: проверяем содержит ли массив элемент или подстроку
                        field_conditions.append(f"(:{param_name} = ANY({db_field}) OR EXISTS (SELECT 1 FROM unnest({db_field}) AS animal WHERE animal ILIKE :{param_name}_pattern))")
                        params[param_name] = word
                        params[f"{param_name}_pattern"] = f"%{word}%"
                    else:
                        field_conditions.append(f"{db_field} ILIKE :{param_name}")
                        params[param_name] = f"%{word}%"
                        if keyword_field in ['generic_name', 'trade_name']:
                            priority_conditions.append(f"({db_field} ILIKE :{param_name})")
                    param_counter += 1

                if field_conditions:
                    conditions.append(f"({' OR '.join(field_conditions)})")

        if not conditions:
            return []

        if priority_conditions:
            priority_expr = " + ".join([f"CASE WHEN {cond} THEN 10 ELSE 0 END" for cond in priority_conditions])
            order_clause = f"ORDER BY ({priority_expr}) DESC, id"
        else:
            order_clause = "ORDER BY id"

        sql = f"""
        SELECT * FROM drugs
        WHERE {' OR '.join(conditions)}
        {order_clause}
        LIMIT 5
        """

        with self.db_engine.connect() as conn:
            result = conn.execute(text(sql), params)
            return result.fetchall()

    def _format_drugs_table(self, drugs: list) -> str:
        """Форматирование найденных препаратов в таблицу"""
        if not drugs:
            return ""

        drug_entries = []
        for i, drug in enumerate(drugs, 1):
            animals = ', '.join(drug.target_animals) if isinstance(drug.target_animals, (list, tuple)) else drug.target_animals
            drug_entry = (
                f"ПРЕПАРАТ {i}\n"
                f"{'-'*40}\n"
                f"Название: {drug.trade_name}\n"
                f"Действующее вещество: {drug.generic_name}\n"
                f"Группа: {drug.drug_class}\n"
                f"Животные: {animals}\n"
                f"Форма: {drug.dosage_form}\n"
                f"Способ применения: {drug.route}\n"
                f"Производитель: {drug.manufacturer}\n\n"
                f"ПОЛНАЯ ИНСТРУКЦИЯ:\n"
                f"{drug.instruction.strip()}\n"
            )
            drug_entries.append(drug_entry)

        return (
            "\n" + "="*80 + "\n\n" +
            ("\n" + "-"*80 + "\n\n").join(drug_entries) +
            "\n" + "="*80 + "\n"
        )

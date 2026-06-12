# Сравнение старого (router v1) и нового (router_v2) агента

Дата: 2026-05-21
Ветка: router-v2-no-double-llm

| Тест | Статус (old) | Время (old) | Статус (new) | Время (new) | Примечание |
|---|---|---|---|---|---|
| TestGeneralQuestions::test_capabilities | PASSED | 25.9s | PASSED | 16.3s | |
| TestSwineDiagnosis::test_streptococcosis_symptoms | PASSED | 92.8s | PASSED | 44.2s | |
| TestSwineDiagnosis::test_prrs_symptoms | PASSED | 58.3s | PASSED | 30.3s | |
| TestSwineDiagnosis::test_edema_disease_symptoms | PASSED | 38.1s | PASSED | 101.8s | |
| TestSwineDiagnosis::test_app_symptoms | PASSED | 38.2s | PASSED | 33.9s | |
| TestSwineDiagnosis::test_mycoplasmosis_swine_symptoms | FAILED | 55.3s | PASSED | 40.2s | новый исправил |
| TestAvianDiagnosis::test_avian_influenza_symptoms | PASSED | 63.9s | FAILED | 12.2s | ❌ exception |
| TestAvianDiagnosis::test_infectious_bursal_disease_symptoms | PASSED | 83.7s | FAILED | 0.5s | ❌ exception |
| TestAvianDiagnosis::test_infectious_bronchitis_symptoms | PASSED | 48.8s | FAILED | 0.7s | ❌ exception |
| TestAvianDiagnosis::test_infectious_laryngotracheitis_symptoms | FAILED | 41.9s | FAILED | 0.5s | ❌ exception |
| TestAvianDiagnosis::test_mycoplasmosis_avian_symptoms | PASSED | 44.1s | FAILED | 0.5s | ❌ exception |
| TestLibrarian::test_erysipelas_swine | PASSED | 68.6s | FAILED | 0.5s | ❌ exception |
| TestLibrarian::test_streptococcosis_clinical_forms | PASSED | 154.0s | FAILED | 0.6s | ❌ exception |
| TestLibrarian::test_mycoplasmosis_poultry | PASSED | 173.3s | FAILED | 0.5s | ❌ exception |
| TestLibrarian::test_newcastle_disease | PASSED | 60.7s | FAILED | 0.3s | ❌ exception |
| TestLibrarian::test_app_strategic_therapy | PASSED | 146.9s | FAILED | 0.3s | ❌ exception |
| TestPharmacist::test_contraindications_tilanik | PASSED | 33.1s | FAILED | 0.2s | ❌ exception |
| TestPharmacist::test_active_substance_tiamulin | FAILED | 67.4s | FAILED | 0.2s | ❌ exception |
| TestPharmacist::test_spelink_interactions | FAILED | 276.6s | FAILED | 0.3s | ❌ exception |
| TestPharmacist::test_kolimixol_multispecies | PASSED | 88.5s | FAILED | 0.2s | ❌ exception |
| TestPharmacist::test_tiamulin_comparison_vik_vs_nitafarm | FAILED | 117.9s | FAILED | 0.4s | ❌ exception |

**Итого:**
- Старый (router v1): **16/21 passed** (5 failed — content issues)
- Новый (router_v2): **6/21 passed** (15 failed — все с `"Извините, произошла ошибка"`)

## Анализ

**Работает (6 тестов):**
- test_capabilities — без инструмента, просто LLM
- Все 5 тестов свиней — инструмент `process_with_swine_disease_diagnosis` (refactored)

**Падает с exception (15 тестов):**
- Все 5 тестов птиц — `process_with_avian_disease_diagnosis`
- Все 5 тестов librarian
- Все 5 тестов pharmacist

Все упавшие тесты возвращают `"Извините, произошла ошибка при обработке вашего вопроса."` за 0.2-0.7s (кроме первого — 12.2s).

**Вывод:** проблема в `process()` методе (синхронный путь). `process_stream` (асинхронный) не используется, т.к. тесты не передают `stream: true`.

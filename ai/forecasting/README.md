## Прогнозирование цены

Для прогноза используются модели:

- Exponential smoothing
- NeuralProphet
- Prophet
- ThetaModel
- TimesFM
- Sarimax (временно отключена)

По расписанию настроены два задания:

- прогноз на 3 месяца вперед с недельной дискретностью данных
- прогноз на 1 год вперед с месячной дискретностью данных

Алгоритм предсказания:

- Для каждого временного ряда откладывается тренировочная и валидационная выборка
- Подбор гиперапараметров на тренировочной выборке
- Получение прогноза для каждой модели на всей выборке
- Сохранение MAPE каждой модели в БД для последующего выбора лучшей модели SQL-запросом

Прогнозируются цены по определенным продуктам для каждого федерального округа отдельно и сразу по всем федеральным
округам.
Шаг прогноза 1 неделя.

## Сборка
`make download_hf_models`

`docker compose up -d --build`

## Тесты

Юнит тесты:

- `make unit-tests`

API тесты:

- поднять приложение `docker compose up -d --build`
- запустить тесты `make api-tests`

e2e тесты:

- `make e2e-tests`

## Примеры SQL запросов для получения прогнозов

Получение последних предсказаний по всем предсказываемым типам продуктов:

```
WITH fh_mm AS (
    SELECT 
        time_series_id,
        MIN(mape_at_test) as min_mape 
    FROM forecasting_history
    WHERE date = (SELECT MAX(date) FROM forecasting_history)
    GROUP BY time_series_id
),
fh AS (
    SELECT
        fh_.id,
        fh_.time_series_id
    FROM forecasting_history fh_
    JOIN fh_mm ON fh_.time_series_id = fh_mm.time_series_id AND fh_.mape_at_test = fh_mm.min_mape
    WHERE date = (SELECT MAX(date) FROM forecasting_history)
)
SELECT 
    pp.id, 
    fh.time_series_id,
    pp.date,
    pp.price
FROM predicted_prices pp
JOIN fh on fh.id = pp.forecasting_id
```

## Получение прогнозов через API

Для получения прогноза реализовано 3 эндпойнта:

1. Отправка задачи для получения прогноза:

```bash
curl -u "user:password" -X POST "http://localhost:81/predict" \
-H "accept: application/json" \
-H "Content-Type: multipart/form-data" \
-F "file=@api_predictions.xlsx" \
-F "sheet_name=beef" \
-F "date_name=date" \
-F "series_name=prod" \
-F "forecasting_steps=5" \
-F "year_limit=7" \
-F "use_only_light_models=False" \
-F "train_n_epochs=20" \
-F "data_frequency=WM" \
-F "sesoanal_period=12"
```

- `sheet_name` - название вкладки, в которой находится числовой ряд
- `date_name` - название столбца с датами
- `series_name` - название столбца со значениями числового ряда
- `forecasting_steps` - число шагов на которое нужно сделать предсказание, если данные в файле указываются с интервалом
  в месяц то будет сделан прогноз на 6 месяцев
- `year_limit` - _**!!НЕ**обязательный параметр_: минимальное значение 3, лучше указывать 5 и больше.
- `train_n_epochs` - _**!!НЕ**обязательный параметр_: устанавливает количество эпох при обучении NeuralProphet модели,
  чем меньше точек данных в датасете, тем большим должно быть количество эпох, например для датасета с 150 точками
  данных достаточно 30-40 эпох. Если параметр не указан, количество эпох будет подобрано автоматически - *
  *предпочитаемый вариант**
- `use_only_light_models` - Использование только быстрых моделей для предсказания. Если результаты предсказания нужно
  получить быстро, то лучше проставлять True, если нужны более точные предсказания, то False (время для предсказания
  увеличится значительно). При `True` запускаются только Exponential smoothing, Prophet и ThetaModel. При `False`
  дополнительно запускаются NeuralProphet и TimesFM.
- `data_frequency` - Частотность данных
- `sesoanal_period` - Длина сезонного периода

Запрос возвращает `{"task_id":"34d316f0-8002-4731-83ac-aa0be5f65781"}` - id задачи для составления прогноза

2. Запрос для получения статуса прогноза

```bash 
curl -u "user:password" -X GET "http://localhost:81/status/34d316f0-8002-4731-83ac-aa0be5f65781"
```

возвращает

`{'status': 'PENDING'}` - если задача ещё не выполнена

`{'status': 'SUCCESS'}` - если задача выполнена

`{'status': 'FAILURE'}` - если при выполнении задачи произошла ошибка

3. При получении `{'status': 'SUCCESS'}` нужно отправить запрос для получения результата:

```bash
curl -u "user:password" -X GET "http://localhost:81/result/34d316f0-8002-4731-83ac-aa0be5f65781"
```

возвращает результаты прогноза `{"result":{"values":[32.34, ... ,39.546,40.5,43.1]}}`
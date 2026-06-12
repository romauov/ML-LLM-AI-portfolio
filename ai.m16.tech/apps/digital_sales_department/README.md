
# Digital sales department

## Поиск клиентов для отдела продаж

### Датасет
Статистика событий пользователей сгруппированная по интервалам.


### Команды
Загрузка датасета из базы данных\
`python -m digital_sales_department.run download-db`\
Обучение модели\
`python -m digital_sales_department.run train`\
Проверка модели\
`python -m digital_sales_department.run test`

Просмотр логов\
`tensorboard --logdir lightning_logs`
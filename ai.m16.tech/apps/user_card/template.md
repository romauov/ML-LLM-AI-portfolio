# {{last_name}} {{first_name}}
<img src="https://{{site}}.ru/{{userid}}/data/profile/{{userid}}/avatar/large.webp"/>

userId: [{{userid}}](https://{{site}}.ru/people/view?user={{userid}})

site: {{site}}

Должность: {{position}}

Указанная деятельность: {{specified_activity}}
{% if user_active %}
Пользователь активен

Последнее действие: {{last_date}}
{% else %}
Пользователь не активен
{% endif %}
Пользователь зарегистрирован: {{add_date}}
# Контакты
email: {{user_email}}
{% for col in user_contacts.columns %}
{{col}}: {{user_contacts[col].values[0]}}
{% endfor %}

{% if company_status %}
# Информация о компании
{% else %}
# информация о компании отсутствует
{% endif %}
{% if company_title %}
Название: {{company_title}}
{% endif %}
{% if company_inn %}
ИНН: {{company_inn}}
{% endif %}
{% if description_ru %}
Описание: {{description_ru}}
{% endif %}
{% if company_link %}
Ссылка на компанию: {{company_link}}
{% endif %}
{% if company_leader %}
Руководитель: {{company_leader}}
{% endif %}
{% if company_logo %}
Логотип компании: {{company_logo}}
{% endif %}

# Последние объявления
{{last_trades}}
# Топ действий
Сводка о действиях пользователя {{userid}} на сайте {{site}} за последний год
{{top_actions}}
# Топ продуктов
{% if top_products_for_sellers.sum() > 0 %}
Сводка о продуктах, которые продавал пользователь {{userid}} на сайте {{site}} за последний год
{{top_products_for_sellers.to_markdown()}}
{% endif %}
{% if top_products_for_buyers.sum() > 0 %}
Сводка о продуктах, которые покупал пользователь {{userid}} на сайте {{site}} за последний год
{{top_products_for_buyers.to_markdown()}}
{% endif %}
{% if top_products_watched.sum() > 0 %}
Сводка о продуктах, которые просматривал пользователь {{userid}} на сайте {{site}} за последний год
{{top_products_watched.to_markdown()}}
{% endif %}
Количество просмотренных объявлений о покупке: {{buy_ads_watched}}

Количество просмотренных объявлений о продаже: {{sell_ads_watched}}

Количество других просмотренных объявлений: {{other_ads_watched}}

Количество выставленных объявлений о покупке: {{buy_ads_posted}}

Количество выставленных объявлений о продаже: {{sell_ads_posted}}

Количество других выставленных объявлений: {{other_ads_posted}}

# Лидовые действия пользователя
Последние взаимодействия пользователя {{userid}} с другими пользователями на сайте {{site}} за последний год
{{user_lead_actions}}
# Пользовательские просмотры
Объявления, которые просматривал пользователь {{userid}} на сайте {{site}} за последний год
{{user_search_actions}}
# Обращения к пользователю
Пользователи, которые обращались к пользователю {{userid}} на сайте {{site}} за последний год
{{lead_ids}}
## действия пользователей
{{leads_to_user}}
# Просмотры пользователя
Пользователи, которые смотрели объявления пользователя {{userid}} на сайте {{site}} за последний год
{{view_ids}}
## действия пользователей
{{searches_to_user}}

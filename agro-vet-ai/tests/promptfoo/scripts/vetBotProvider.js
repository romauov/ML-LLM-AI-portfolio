/**
 * Провайдер для локальной модели
 * Сохраните как localProvider.js в папке с promptfooconfig.yaml
 */

module.exports = class LocalModelProvider {
  constructor(options) {
    this.providerId = options?.id || 'local-model';
    this.config = options?.config || {};
  }

  id() {
    return this.providerId;
  }

  async callApi(prompt, context) {
    const { query } = context.vars;

    try {
      const requestBody = {
        message: query,
      };
      // ВЫВОДИМ В КОНСОЛЬ ТЕЛО ЗАПРОСА
      // console.log('\n>>>>> Отправляем на API:', JSON.stringify(requestBody, null, 2));

      const response = await fetch(`http://localhost:${process.env.API_SERVICE_HOST_PORT || 80}/api/submit_json`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${process.env.API_KEY}`,
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        const errorBody = await response.text();
        return {
          error: `HTTP ${response.status}: ${response.statusText}. Body: ${errorBody}`,
        };
      }

      const data = await response.json();
      // ВЫВОДИМ В КОНСОЛЬ ПОЛУЧЕННЫЙ ОТВЕТ
      // console.log('<<<<< Получено от API:', JSON.stringify(data, null, 2));

      // Сохраняем context в vars для отображения в колонке
      if (context.vars) {
        context.vars.context = data.context || "";
      }

      // Возвращаем response как строку - это будет отображаться в outputs
      return {
        output: data.response || "",
        context: data.context || "",
      };

    } catch (error) {
      return {
        error: error.message,
      };
    }
  }
};
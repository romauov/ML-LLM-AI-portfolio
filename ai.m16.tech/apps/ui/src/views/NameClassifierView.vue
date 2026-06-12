<script setup lang="ts">
import { reactive, ref } from "vue"
import axios from "axios"

const loading = ref<boolean>(false)
const text = ref<string>("")
const results = reactive({
  value: {
    name: "",
    date: "",
    label: "",
    error: "",
  },
})

const detect = async () => {
  loading.value = true
  const res = await axios.get("/api/name_classifier?name=" + text.value)
  results.value = res.data
  loading.value = false
}
</script>
<template>
  <div class="name">
    <h2>Валидатор имён</h2>
    <br />
    <div>
      Разработан для проверки введенного имени пользователем
      <br />Модель способна отсортировать нецензурные слова, слова, которые не
      относятся к именам, случайные последовательности <br />Модель построена на
      основе рекуррентных и сверточных слоёв <br /><br />
      <b> Пример работы: </b>
    </div>

    <div class="examples">
      <table>
        <tr>
          <th>Введенное значение</th>
          <th>Результат</th>
        </tr>
        <tr>
          <td>Николай</td>
          <td>Прошло проверку</td>
        </tr>
        <tr>
          <td>132g12</td>
          <td>Не прошло проверку</td>
        </tr>
        <tr>
          <td>Чайник</td>
          <td>Не прошло проверку</td>
        </tr>
        <tr>
          <td>Если оставить поле пустым</td>
          <td>Имя не введено</td>
        </tr>
      </table>
    </div>

    <textarea
      v-model="text"
      :disabled="loading"
      class="form-control"
      rows="1"
      cols="10"
    ></textarea>
    <br />

    <button class="btn btn-secondary" :disabled="loading" @click="detect()">
      Классифицировать
    </button>

    <div class="result">
      <table class="el-table">
        <div v-if="results.value['error']">
          <tr>
            <th>Ошибка</th>
          </tr>
          <tr>
            <td>
              {{ results.value["error"] }}
            </td>
          </tr>
        </div>

        <div v-else>
          <tr>
            <th>Имя</th>
            <th>Определенный класс</th>
          </tr>
          <tr>
            <td>
              {{ results.value["name"] }}
            </td>
            <td>
              {{
                results.value["label"]
                  ? "Прошло проверку"
                  : "Не прошло проверку"
              }}
            </td>
          </tr>
        </div>
      </table>
    </div>
  </div>
</template>

<style>
.result {
  margin-top: 50px;
}

.examples {
  text-align: "center";
  margin: 10px 10px 20px 33%;
}

.result td {
  padding: 10px;
  min-width: 100px;
  text-align: "center";
}
</style>

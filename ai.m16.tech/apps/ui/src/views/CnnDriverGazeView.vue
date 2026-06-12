<script setup lang="ts">
import axios from "axios"
import { reactive, ref } from "vue"

const loading = ref<boolean>(false)
const text = ref<string>("")
const results = reactive({
  value: {
    "upper left part of the windshield": "",
    straight: "",
    speedometer: "",
    radio: "",
    "upper right part of the windshield": "",
    "bottom right part of the windshield": "",
    "right side mirror": "",
    "rear view mirror": "",
    "left side mirror": "",
  },
})

const detect = async () => {
  loading.value = true
  const res = await axios.get(
    "/api/cnn_based_driver_gaze_predictor?image_path=" + text.value,
  )
  results.value = res.data
  loading.value = false
}
</script>
<template>
  <div class="product">
    <h2>Модель сверточной сети для определения направления взгляда водителя</h2>
    <br />
    <h5>Примеры тестовых изображений</h5>
    <span>https://disk.yandex.ru/i/yTZWHD_CJeLe8w</span>
    <br />
    <span>https://disk.yandex.ru/i/eU5IrD3Rnm8v_A</span>
    <br />
    <span>https://disk.yandex.ru/i/cQ985sxHOzHLbg</span>
    <br />
    <span>https://disk.yandex.ru/i/OyY_2ZFoZKQePA</span>
    <br />
    <span>https://disk.yandex.ru/i/vQ9vN93eZEUKGg</span>
    <div v-text="testTarget" style="height: 30px; margin-top: 5px"></div>
    <textarea
      v-model="text"
      :disabled="loading"
      class="form-control"
      rows="1"
      cols="50"
    ></textarea>
    <br />
    <button class="btn btn-secondary" :disabled="loading" @click="detect()">
      Определить направление взгляда
    </button>
    <div class="result">
      <table class="el-table">
        <tr>
          <th>Лев. верхн. часть лоб. стекла</th>
          <th>Прямо</th>
          <th>Спидометр</th>
          <th>Радио</th>
          <th>Прав. верхн. часть лоб. стекла</th>
          <th>Прав. нижн часть лоб. стекла</th>
          <th>Прав. бок. зерк.</th>
          <th>Зеркало задн. вида</th>
          <th>Лев. бок. зерк</th>
        </tr>

        <tr>
          <td>
            {{ results.value["upper left part of the windshield"] }}
          </td>
          <td>
            {{ results.value["straight"] }}
          </td>
          <td>
            {{ results.value["speedometer"] }}
          </td>
          <td>
            {{ results.value["radio"] }}
          </td>
          <td>
            {{ results.value["upper right part of the windshield"] }}
          </td>
          <td>
            {{ results.value["bottom right part of the windshield"] }}
          </td>
          <td>
            {{ results.value["right side mirror"] }}
          </td>
          <td>
            {{ results.value["rear view mirror"] }}
          </td>
          <td>
            {{ results.value["left side mirror"] }}
          </td>
        </tr>
      </table>
    </div>
  </div>
</template>

<style scoped>
.result {
  margin-top: 50px;
}

.result td {
  padding: 10px;
  min-width: 70px;
  text-align: center;
}
</style>

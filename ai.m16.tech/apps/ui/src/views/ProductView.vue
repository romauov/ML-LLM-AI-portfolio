<script setup lang="ts">
import axios from "axios"
import { reactive, ref } from "vue"

const objectResult = () => ({
  mtype: "",
  part: "",
  ice_status: "",
  gost: "",
  ty: "",
})

const listModels = ["cointegrated/rubert-tiny", "cointegrated/rubert-tiny2"]

const loading = ref<boolean>(false)
const text = ref<string>("")
const testTarget = ref<string>("")
const results = reactive(
  listModels.map((modelName) => ({ name: modelName, result: objectResult() })),
)

const testText = async () => {
  const res = await axios.post("/api/product/test-text")
  const result = res.data
  text.value = result.text
  testTarget.value =
    result.mtype +
    ", " +
    result.part +
    ", " +
    result.ice_status +
    ", " +
    result.gost +
    ", " +
    result.ty
}

const detect = async (index: number, model: string) => {
  loading.value = true
  const form = new FormData()
  form.append("text", text.value)
  form.append("model", model)
  const res = await axios.post("/api/product/product-detect", form)
  results[index].result = res.data
  loading.value = false
}
</script>
<template>
  <div class="product">
    <h2>Модель сети для определения продукции</h2>
    <br />
    <button class="btn btn-secondary" :disabled="loading" @click="testText()">
      Случайный образец
    </button>
    <div v-text="testTarget" style="height: 30px; margin-top: 5px"></div>
    <textarea
      v-model="text"
      :disabled="loading"
      class="form-control"
      rows="5"
      cols="50"
    ></textarea>

    <div class="result">
      <table class="el-table">
        <tr>
          <th>Модель</th>
          <th>Вид</th>
          <th>Разруб</th>
          <th>Терм. сост</th>
          <th>Гост</th>
          <th>Ту</th>
        </tr>

        <tr v-for="(item, index) in results" :key="index">
          <td class="el-table__cell">
            <button
              v-text="item.name"
              :disabled="loading"
              class="btn btn-outline-secondary"
              @click="detect(index, item.name)"
            />
          </td>
          <td
            v-for="(type, typeIndex) in Object.keys(item.result)"
            :key="typeIndex"
            class="el-table__cell"
          >
            <div v-if="item.result[type]">
              <div v-text="item.result[type].value"></div>
              <div v-text="item.result[type].proba"></div>
            </div>
          </td>
        </tr>
      </table>
    </div>
  </div>
</template>
<style scoped>
.product {
  max-width: 800px;
  margin: auto;
}

.result {
  margin-top: 50px;
}

.result td {
  padding: 10px;
  min-width: 70px;
  text-align: center;
}
</style>

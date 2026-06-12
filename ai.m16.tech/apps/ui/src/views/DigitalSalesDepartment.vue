<script setup lang="ts">
import axios from "axios"
import { reactive, ref } from "vue"
import { arrayToXlsx } from "@/lib/exceljs"

interface UserResult {
  user_id: number
  name: string
  email: string
  date: string
  link: string
}

const loading = ref(false)
const result = reactive<{ items: UserResult[] }>({ items: [] })

const inputSite = ref("meatinfo")
const inputService = ref("Акселератор продаж")
const inputActivity = ref("1")

const send = async () => {
  loading.value = true
  const query = {
    site: inputSite.value,
    service: inputService.value,
    activity: parseInt(inputActivity.value),
  }
  const res = await axios.post(
    "/api/digital_sales_department/user_interest_active",
    query,
  )
  result.items = res.data.map((it: any) => ({
    user_id: it.user_id,
    name: it.info.firstname + " " + it.info.lastname,
    email: it.info.email,
    date: it.info.date,
    link: "https://axe.m16.tech/razmetka?user_login=" + it.info.email,
  }))
  loading.value = false
}

const download = async () => {
  loading.value = true
  const rows = result.items.map(item => [
    item.name,
    item.email,
    item.link,
    "https://" + inputSite.value + ".ru/people/view?user=" + item.user_id,
  ])
  const fileName = inputService.value + ".xlsx"
  await arrayToXlsx(fileName, rows)
  loading.value = false
}

</script>

<template>
  <h1>Digital sales department</h1>

  <CContainer class="my-5">
    <CRow>
      <CCol xs>
        <CFormSelect v-model="inputSite" label="Сайт" :options="['meatinfo']">
        </CFormSelect>
      </CCol>
      <CCol xs>
        <CFormSelect
          v-model="inputService"
          label="Услуги"
          :options="['Акселератор продаж']"
        >
        </CFormSelect>
      </CCol>
      <CCol xs>
        <CFormSelect
          v-model="inputActivity"
          label="Активность (Недель)"
          :options="['1', '2', '3', '4', '5']"
        >
        </CFormSelect>
      </CCol>
      <CCol xs class="col-btn">
        <CButton
          v-text="'Сгенерировать список'"
          :disabled="loading"
          color="primary"
          @click="send()"
        />
      </CCol>
    </CRow>
    <CRow v-if="result.items.length > 0" class="mt-2" style="text-align: right;">
      <CCol xs>
      </CCol>
      <CCol xs class="col-btn">
        <CButton
          v-text="'Загрузить Excel'"
          :disabled="loading"
          color="light"
          @click="download()"
        />
      </CCol>
    </CRow>
  </CContainer>

  <div v-if="result.items.length > 0">
    <CTable striped>
      <CTableHead>
        <CTableRow>
          <CTableHeaderCell scope="col">#</CTableHeaderCell>
          <CTableHeaderCell scope="col">Имя</CTableHeaderCell>
          <CTableHeaderCell scope="col">Email</CTableHeaderCell>
          <CTableHeaderCell scope="col">Активность</CTableHeaderCell>
          <CTableHeaderCell scope="col"></CTableHeaderCell>
        </CTableRow>
      </CTableHead>
      <CTableBody>
        <CTableRow v-for="item in result.items" :key="item.user_id">
          <CTableHeaderCell scope="row">{{ item.user_id }}</CTableHeaderCell>
          <CTableDataCell>{{ item.name }}</CTableDataCell>
          <CTableDataCell>{{ item.email }}</CTableDataCell>
          <CTableDataCell>{{ item.date }}</CTableDataCell>
          <CTableDataCell>
            <a rel="stylesheet" :href="item.link" target="_blank"> axe </a>
          </CTableDataCell>
        </CTableRow>
      </CTableBody>
    </CTable>
  </div>
</template>
<style scoped>
.col-btn button {
  width: 200px;
}
.col-btn {
  align-self: flex-end;
  text-align: right;
}
</style>

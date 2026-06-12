import { createRouter, createWebHistory, RouteRecordRaw } from "vue-router"
import ProductView from "../views/ProductView.vue"
import CnnDriverGazeView from "../views/CnnDriverGazeView.vue"
import NameClassifierView from "../views/NameClassifierView.vue"
import DigitalSalesDepartment from "../views/DigitalSalesDepartment.vue"
import DefaultLayout from "@/layouts/DefaultLayout.vue"
import AppLayout from "@/layouts/AppLayout.vue"
import IndexView from "@/views/IndexView.vue"

const routes: Array<RouteRecordRaw> = [
  {
    path: "/",
    name: "index",
    component: DefaultLayout,
    children: [
      {
        path: "/",
        name: "index",
        component: IndexView,
      },
      {
        path: "/product",
        name: "product",
        component: ProductView,
      },
      {
        path: "/cnn_driver_gaze",
        name: "cnn_driver_gaze",
        component: CnnDriverGazeView,
      },
      {
        path: "/name_classifier",
        name: "name_classifier",
        component: NameClassifierView,
      },
    ],
  },
  {
    path: "/dsd",
    name: "dsd",
    component: AppLayout,
    children: [
      {
        path: "/dsd/digital_sales_department",
        name: "digital_sales_department",
        component: DigitalSalesDepartment,
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes,
})

export default router

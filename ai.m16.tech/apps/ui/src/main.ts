import { createApp } from "vue"
import App from "./App.vue"
import router from "./router"
import store from "./store"
import CoreuiVue from "@coreui/vue"

import "@coreui/coreui/dist/css/coreui.min.css"
import "bootstrap/dist/css/bootstrap.min.css"

createApp(App).use(CoreuiVue).use(store).use(router).mount("#app")

import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import Players   from '../views/Players.vue'

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/',        name: 'Dashboard', component: Dashboard },
    { path: '/players', name: 'Players',   component: Players   },
  ],
})

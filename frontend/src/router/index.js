import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import Players   from '../views/Players.vue'
import Sentiment from '../views/Sentiment.vue'

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/',          name: 'Dashboard', component: Dashboard  },
    { path: '/players',   name: 'Players',   component: Players    },
    { path: '/sentiment', name: 'Sentiment', component: Sentiment  },
  ],
})

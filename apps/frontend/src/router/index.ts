import { createRouter, createWebHistory } from 'vue-router';
import HomeView from '../views/HomeView.vue';

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
    {
      path: '/no-session-id-provided',
      name: 'no session id provided',
      component: () => import('../views/NoSessionIdProvided.vue'),
    },
    {
      path: '/unknown-user',
      name: 'unknown user',
      component: () => import('../views/UnknownUser.vue'),
    },
  ],
});

export default router;

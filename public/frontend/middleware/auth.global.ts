import { useUserStore } from '~/stores/user'

export default defineNuxtRouteMiddleware((to, from) => {
  const userStore = useUserStore()
  if (!userStore.user && to.path !== '/login' && to.path !== '/register') {
    return navigateTo('/login')
  }
})
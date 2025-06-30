import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useNuxtApp } from '#app'
import { onAuthStateChanged } from 'firebase/auth'

export const useUserStore = defineStore('user', () => {
  const user = ref(null)
  const idToken = ref(null)
  const { $firebaseAuth } = useNuxtApp()

  onAuthStateChanged($firebaseAuth, async (u) => {
    user.value = u
    idToken.value = u ? await u.getIdToken() : null
  })

  const logout = async () => {
    await $firebaseAuth.signOut()
    user.value = null
    idToken.value = null
  }

  return { user, idToken, logout }
})
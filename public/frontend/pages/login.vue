//login page for a Vue.js application using Firebase Auth

<template>
  <div>
    <h1>Login</h1>
    <form @submit.prevent="login">
      <input v-model="email" type="email" placeholder="Email" required />
      <input v-model="password" type="password" placeholder="Password" required />
      <button type="submit">Login</button>
    </form>
    <div v-if="error" style="color: red;">{{ error }}</div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useNuxtApp } from '#app'

const { $firebaseAuth } = useNuxtApp()
const email = ref('')
const password = ref('')
const error = ref('')

const login = async () => {
  error.value = ''
  try {
    await $firebaseAuth.signInWithEmailAndPassword(email.value, password.value)
    window.location.href = '/'
  } catch (e: any) {
    error.value = e.message
  }
}
</script>

// User login page

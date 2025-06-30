// Registration page for a Vue.js application using Firebase Auth and Firestore
<template>
  <div>
    <h1>Register</h1>
    <form @submit.prevent="register">
      <input v-model="email" type="email" placeholder="Email" required />
      <input v-model="password" type="password" placeholder="Password" required />
      <button type="submit">Register</button>
    </form>
    <div v-if="error" style="color: red;">{{ error }}</div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useNuxtApp } from '#app'
import { doc, setDoc } from 'firebase/firestore'

const { $firebaseAuth, $firebaseDb } = useNuxtApp()
const email = ref('')
const password = ref('')
const error = ref('')

const register = async () => {
  error.value = ''
  try {
    const userCredential = await $firebaseAuth.createUserWithEmailAndPassword(email.value, password.value)
    const user = userCredential.user
    await setDoc(doc($firebaseDb, 'users', user.uid), {
      email: user.email,
      topics: []
    })
    window.location.href = '/login'
  } catch (e: any) {
    error.value = e.message
  }
}
</script>

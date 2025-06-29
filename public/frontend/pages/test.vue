<template>
  <div>
    <h1>Firestore Test</h1>
    <div v-if="error" style="color: red;">Error: {{ error }}</div>
    <div v-else-if="testDocData">
      <pre>{{ testDocData }}</pre>
    </div>
    <div v-else>Loading...</div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useNuxtApp } from '#app'
import { doc, getDoc } from 'firebase/firestore'

const { $firebaseDb } = useNuxtApp()

const testDocData = ref<any>(null)
const error = ref<string | null>(null)

onMounted(async () => {
  try {
    const docRef = doc($firebaseDb, 'test', 'testDoc')
    const docSnap = await getDoc(docRef)
    if (docSnap.exists()) {
      testDocData.value = docSnap.data()
    } else {
      error.value = 'No such document!'
    }
  } catch (e: any) {
    error.value = e.message
  }
})
</script>
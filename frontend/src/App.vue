<template>
  <div id="app">
    <template v-if="route.path === '/login'">
      <router-view />
    </template>
    <Layout v-else>
      <router-view />
    </Layout>
  </div>
</template>

<script setup>
import { useRoute } from 'vue-router'
import Layout from './components/Layout.vue'

const route = useRoute()
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  margin: 0;
  padding: 0;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  margin: 0;
  padding: 0;
}
</style>
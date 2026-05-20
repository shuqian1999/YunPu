<template>
  <el-tooltip content="切换主题" placement="bottom">
    <el-switch
      v-model="isDark"
      inline-prompt
      :active-icon="Moon"
      :inactive-icon="Sunny"
      @change="handleThemeChange"
    />
  </el-tooltip>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Moon, Sunny } from '@element-plus/icons-vue'

const isDark = ref(false)

const handleThemeChange = (value) => {
  if (value) {
    document.documentElement.classList.add('dark')
    localStorage.setItem('theme', 'dark')
  } else {
    document.documentElement.classList.remove('dark')
    localStorage.setItem('theme', 'light')
  }
}

onMounted(() => {
  const savedTheme = localStorage.getItem('theme')
  if (savedTheme === 'dark') {
    isDark.value = true
    document.documentElement.classList.add('dark')
  } else if (!savedTheme && window.matchMedia('(prefers-color-scheme: dark)').matches) {
    // 如果没有保存的主题，且系统偏好为深色
    isDark.value = true
    document.documentElement.classList.add('dark')
    localStorage.setItem('theme', 'dark')
  }
})
</script>

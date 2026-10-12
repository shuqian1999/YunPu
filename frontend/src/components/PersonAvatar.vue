<template>
  <el-avatar
    :size="size"
    :src="imgSrc || undefined"
    :class="['person-avatar', { 'is-fallback': !imgSrc }]"
    :style="fallbackStyle"
  >
    {{ text }}
  </el-avatar>
</template>

<script setup>
import { computed } from 'vue'
import { avatarText, avatarColor } from '@/utils/avatar'

const props = defineProps({
  // 传人物对象
  person: { type: Object, default: null },
  // 或直接传名字 / 图片地址
  name: { type: String, default: '' },
  src: { type: String, default: '' },
  size: { type: [Number, String], default: 40 }
})

const imgSrc = computed(() => props.src || props.person?.avatar_url || '')

const text = computed(() => {
  if (props.person) return avatarText(props.person)
  const n = (props.name || '').trim()
  return n ? n.charAt(0) : '?'
})

const fallbackStyle = computed(() => {
  if (imgSrc.value) return {}
  return {
    backgroundColor: avatarColor(text.value),
    color: '#ffffff',
    fontWeight: 'var(--font-weight-semibold, 600)'
  }
})
</script>

<style scoped>
.person-avatar.is-fallback {
  flex-shrink: 0;
  user-select: none;
}
</style>

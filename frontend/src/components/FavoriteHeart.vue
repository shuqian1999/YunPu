<template>
  <el-tooltip :content="modelValue ? '取消关注' : '关注'" placement="top">
    <button
      type="button"
      class="favorite-heart"
      :class="{ active: modelValue }"
      :disabled="loading"
      :aria-label="modelValue ? '取消关注' : '关注'"
      @click.stop="toggle"
    >
      <svg
        :width="size"
        :height="size"
        viewBox="0 0 24 24"
        :fill="modelValue ? '#f56c6c' : 'none'"
        :stroke="modelValue ? '#f56c6c' : '#a8abb2'"
        stroke-width="2"
        stroke-linejoin="round"
      >
         <path
          d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"
        />
      </svg>
    </button>
  </el-tooltip>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { updatePerson } from '@/api/persons'

const props = defineProps({
  personId: { type: Number, required: true },
  modelValue: { type: Boolean, default: false },
  size: { type: Number, default: 20 }
})

const emit = defineEmits(['update:modelValue', 'change'])

const loading = ref(false)

const toggle = async () => {
  if (loading.value) return
  const next = !props.modelValue
  loading.value = true
  try {
    await updatePerson(props.personId, { is_favorite: next })
    emit('update:modelValue', next)
    emit('change', next)
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '操作失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.favorite-heart {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 4px;
  border: none;
  background: transparent;
  cursor: pointer;
  border-radius: 50%;
  line-height: 0;
  transition: transform 0.15s ease;
}

.favorite-heart:hover {
  background: var(--el-fill-color-light, #f5f7fa);
}

.favorite-heart:active {
  transform: scale(0.85);
}

.favorite-heart svg {
  transition: fill 0.15s ease, stroke 0.15s ease;
}

.favorite-heart.active:hover svg {
  opacity: 0.8;
}

.favorite-heart:disabled {
  cursor: wait;
  opacity: 0.6;
}
</style>

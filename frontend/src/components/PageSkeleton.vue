<template>
  <div class="page-skeleton" :class="`variant-${variant}`" aria-label="加载中" aria-busy="true">
    <!-- 仪表盘：统计卡 + 今日聚焦 + 两大栏 -->
    <template v-if="variant === 'dashboard'">
      <div class="sk-focus sk-block" />
      <div class="sk-stats">
        <div v-for="i in 3" :key="i" class="sk-block sk-stat" />
      </div>
      <div class="sk-dashboard-body">
        <div class="sk-block sk-timeline">
          <div v-for="i in 5" :key="i" class="sk-row">
            <div class="sk-dot sk-block" />
            <div class="sk-lines">
              <div class="sk-block sk-line w-60" />
              <div class="sk-block sk-line w-90" />
            </div>
          </div>
        </div>
        <div class="sk-block sk-side">
          <div v-for="i in 4" :key="i" class="sk-block sk-line w-80" />
        </div>
      </div>
    </template>

    <!-- 人物卡片网格 -->
    <template v-else-if="variant === 'person-grid'">
      <div class="sk-person-grid">
        <div v-for="i in 8" :key="i" class="sk-block sk-person">
          <div class="sk-avatar sk-block" />
          <div class="sk-block sk-line w-70" />
          <div class="sk-block sk-line w-40" />
        </div>
      </div>
    </template>

    <!-- 分组卡片 -->
    <template v-else-if="variant === 'groups'">
      <div v-for="i in 3" :key="i" class="sk-block sk-group">
        <div class="sk-block sk-line w-30" />
        <div class="sk-chips">
          <div v-for="j in 5" :key="j" class="sk-chip sk-block" />
        </div>
      </div>
    </template>

    <!-- 通用行列表（代际/提醒等） -->
    <template v-else>
      <div v-for="i in rows" :key="i" class="sk-list-item">
        <div class="sk-avatar sk-block" />
        <div class="sk-lines">
          <div class="sk-block sk-line w-50" />
          <div class="sk-block sk-line w-80" />
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
defineProps({
  variant: {
    type: String,
    default: 'list', // dashboard | person-grid | groups | list
    validator: (v) => ['dashboard', 'person-grid', 'groups', 'list'].includes(v)
  },
  rows: { type: Number, default: 6 }
})
</script>

<style scoped>
.page-skeleton {
  width: 100%;
}

.sk-block {
  background: linear-gradient(
    90deg,
    var(--bg-color-light, #f2f3f5) 25%,
    var(--border-lighter, #e8eaed) 37%,
    var(--bg-color-light, #f2f3f5) 63%
  );
  background-size: 400% 100%;
  animation: sk-shimmer 1.4s ease infinite;
  border-radius: 8px;
}

:global(.dark) .sk-block {
  background: linear-gradient(
    90deg,
    rgba(255, 255, 255, 0.04) 25%,
    rgba(255, 255, 255, 0.09) 37%,
    rgba(255, 255, 255, 0.04) 63%
  );
  background-size: 400% 100%;
}

@keyframes sk-shimmer {
  0% { background-position: 100% 50%; }
  100% { background-position: 0 50%; }
}

/* 通用线条 */
.sk-line { height: 14px; margin: 6px 0; }
.w-30 { width: 30%; }
.w-40 { width: 40%; }
.w-50 { width: 50%; }
.w-60 { width: 60%; }
.w-70 { width: 70%; }
.w-80 { width: 80%; }
.w-90 { width: 90%; }

.sk-avatar {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  flex-shrink: 0;
}

.sk-row,
.sk-list-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px 4px;
}

.sk-lines { flex: 1; }

/* dashboard */
.sk-focus { height: 96px; border-radius: 12px; margin-bottom: 16px; }
.sk-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}
.sk-stat { height: 96px; border-radius: 12px; }
.sk-dashboard-body {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 16px;
}
.sk-timeline,
.sk-side {
  min-height: 320px;
  padding: 16px;
  border-radius: 12px;
}
.sk-side { display: flex; flex-direction: column; justify-content: space-evenly; }
.sk-dot { width: 12px; height: 12px; border-radius: 50%; }
.sk-timeline .sk-row { gap: 12px; }
.sk-timeline .sk-avatar { width: 36px; height: 36px; }

/* person grid */
.sk-person-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 16px;
}
.sk-person {
  padding: 24px 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  border-radius: 12px;
}
.sk-person .sk-avatar { width: 72px; height: 72px; }
.sk-person .sk-line { margin: 2px 0; text-align: center; }
.sk-person .w-70 { width: 70%; }
.sk-person .w-40 { width: 40%; }

/* groups */
.sk-group {
  padding: 20px;
  border-radius: 12px;
  margin-bottom: 16px;
}
.sk-chips { display: flex; gap: 10px; margin-top: 16px; flex-wrap: wrap; }
.sk-chip { width: 88px; height: 28px; border-radius: 14px; }

/* list */
.variant-list .sk-list-item {
  padding: 14px 8px;
  border-bottom: 1px solid var(--border-lighter, #f0f2f5);
}

@media (max-width: 768px) {
  .sk-stats { grid-template-columns: repeat(3, 1fr); gap: 10px; }
  .sk-stat { height: 76px; }
  .sk-dashboard-body { grid-template-columns: 1fr; }
  .sk-person-grid { grid-template-columns: repeat(2, 1fr); gap: 10px; }
  .sk-person { padding: 16px 10px; }
  .sk-person .sk-avatar { width: 56px; height: 56px; }
}
</style>

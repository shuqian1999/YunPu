<template>
  <div class="person-card" @click="$emit('view', person.id)">
    <div class="person-avatar">
      <el-avatar :size="80" :src="person.avatar_url">
        {{ person.first_name || person.nickname || '?' }}
      </el-avatar>
    </div>

    <div class="person-info">
      <div class="person-name">
        {{ person.last_name }}{{ person.first_name }}
      </div>
      <div v-if="person.nickname" class="person-nickname">
        {{ person.nickname }}
      </div>
      <div v-if="ageText" class="person-age">
        {{ ageText }}
      </div>

      <div v-if="person.birth_date" class="person-birthday">
        <el-icon><Calendar /></el-icon>
        <span class="birthday-label">生日</span>
        <span class="birthday-date">{{ formatBirthday(person.birth_date) }}</span>
        <el-tag v-if="person.is_lunar_birth" size="small" type="warning" class="lunar-tag">
          农历
        </el-tag>
      </div>

      <div v-if="person.death_date" class="person-deathday">
        <el-icon><Moon /></el-icon>
        <span class="deathday-label">忌日</span>
        <span class="deathday-date">{{ formatBirthday(person.death_date) }}</span>
        <el-tag v-if="person.is_lunar_death" size="small" type="warning" class="lunar-tag">
          农历
        </el-tag>
      </div>

      <div v-if="countryName || person.residence" class="person-location">
        <span v-if="countryFlag" class="location-flag">{{ countryFlag }}</span>
        <span v-if="countryName" class="location-text">{{ countryName }}</span>
        <span v-if="countryName && person.residence" class="location-sep">·</span>
        <el-icon v-if="person.residence" class="location-icon"><Location /></el-icon>
        <span v-if="person.residence" class="location-text">{{ person.residence }}</span>
      </div>

      <div v-if="person.hometown && person.hometown !== person.residence" class="person-hometown">
        <el-icon><HomeFilled /></el-icon>
        <span>家乡：{{ person.hometown }}</span>
      </div>

      <div class="person-tags">
        <el-tag v-if="person.is_me" type="primary" size="small">我</el-tag>
        <el-tag v-if="person.gender === 1" type="success" size="small">男</el-tag>
        <el-tag v-else-if="person.gender === 2" type="danger" size="small">女</el-tag>
        <el-tag v-if="person.death_date" type="info" size="small">已故</el-tag>
      </div>
    </div>

    <div class="person-actions">
      <el-button
        v-if="!person.is_me"
        type="danger"
        text
        size="small"
        @click.stop="$emit('delete', person.id)"
      >
        删除
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Calendar, Moon, Location, HomeFilled } from '@element-plus/icons-vue'

const props = defineProps({
  person: { type: Object, required: true },
  getCountryName: { type: Function, required: true },
  getCountryFlag: { type: Function, required: true },
  getPersonAgeText: { type: Function, required: true },
  formatBirthday: { type: Function, required: true }
})

defineEmits(['view', 'delete'])

const countryName = computed(() => props.getCountryName(props.person.country))
const countryFlag = computed(() => props.getCountryFlag(props.person.country))
const ageText = computed(() => props.getPersonAgeText(props.person))
</script>

<style scoped>
.person-card {
  cursor: pointer;
  transition: all 0.3s ease;
  border-radius: 12px;
  background: var(--card-bg, #ffffff);
  border: 1px solid var(--border-color, #dcdfe6);
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 24px 16px;
}

.person-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
  transform: translateY(-2px);
  border-color: var(--primary-color, #409EFF);
}

.person-avatar {
  margin-bottom: 16px;
}

.person-info {
  text-align: center;
  flex: 1;
  width: 100%;
}

.person-name {
  font-size: 18px;
  font-weight: 500;
  color: var(--text-primary, #303133);
  margin-bottom: 4px;
}

.person-nickname {
  font-size: 14px;
  color: var(--text-secondary, #909399);
  margin-bottom: 8px;
}

.person-age {
  font-size: 13px;
  color: var(--el-color-primary, #409eff);
  margin-bottom: 8px;
  font-weight: 500;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.lunar-tag {
  font-size: 10px;
  height: 16px;
  padding: 0 4px;
  line-height: 16px;
}

.person-birthday,
.person-deathday {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  font-size: 13px;
  color: var(--text-regular, #606266);
  margin-bottom: 6px;
  line-height: 1.4;
}

.person-birthday .el-icon,
.person-deathday .el-icon {
  font-size: 13px;
  color: var(--text-secondary, #909399);
}

.birthday-label,
.deathday-label {
  color: var(--text-secondary, #909399);
}

.birthday-date,
.deathday-date {
  font-weight: 500;
  color: var(--text-primary, #303133);
}

.person-location {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  font-size: 13px;
  color: var(--text-regular, #606266);
  margin-bottom: 6px;
  max-width: 100%;
  flex-wrap: wrap;
  line-height: 1.4;
}

.location-flag {
  font-size: 14px;
  line-height: 1;
}

.location-icon {
  font-size: 12px;
  color: var(--text-secondary, #909399);
}

.location-text {
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.location-sep {
  color: var(--text-secondary, #c0c4cc);
  margin: 0 2px;
}

.person-hometown {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  font-size: 12px;
  color: var(--text-secondary, #909399);
  margin-bottom: 8px;
}

.person-hometown .el-icon {
  font-size: 12px;
}

.person-tags {
  display: flex;
  justify-content: center;
  gap: 4px;
  flex-wrap: wrap;
}

.person-tags .el-tag {
  margin: 0;
}

.person-actions {
  display: flex;
  gap: 8px;
  margin-top: 16px;
}
</style>

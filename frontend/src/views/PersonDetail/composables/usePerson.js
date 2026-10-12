import { ref, onMounted } from 'vue'
import { getPerson } from '@/api/persons'
import { getCountries } from '@/api/countries'
import { getEventTypes } from '@/api/event_types'
import { getGroups } from '@/api/groups'
import { getPersons } from '@/api/persons'

/**
 * 加载人物详情页共享数据：人物信息、国家、事件类型、可用人物列表、全部分组
 * @param {number|string} personId
 */
export function usePerson(personId) {
  const personInfo = ref({})
  const countries = ref({})
  const eventTypes = ref([])
  const allGroups = ref([])
  const availablePersons = ref([])
  const loading = ref(false)

  const loadSharedData = async (targetId = personId) => {
    loading.value = true
    try {
      const [personData, countriesData, eventTypesData, groupsData, personsData] = await Promise.all([
        getPerson(targetId),
        getCountries(),
        getEventTypes(),
        getGroups(),
        // 关系类对话框需要全量人物可选（后端默认 limit=20 仅适用于列表分页）
        getPersons({ skip: 0, limit: 100000 })
      ])

      personInfo.value = personData
      countries.value = countriesData
      eventTypes.value = eventTypesData
      allGroups.value = groupsData

      availablePersons.value = personsData
        .map(p => {
          const fullName = `${p.last_name || ''}${p.first_name || ''}`.trim()
          const nickname = (p.nickname || '').trim()
          const baseName = fullName || nickname || '未命名'
          // 选择器选项展示「姓名（称呼）」，filterable 可按任一字段检索
          const name = fullName && nickname && nickname !== fullName
            ? `${fullName}（${nickname}）`
            : baseName
          return { id: p.id, name, fullName: baseName, nickname }
        })
        .filter(p => p.id !== targetId)
    } catch (error) {
      console.error('加载共享数据失败:', error)
    } finally {
      loading.value = false
    }
  }

  onMounted(() => {
    loadSharedData()
  })

  return {
    personInfo,
    countries,
    eventTypes,
    allGroups,
    availablePersons,
    loading,
    loadSharedData
  }
}

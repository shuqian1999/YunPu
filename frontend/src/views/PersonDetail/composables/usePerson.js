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

  const loadSharedData = async () => {
    loading.value = true
    try {
      const [personData, countriesData, eventTypesData, groupsData, personsData] = await Promise.all([
        getPerson(personId),
        getCountries(),
        getEventTypes(),
        getGroups(),
        getPersons()
      ])

      personInfo.value = personData
      countries.value = countriesData
      eventTypes.value = eventTypesData
      allGroups.value = groupsData

      availablePersons.value = personsData
        .map(p => ({
          id: p.id,
          name: p.nickname || `${p.last_name || ''}${p.first_name || ''}`.trim() || '未命名'
        }))
        .filter(p => p.id !== personId)
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

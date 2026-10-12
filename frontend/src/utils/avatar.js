// 头像兜底：无头像图片时，用姓名首字 + 按名字稳定取色的色块

const AVATAR_PALETTE = [
  '#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#9B59B6',
  '#1ABC9C', '#36CFC9', '#FF85C0', '#5C7BD9', '#FF9F40'
]

/**
 * 获取人物头像应显示的首字：优先姓氏首字（如"张三"→"张"），其次名字/称呼
 */
export function avatarText(person) {
  if (!person) return '?'
  const source = person.last_name || person.first_name || person.nickname || ''
  const trimmed = String(source).trim()
  return trimmed ? trimmed.charAt(0) : '?'
}

/**
 * 根据字符串稳定计算一个色块颜色
 */
export function avatarColor(seed) {
  const key = String(seed || '?')
  let hash = 0
  for (let i = 0; i < key.length; i++) {
    hash = (hash * 31 + key.charCodeAt(i)) >>> 0
  }
  return AVATAR_PALETTE[hash % AVATAR_PALETTE.length]
}

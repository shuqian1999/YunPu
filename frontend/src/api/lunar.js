import request from '../utils/request'

// 公历转农历
export const convertToLunar = (dateStr) => {
  return request({
    url: '/lunar/convert',
    method: 'get',
    params: {
      date_str: dateStr
    }
  })
}

// 获取下一个农历生日
export const getNextLunarBirthday = (year, month, day, isLeap = false) => {
  return request({
    url: '/lunar/next-birthday',
    method: 'get',
    params: {
      year,
      month,
      day,
      is_leap: isLeap
    }
  })
}

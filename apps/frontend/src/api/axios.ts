import AXIOS from 'axios'

export const appAxios = AXIOS.create({
  baseURL: '/api'
})

import axios from 'axios'

const api = axios.create({ baseURL: '/api/v1' })

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (res) => res,
  async (err) => {
    if (err.response?.status === 401) {
      const detail = err.response.data?.detail;
      if (detail && typeof detail === "object" && detail.error_type === "invalid_api_key") {
        // Do not log out or redirect to login. This is a server configuration issue.
      } else {
        localStorage.removeItem('token')
        window.location.href = '/login'
        return Promise.reject(err)
      }
    }

    if (err.response?.data?.detail && typeof err.response.data.detail === "object") {
      const detail = err.response.data.detail;
      let msg = detail.message || "An LLM error occurred";
      if (detail.retry_after !== undefined && detail.retry_after !== null) {
        msg += ` Please try again in ${detail.retry_after} seconds.`;
      }
      err.response.data.detail = msg;
    }
    return Promise.reject(err)
  }
)

export default api

export function getErrorMessage(error: any, fallback: string): string {
  const detail = error?.response?.data?.detail;
  if (!detail) return fallback;
  if (typeof detail === "object" && detail !== null) {
    let msg = detail.message || JSON.stringify(detail);
    if (detail.retry_after !== undefined && detail.retry_after !== null) {
      msg += ` Please try again in ${detail.retry_after} seconds.`;
    }
    return msg;
  }
  return String(detail);
}

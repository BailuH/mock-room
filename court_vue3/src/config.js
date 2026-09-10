// Docker 构建时 VUE_APP_API_BASE_URL 注入为空串（同域反代）。
// 注意不能用 || 回退：空字符串是 falsy，会把 baseURL 又变成 localhost:8000。
const baseURL = process.env.VUE_APP_API_BASE_URL === undefined
  ? "http://localhost:8000"
  : process.env.VUE_APP_API_BASE_URL
//"http://82.157.203.240:8000"

export {baseURL}

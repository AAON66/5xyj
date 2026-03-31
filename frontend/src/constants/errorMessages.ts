export const ERROR_MESSAGES: Record<string, string> = {
  validation_error: '请求参数有误，请检查输入内容',
  token_expired: '登录已过期，请重新登录',
  invalid_credentials: '用户名或密码错误',
  forbidden: '您没有权限执行此操作',
  not_found: '请求的资源不存在',
  duplicate_entry: '数据已存在，请勿重复提交',
  file_too_large: '文件大小超出限制',
  unprocessable_entity: '数据格式不正确，请检查后重试',
  rate_limited: '操作过于频繁，请稍后再试',
  server_error: '服务器内部错误，请稍后重试',
  service_unavailable: '服务暂时不可用，请稍后重试',
  request_timeout: '请求超时，请检查网络连接后重试',
  network_error: '网络连接失败，请检查网络设置',
};

export const HTTP_STATUS_MESSAGES: Record<number, string> = {
  400: '请求参数有误，请检查输入内容',
  401: '身份验证失败，请重新登录',
  403: '您没有权限执行此操作',
  404: '请求的资源不存在',
  409: '数据已存在，请勿重复提交',
  413: '文件大小超出限制',
  422: '数据格式不正确，请检查后重试',
  429: '操作过于频繁，请稍后再试',
  500: '服务器内部错误，请稍后重试',
  502: '服务暂时不可用，请稍后重试',
  503: '服务暂时不可用，请稍后重试',
};

export function getChineseErrorMessage(statusCode?: number, errorCode?: string): string {
  if (errorCode && ERROR_MESSAGES[errorCode]) return ERROR_MESSAGES[errorCode];
  if (statusCode && HTTP_STATUS_MESSAGES[statusCode]) return HTTP_STATUS_MESSAGES[statusCode];
  return `操作失败，请稍后重试${errorCode ? `（错误码：${errorCode}）` : ''}`;
}

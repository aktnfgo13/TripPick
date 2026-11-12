export async function checkHealth(request: typeof fetch = fetch): Promise<boolean> {
  try {
    const response = await request('/api/v1/health', {signal: AbortSignal.timeout(5000)})
    return response.ok && (await response.json()).status === 'ok'
  } catch {
    return false
  }
}

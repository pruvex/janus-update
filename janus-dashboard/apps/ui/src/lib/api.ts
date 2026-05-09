import type { BacklogResponse } from '@shared/types'

const LOCAL_API_URL = 'http://127.0.0.1:3001'

export async function fetchBacklogItems(): Promise<BacklogResponse> {
  const response = await fetch(`${LOCAL_API_URL}/api/backlog/items`)
  
  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`)
  }
  
  return response.json()
}

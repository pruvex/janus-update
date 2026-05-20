import type { BacklogResponse, TaskExecutionHistoryResponse, TestResultsResponse, TestOverviewResponse, TestSuiteResponse } from '@shared/types'

const LOCAL_API_URL = 'http://127.0.0.1:3001'

export async function fetchBacklogItems(): Promise<BacklogResponse> {
  const response = await fetch(`${LOCAL_API_URL}/api/backlog/items`)
  
  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`)
  }
  
  return response.json()
}

export async function fetchTaskExecutionHistory(): Promise<TaskExecutionHistoryResponse> {
  const response = await fetch(`${LOCAL_API_URL}/api/task-execution-history`)

  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`)
  }

  return response.json()
}

export async function fetchTestResults(): Promise<TestResultsResponse> {
  const response = await fetch(`${LOCAL_API_URL}/api/test-results`)

  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`)
  }

  return response.json()
}

export async function fetchTestOverview(): Promise<TestOverviewResponse> {
  const response = await fetch(`${LOCAL_API_URL}/api/test-overview`)

  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`)
  }

  return response.json()
}

export async function fetchTestSuite(): Promise<TestSuiteResponse> {
  const response = await fetch(`${LOCAL_API_URL}/api/test-suite`)

  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`)
  }

  return response.json()
}

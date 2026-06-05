import type {
  BoardStateResponse,
  SimParamsRequest,
  SimulationResponse,
  TickResponse,
  TickSnapshotResponse,
} from '../types'

const BASE = '/api'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, init)
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json() as Promise<T>
}

function post<T>(path: string, body?: unknown): Promise<T> {
  return request<T>(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })
}

export const api = {
  simulations: {
    create: (params: SimParamsRequest) =>
      post<SimulationResponse>('/simulations', params),

    list: () =>
      request<SimulationResponse[]>('/simulations'),

    get: (id: number) =>
      request<SimulationResponse>(`/simulations/${id}`),

    step: (id: number) =>
      post<TickResponse>(`/simulations/${id}/step`),

    run: (id: number, ticks?: number) =>
      post<TickResponse>(`/simulations/${id}/run`, { ticks: ticks ?? null }),

    stop: (id: number) =>
      post<SimulationResponse>(`/simulations/${id}/stop`),

    getState: (id: number) =>
      request<BoardStateResponse>(`/simulations/${id}/state`),

    getStats: (id: number) =>
      request<TickSnapshotResponse[]>(`/simulations/${id}/stats`),
  },
}

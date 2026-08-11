import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || ''

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
})

// ── Scans ──────────────────────────────────────────────────────
export const getScans = (params = {}) =>
  api.get('/api/scans', { params }).then(r => r.data)

export const getScan = (id) =>
  api.get(`/api/scans/${id}`).then(r => r.data)

// ── Packages ───────────────────────────────────────────────────
export const getPackages = (params = {}) =>
  api.get('/api/packages', { params }).then(r => r.data)

export const getPackage = (name) =>
  api.get(`/api/packages/${encodeURIComponent(name)}`).then(r => r.data)

// ── Stats ──────────────────────────────────────────────────────
export const getOverviewStats = () =>
  api.get('/api/stats/overview').then(r => r.data)

export const getRiskTrend = (days = 30) =>
  api.get('/api/stats/risk-trend', { params: { days } }).then(r => r.data)

// ── Graph ──────────────────────────────────────────────────────
export const getGraphData = () =>
  api.get('/api/graph/data').then(r => r.data)

export default api

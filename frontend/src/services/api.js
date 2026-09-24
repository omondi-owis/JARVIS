/**
 * J.A.R.V.I.S. API Service - Production
 * JWT auth, device trust, scopes, audit
 */
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || ''

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor - add JWT, device ID
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('jarvis_token')
  const deviceId = localStorage.getItem('jarvis_device_id') || 'web-console'
  
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  config.headers['X-Device-ID'] = deviceId
  
  return config
})

// Response interceptor - handle 401, audit
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired - redirect to login or re-auth
      localStorage.removeItem('jarvis_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export const JarvisAPI = {
  // System
  health: () => api.get('/health').then(r => r.data),
  apiHealth: () => api.get('/api/health').then(r => r.data),

  // Server
  serverHealth: () => api.get('/api/server/health').then(r => r.data),
  serverServices: () => api.get('/api/server/services').then(r => r.data),
  serverSecurity: () => api.get('/api/server/security').then(r => r.data),

  // Wazuh
  wazuhStatus: () => api.get('/api/wazuh/status').then(r => r.data),
  wazuhAlerts: (limit = 20) => api.get(`/api/wazuh/alerts?limit=${limit}`).then(r => r.data),
  wazuhAgents: () => api.get('/api/wazuh/agents').then(r => r.data),

  // MlinziOps
  mlinziStatus: () => api.get('/api/mlinziops/status').then(r => r.data),
  mlinziAlerts: (limit = 20) => api.get(`/api/mlinziops/alerts?limit=${limit}`).then(r => r.data),
  triggerWorkflow: (name, payload) => api.post(`/api/mlinziops/workflows/${name}/trigger`, payload).then(r => r.data),

  // Telephony
  telephonyHistory: (limit = 20) => api.get(`/api/telephony/history?limit=${limit}`).then(r => r.data),
  makeCall: (destination, contactName, purpose = 'routine') => 
    api.post('/api/telephony/call', null, { params: { destination, contact_name: contactName, purpose } }).then(r => r.data),

  // IoT
  iotDevices: () => api.get('/api/iot/devices').then(r => r.data),
  iotTurnOn: (deviceId) => api.post(`/api/iot/${deviceId}/on`).then(r => r.data),
  iotTurnOff: (deviceId) => api.post(`/api/iot/${deviceId}/off`).then(r => r.data),

  // Routines
  routines: () => api.get('/api/routines').then(r => r.data),
  runRoutine: (name, dryRun = false) => api.post(`/api/routines/${name}/run?dry_run=${dryRun}`).then(r => r.data),

  // Devices
  devices: () => api.get('/api/devices').then(r => r.data),
  revokeDevice: (deviceId) => api.post(`/api/devices/${deviceId}/revoke`).then(r => r.data),

  // Audit
  auditRecent: (n = 20) => api.get(`/api/audit/recent?n=${n}`).then(r => r.data),

  // Voice
  parseVoice: (text) => api.get(`/api/voice/parse?text=${encodeURIComponent(text)}`).then(r => r.data)
}

export default api

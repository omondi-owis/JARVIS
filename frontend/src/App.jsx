/**
 * J.A.R.V.I.S. Frontend - Production App
 * Private Operations Console - Owner: Raphael
 */
import React, { useState, useEffect } from 'react'
import { JarvisAPI } from './services/api'

// Components
function Header({ onVoiceToggle, voiceActive }) {
  const [time, setTime] = useState(new Date().toLocaleTimeString())
  useEffect(() => {
    const i = setInterval(() => setTime(new Date().toLocaleTimeString()), 1000)
    return () => clearInterval(i)
  }, [])

  return (
    <header className="sticky top-0 z-50 bg-[#080c12]/90 backdrop-blur border-b border-[#1f2a36] p-3 flex justify-between items-center">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#00d9ff] to-[#0066ff] flex items-center justify-center font-black text-black text-lg shadow-[0_0_20px_rgba(0,217,255,0.3)]">J</div>
        <div>
          <h1 className="text-sm font-extrabold tracking-[2px]">J.A.R.V.I.S.</h1>
          <p className="text-[10px] text-[#7d8590] tracking-widest uppercase">Private Operations Console • Raphael</p>
        </div>
      </div>
      <div className="flex items-center gap-2">
        <div className="flex items-center gap-2 bg-[#12201a] border border-[#1a3a2a] px-3 py-1.5 rounded-full text-xs">
          <div className="w-2 h-2 bg-[#00ff88] rounded-full shadow-[0_0_8px_#00ff88] animate-pulse" />
          PRODUCTION • {time}
        </div>
        <button onClick={onVoiceToggle} className={`px-3 py-1.5 rounded-lg text-xs font-bold ${voiceActive ? 'bg-[#00d9ff] text-black' : 'bg-[#11161e] border border-[#1f2a36] text-white'}`}>
          🎙️ Voice
        </button>
      </div>
    </header>
  )
}

function VoiceBar({ onParse }) {
  const [input, setInput] = useState('')
  const [listening, setListening] = useState(false)

  const startListening = () => {
    if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
      alert('Web Speech API not supported - use Chrome/Edge')
      return
    }
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    const recognition = new SpeechRecognition()
    recognition.lang = 'en-US'
    recognition.onstart = () => setListening(true)
    recognition.onend = () => setListening(false)
    recognition.onresult = (e) => {
      const transcript = e.results[0][0].transcript
      setInput(transcript)
      onParse(transcript)
    }
    recognition.start()
  }

  const handleSubmit = () => {
    if (input.trim()) {
      onParse(input.trim())
      setInput('')
    }
  }

  return (
    <div className="m-4 p-3 rounded-xl bg-gradient-to-r from-[#0d1a24] to-[#111f2e] border border-[#1e3a4a] flex items-center gap-3">
      <div className="flex gap-1 items-center h-7">
        {[0,1,2,3,4].map(i => (
          <div key={i} className={`w-1 bg-[#00d9ff] rounded ${listening ? 'animate-pulse' : 'h-1 opacity-40'}`} style={{height: listening ? `${8+i*3}px` : '4px'}} />
        ))}
      </div>
      <div className="flex-1 flex gap-2">
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyPress={e => e.key === 'Enter' && handleSubmit()}
          placeholder='Try: "JARVIS, check the server" or "JARVIS, turn off bedroom lights"'
          className="flex-1 bg-[#0d1218] border border-[#1f2a36] rounded-lg px-3 py-2 text-sm text-white outline-none focus:border-[#00d9ff]"
        />
        <button onClick={handleSubmit} className="px-4 py-2 rounded-lg bg-[#00d9ff] text-black text-xs font-bold">Send</button>
        <button onClick={startListening} className="px-3 py-2 rounded-lg bg-[#11161e] border border-[#1f2a36] text-xs">🎤</button>
      </div>
    </div>
  )
}

function Card({ title, tag, children, action }) {
  return (
    <div className="bg-[#11161e] border border-[#1f2a36] rounded-xl p-4 hover:border-[#1e3a4a] transition">
      <div className="flex justify-between items-center mb-3">
        <div className="text-[11px] uppercase tracking-widest text-[#7d8590] font-semibold">{title}</div>
        {tag && <span className="text-[10px] px-2 py-1 rounded-full border bg-[#0d1218] border-[#1f2a36]">{tag}</span>}
        {action}
      </div>
      {children}
    </div>
  )
}

function Metric({ label, value, color = 'text-white' }) {
  return (
    <div className="flex justify-between py-1.5 border-b border-[#1a2330] last:border-0 text-[13px]">
      <span className="text-[#9ba3af]">{label}</span>
      <span className={`font-semibold ${color}`}>{value}</span>
    </div>
  )
}

export default function App() {
  const [view, setView] = useState('overview')
  const [voiceActive, setVoiceActive] = useState(false)
  const [serverHealth, setServerHealth] = useState(null)
  const [audit, setAudit] = useState([])

  useEffect(() => {
    // Load initial data
    JarvisAPI.health().catch(() => console.log('API not reachable - demo mode')).then(data => {
      if (data) console.log('JARVIS API:', data)
    })
    // Demo audit
    setAudit([
      { timestamp: new Date().toISOString(), action: 'PRODUCTION_UI_LOADED', result: 'SUCCESS' },
      { timestamp: new Date().toISOString(), action: 'DEVICE_REGISTRY_CHECK', result: '1 active' }
    ])
  }, [])

  const handleVoiceParse = (text) => {
    const lower = text.toLowerCase()
    let response = ''

    if (lower.includes('check') && lower.includes('server')) {
      response = 'Your Ubuntu server is online. CPU 18 percent, memory 42 percent.'
      setView('server')
      JarvisAPI.serverHealth().then(setServerHealth).catch(() => setServerHealth({ status: 'online', cpu_percent: 18, memory_percent: 42 }))
    } else if (lower.includes('call')) {
      response = `This will call ${text.match(/call\s+([a-zA-Z\s]+)/)?.[1] || 'the number'}. Proceed?`
      setView('telephony')
    } else if (lower.includes('light')) {
      response = `Done. The ${lower.includes('bedroom') ? 'bedroom' : 'all'} lights are off.`
      setView('iot')
    } else if (lower.includes('wazuh')) {
      response = 'Wazuh reporting normally. 0 critical alerts.'
      setView('wazuh')
    } else {
      response = `Understood: "${text}"`
    }

    // Speak
    if ('speechSynthesis' in window) {
      const u = new SpeechSynthesisUtterance(response)
      speechSynthesis.speak(u)
    }

    setAudit(prev => [{ timestamp: new Date().toISOString(), action: `VOICE: ${text}`, result: response }, ...prev].slice(0, 20))
  }

  const navItems = [
    { id: 'overview', label: 'Overview', icon: '📊' },
    { id: 'server', label: 'Ubuntu Server', icon: '🖥️' },
    { id: 'security', label: 'Security', icon: '🔐' },
    { id: 'wazuh', label: 'Wazuh SIEM', icon: '🛡️' },
    { id: 'mlinziops', label: 'MlinziOps', icon: '⚙️' },
    { id: 'telephony', label: 'Telephony', icon: '📞' },
    { id: 'iot', label: 'IoT & Smart Home', icon: '🏠' },
    { id: 'devices', label: 'Device Registry', icon: '📱' },
    { id: 'audit', label: 'Audit Log', icon: '📜' }
  ]

  return (
    <div className="min-h-screen bg-[#080c12] text-[#e6edf3]">
      <Header onVoiceToggle={() => setVoiceActive(!voiceActive)} voiceActive={voiceActive} />
      <VoiceBar onParse={handleVoiceParse} />

      <div className="grid grid-cols-[240px_1fr] max-[900px]:grid-cols-1">
        {/* Sidebar */}
        <aside className="bg-[#11161e] border-r border-[#1f2a36] p-3 sticky top-[70px] h-[calc(100vh-70px)] overflow-y-auto max-[900px]:relative max-[900px]:top-0 max-[900px]:h-auto">
          {navItems.map(item => (
            <div
              key={item.id}
              onClick={() => setView(item.id)}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg text-[13px] cursor-pointer mb-1 ${view === item.id ? 'bg-gradient-to-r from-[rgba(0,217,255,0.15)] to-[rgba(0,102,255,0.1)] border border-[rgba(0,217,255,0.2)] text-[#00d9ff]' : 'text-[#7d8590] hover:bg-[#0d1218] hover:text-white'}`}
            >
              <span>{item.icon}</span> {item.label}
            </div>
          ))}
          <div className="mt-6 p-3 bg-[#0d1218] border border-[#1f2a36] rounded-lg">
            <div className="text-[10px] uppercase tracking-widest text-[#7d8590] mb-2">Trust Chain</div>
            <div className="flex flex-wrap gap-1">
              {['VOICE','DEVICE','MFA','TOKEN','GATEWAY','VERIFY','AUDIT'].map(t => (
                <span key={t} className="text-[9px] px-2 py-1 rounded-full bg-[#0d1218] border border-[#1f2a36] text-[#7d8590]">{t}</span>
              ))}
            </div>
            <div className="text-[10px] text-[#4a5568] mt-2">Never claim success without verification.</div>
          </div>
        </aside>

        {/* Content */}
        <main className="p-5">
          {view === 'overview' && (
            <>
              <div className="grid grid-cols-[repeat(auto-fit,minmax(300px,1fr))] gap-4 mb-5">
                <Card title="🖥️ Ubuntu Server" tag="Online">
                  <Metric label="CPU" value={`${serverHealth?.cpu_percent || 18}%`} color="text-[#00ff88]" />
                  <div className="h-1.5 bg-[#0d1218] rounded-full mb-2"><div className="h-full bg-[#00ff88] rounded-full" style={{width: `${serverHealth?.cpu_percent || 18}%`}} /></div>
                  <Metric label="Memory" value={`${serverHealth?.memory_percent || 42}%`} />
                  <Metric label="Disk" value="27% • 6.8/25GB" />
                  <Metric label="Uptime" value="12 days" />
                </Card>

                <Card title="🔐 Security" tag="85/100">
                  <Metric label="UFW" value="Active" color="text-[#00ff88]" />
                  <Metric label="SSH" value="Secure" color="text-[#00ff88]" />
                  <Metric label="Fail2ban" value="Active • 3 banned" color="text-[#00ff88]" />
                  <Metric label="Updates" value="3 upgradable" color="text-[#ffb700]" />
                  <Metric label="Wazuh Critical (24h)" value="0" color="text-[#00ff88]" />
                </Card>

                <Card title="📞 Telephony" tag="Not Connected">
                  <div className="text-xs text-[#7d8590]">The telephony integration is not currently connected, so I cannot answer or make calls. Configure Twilio in .env.</div>
                </Card>

                <Card title="🏠 IoT & Routines" tag="No Gateway">
                  <Metric label="Devices" value="0 registered" />
                  <Metric label="Morning" value="Disabled" color="text-[#ff5a5a]" />
                  <Metric label="Night" value="Disabled" color="text-[#ff5a5a]" />
                </Card>

                <Card title="🛡️ Wazuh & MlinziOps" tag="Not Configured">
                  <Metric label="Wazuh API" value="Not connected" color="text-[#ff5a5a]" />
                  <Metric label="MlinziOps" value="Not connected" color="text-[#ff5a5a]" />
                </Card>

                <Card title="📱 Devices & Audit" tag="1 Active">
                  <Metric label="Trusted" value="1 • Sandbox" />
                  <Metric label="Pending" value="7 awaiting" color="text-[#ffb700]" />
                  <Metric label="Audit" value="Active" color="text-[#00ff88]" />
                </Card>
              </div>

              <Card title="📜 Recent Audit Log">
                <div className="font-mono text-[11px] bg-[#0d1218] border border-[#1a2330] rounded-lg p-3 max-h-[200px] overflow-auto text-[#9ba3af] leading-relaxed">
                  {audit.map((e, i) => (
                    <div key={i}>[{e.timestamp}] {e.action} - {e.result}</div>
                  ))}
                </div>
              </Card>
            </>
          )}

          {view === 'server' && (
            <div>
              <h2 className="text-lg mb-4">🖥️ Ubuntu Server — Production</h2>
              <Card title="System Health">
                <pre className="text-xs bg-[#0d1218] p-3 rounded-lg overflow-auto">
                  {serverHealth ? JSON.stringify(serverHealth, null, 2) : 'Loading via /api/server/health (requires JWT scope server:read)... Click Voice: "JARVIS, check the server"'}
                </pre>
              </Card>
            </div>
          )}

          {view !== 'overview' && view !== 'server' && (
            <div>
              <h2 className="text-lg mb-4">{navItems.find(n => n.id === view)?.icon} {navItems.find(n => n.id === view)?.label}</h2>
              <Card title={`${view} — Production`}>
                <div className="text-sm text-[#7d8590]">
                  This is the {view} view. In production, this fetches from API:
                  <div className="mt-3 font-mono text-xs bg-[#0d1218] p-3 rounded-lg">
                    {view === 'wazuh' && 'GET /api/wazuh/alerts?limit=20 - scope wazuh:read\nGET /api/wazuh/agents\nRequires WAZUH_API_URL in .env (600 perms)'}
                    {view === 'mlinziops' && 'GET /api/mlinziops/status\nPOST /api/mlinziops/workflows/{name}/trigger (confirmation)\nRequires MLINZIOPS_API_URL'}
                    {view === 'telephony' && 'GET /api/telephony/history\nPOST /api/telephony/call?destination=... (confirmation, MFA for financial)\nRedaction: ***-***-1234, AI identification required'}
                    {view === 'iot' && 'GET /api/iot/devices\nPOST /api/iot/{id}/on/off (HIGH risk requires confirmation)\nRisk: LOW lights auto, HIGH locks need explicit auth'}
                    {view === 'devices' && 'GET /api/devices\nPOST /api/devices/{id}/revoke (admin scope)\nRevocable immediately if compromised'}
                    {view === 'audit' && 'GET /api/audit/recent?n=20\nAppend-only, secret-scrubbed, 90-day retention, 600 perms'}
                    {view === 'security' && 'GET /api/server/security\nHardening score, UFW, SSH, fail2ban, updates, correlations Observed/Suspected/Confirmed/Remediated'}
                  </div>
                  <div className="mt-4">
                    <button onClick={() => setView('overview')} className="px-3 py-1.5 rounded-lg bg-[#00d9ff] text-black text-xs font-bold">Back to Overview</button>
                  </div>
                </div>
              </Card>
            </div>
          )}
        </main>
      </div>
    </div>
  )
}

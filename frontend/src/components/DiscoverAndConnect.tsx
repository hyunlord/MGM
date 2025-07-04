import React, { useState } from 'react';
import axios from 'axios';

interface DiscoverAndConnectProps {
  onConnect: (host: string) => void;
}
export function DiscoverAndConnect({ onConnect }: DiscoverAndConnectProps) {
  // 연결된 서버 리스트
  const [connectedServers, setConnectedServers] = useState<string[]>([]);

  // 수동 입력용 state
  const [host, setHost] = useState('');
  const [sshUser, setSshUser] = useState('hanadmin');
  const [principal, setPrincipal] = useState('');
  const [kinitPassword, setKinitPassword] = useState('');
  const [password, setPassword] = useState('');
  const [connecting, setConnecting] = useState(false);

  // SSH 연결 요청
  const connect = async () => {
    if (!host) return;
    setConnecting(true);
    try {
      await axios.post('/api/servers/connect', {
        host,
        ssh_user: sshUser,
        principal: principal || undefined,
        kinit_password: kinitPassword || undefined,
        password: password || undefined
      });
      onConnect(host);
      setHost('');
      setPassword('');
      setKinitPassword('');
    } catch (e) {
      alert(`Connect failed (${host}): ${e}`);
    } finally {
      setConnecting(false);
    }
  };

  return (
    <div style={{ maxWidth: 600, margin: '40px auto', fontFamily: 'Arial, sans-serif' }}>
      <h1 style={{ textAlign: 'center', marginBottom: 20 }}>Remote MLOps UI</h1>

      {/* 연결된 서버 목록 */}
      <div style={{ marginBottom: 30 }}>
        <h2>Connected Servers</h2>
        {connectedServers.length === 0 ? (
          <p style={{ color: '#777' }}>No servers connected.</p>
        ) : (
          <ul style={{ listStyle: 'none', padding: 0 }}>
            {connectedServers.map(s => (
              <li key={s} style={{ padding: '8px 12px', background: '#f5f5f5', marginBottom: 8, borderRadius: 4 }}>
                {s}
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* 수동 연결 섹션 */}
      <div style={{ padding: 20, border: '1px solid #ddd', borderRadius: 6, background: '#fafafa' }}>
        <h2 style={{ marginBottom: 16 }}>Connect to Server</h2>
        <div style={{ marginBottom: 12 }}>
          <label style={{ display: 'block', marginBottom: 4 }}>Host</label>
          <input
            value={host}
            onChange={e => setHost(e.target.value)}
            placeholder="hostname or IP"
            style={{ width: '100%', padding: 8, borderRadius: 4, border: '1px solid #ccc' }}
          />
        </div>
        <div style={{ marginBottom: 12 }}>
          <label style={{ display: 'block', marginBottom: 4 }}>SSH User</label>
          <input
            value={sshUser}
            onChange={e => setSshUser(e.target.value)}
            style={{ width: '100%', padding: 8, borderRadius: 4, border: '1px solid #ccc' }}
          />
        </div>
        <div style={{ marginBottom: 12 }}>
          <label style={{ display: 'block', marginBottom: 4 }}>Principal (Kerberos)</label>
          <input
            value={principal}
            onChange={e => setPrincipal(e.target.value)}
            placeholder="e.g. rexxa.som@KAKAO.COM"
            style={{ width: '100%', padding: 8, borderRadius: 4, border: '1px solid #ccc' }}
          />
        </div>
        <div style={{ marginBottom: 12 }}>
          <label style={{ display: 'block', marginBottom: 4 }}>kinit Password</label>
          <input
            type="password"
            value={kinitPassword}
            onChange={e => setKinitPassword(e.target.value)}
            style={{ width: '100%', padding: 8, borderRadius: 4, border: '1px solid #ccc' }}
          />
        </div>
        <div style={{ marginBottom: 12 }}>
          <label style={{ display: 'block', marginBottom: 4 }}>Password (SSH)</label>
          <input
            type="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            style={{ width: '100%', padding: 8, borderRadius: 4, border: '1px solid #ccc' }}
          />
        </div>
        <button
          onClick={connect}
          disabled={connecting || !host}
          style={{
            width: '100%', padding: 12, borderRadius: 4,
            border: 'none', background: connecting ? '#999' : '#007bff',
            color: '#fff', fontSize: 16, cursor: connecting ? 'default' : 'pointer'
          }}
        >
          {connecting ? 'Connecting…' : 'Connect'}
        </button>
      </div>
    </div>
  );
}

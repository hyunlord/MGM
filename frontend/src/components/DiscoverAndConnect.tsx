// frontend/src/components/DiscoverAndConnect.tsx
import React, { useState } from 'react';
import axios from 'axios';

export function DiscoverAndConnect() {
  const [subnet, setSubnet] = useState('192.168.1.0/24');
  const [hosts, setHosts] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  // 수동 입력용 state
  const [manualHost, setManualHost] = useState('');
  const [user, setUser] = useState('user');
  const [keyPath, setKeyPath] = useState('~/.ssh/id_rsa');
  const [password, setPassword] = useState('');

  // 1) 서버 스캔
  const discover = async () => {
    setLoading(true);
    try {
      const res = await axios.get<string[]>('/servers/discover', { params: { subnet } });
      setHosts(res.data);
    } catch (e) {
      alert('Discovery failed: ' + e);
    } finally {
      setLoading(false);
    }
  };

  // 2) SSH 연결 요청
  const connect = async (host: string) => {
    try {
      await axios.post('/servers/connect', { host, user, key_path: keyPath, password });
      alert(`Connected to ${host}`);
    } catch (e) {
      alert(`Connect failed (${host}): ` + e);
    }
  };

  return (
    <div style={{ padding: 20 }}>
      <h2>1. 서버 자동 스캔</h2>
      <input
        value={subnet}
        onChange={e => setSubnet(e.target.value)}
        style={{ width: 200 }}
      />
      <button onClick={discover} disabled={loading}>
        {loading ? 'Scanning…' : 'Discover'}
      </button>

      <h3>발견된 호스트</h3>
      <ul>
        {hosts.map(h => (
          <li key={h}>
            {h}{' '}
            <button onClick={() => connect(h)}>Connect</button>
          </li>
        ))}
      </ul>

      <h2>2. 수동 입력</h2>
      <div>
        <label>
          Host:&nbsp;
          <input value={manualHost} onChange={e => setManualHost(e.target.value)} />
        </label>
      </div>
      <div>
        <label>
          User:&nbsp;
          <input value={user} onChange={e => setUser(e.target.value)} />
        </label>
      </div>
      <div>
        <label>
          Key Path:&nbsp;
          <input value={keyPath} onChange={e => setKeyPath(e.target.value)} />
        </label>
      </div>
      <div>
        <label>
          Password (옵션):&nbsp;
          <input type="password" value={password} onChange={e => setPassword(e.target.value)} />
        </label>
      </div>
      <button onClick={() => connect(manualHost)}>Manual Connect</button>
    </div>
  );
}

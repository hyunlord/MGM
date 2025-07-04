// frontend/src/App.tsx
import React, { useState } from 'react';
import { DiscoverAndConnect } from './components/DiscoverAndConnect';
import { ServerDashboard } from './components/ServerDashboard';

function App() {
    const [connectedServers, setConnectedServers] = useState<string[]>([]);
    const handleConnect = (host: string) => {
        setConnectedServers(prev =>
            prev.includes(host) ? prev : [...prev, host]
        );
    }
    return (
        <div style={{padding: 20}}>
            {/* 3) 서버 연결 폼에 콜백 전달 */}
            <DiscoverAndConnect onConnect={handleConnect}/>
            {/* 4) 연결된 서버마다 대시보드 렌더링 */}
            {connectedServers.map(host => (
                <ServerDashboard key={host} host={host}/>
            ))}
        </div>
    );
}

export default App;

import React, { useEffect, useState } from 'react';
import axios from 'axios';

export interface Metrics {
  cpu_percent: number;
  mem_percent: number;
  disk: Array<{
    filesystem: string;
    size: string;
    used: string;
    avail: string;
    use_percent: string;
    mountpoint: string;
  }>;
  gpus: Array<{
    index: number;
    memory_used: number;
    memory_total: number;
    utilization: number;
  }>;
}

interface ServerDashboardProps {
  host: string;
}

export const ServerDashboard: React.FC<ServerDashboardProps> = ({ host }) => {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchMetrics = async () => {
    try {
      const res = await axios.get<Metrics>(`/api/servers/${encodeURIComponent(host)}/metrics`);
      setMetrics(res.data);
      setError(null);
    } catch (e) {
      if (axios.isAxiosError(e) && e.response) {
        const code = e.response.status;
        if (code === 400) {
          setError('서버에 연결되어 있지 않습니다.');
        } else if (code === 502) {
          setError('원격 서버에서 메트릭을 가져오던 중 오류가 발생했습니다.');
        } else {
          setError(`메트릭 요청 실패 (HTTP ${code})`)
        }
      } else {
        setError(`메트릭 요청 실패: ${String(e)}`);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMetrics();
    const tid = setInterval(fetchMetrics, 5000);
    return () => clearInterval(tid);
  }, [host]);

  if (loading) return <p>Loading metrics for {host}…</p>;
  if (error)   return <p style={{ color: 'red' }}>{error}</p>;
  if (!metrics) return null;

  return (
    <div style={{
      margin: '20px 0', padding: 16,
      border: '1px solid #ddd', borderRadius: 6, background: '#fff'
    }}>
      <h3 style={{ marginBottom: 12 }}>{host}</h3>
      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
        <div>
          <p><strong>CPU:</strong> {metrics.cpu_percent}%</p>
          <p><strong>Memory:</strong> {metrics.mem_percent}%</p>
        </div>
        <div>
          <p><strong>Disk:</strong></p>
          {metrics.disk.map(d => (
            <li key={d.mountpoint}>
              <strong>{d.mountpoint}</strong>: {d.used}GB / {d.size}GB ({d.percent}%)
            </li>
          ))}
        </div>
        <div>
          <p><strong>GPUs:</strong></p>
          {metrics.gpus.map(g => (
            <p key={g.index}>
              GPU {g.index}: {g.utilization}% | {g.memory_used}/{g.memory_total} MB
            </p>
          ))}
        </div>
      </div>
    </div>
  );
};

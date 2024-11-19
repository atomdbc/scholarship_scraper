// pages/dashboard.tsx
import { useEffect, useState } from 'react';
import { StatusCards } from '../components/dashboard/StatusCards';
import { ScholarshipTable } from '../components/dashboard/ScholarshipTable';
import { FilterPanel } from '../components/dashboard/FilterPanel';
import { Loading } from '../components/common/Loading';
import { api } from '../lib/api';
import type { ScrapingStatus, Scholarship } from '../lib/types';

export default function Dashboard() {
  const [status, setStatus] = useState<ScrapingStatus | null>(null);
  const [scholarships, setScholarships] = useState<Scholarship[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statusData, scholarshipsData] = await Promise.all([
          api.getStatus(),
          api.getScholarships()
        ]);
        setStatus(statusData);
        setScholarships(scholarshipsData);
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading || !status) return <Loading />;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Dashboard</h1>
      <StatusCards status={status} />
      <FilterPanel onFilter={console.log} />
      <ScholarshipTable scholarships={scholarships} />
    </div>
  );
}
// pages/export.tsx
import { Layout } from '../components/layout/Layout';
import { ExportForm } from '../components/export/ExportForm';

export default function ExportPage() {
  return (
      <div className="container mx-auto py-6">
        <h1 className="text-2xl font-bold mb-6">Export Scholarships</h1>
        <ExportForm />
      </div>
  );
}
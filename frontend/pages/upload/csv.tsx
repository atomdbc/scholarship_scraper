// pages/upload/csv.tsx
import { Layout } from '../../components/layout/Layout';
import { UploadForm } from '../../components/upload/UploadForm';

export default function CsvUploadPage() {
  return (
      <div className="container mx-auto py-6">
        <h1 className="text-2xl font-bold mb-6">Upload Scholarship CSV</h1>
        <UploadForm />
      </div>
  );
}
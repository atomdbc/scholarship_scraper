import { Layout } from '../components/layout/Layout';
import { UploadForm } from '../components/upload/UploadForm';

export default function UploadPage() {
  return (
    <Layout>
      <div className="container mx-auto py-6">
        <h1 className="text-2xl font-bold mb-6">Upload Scholarship URLs</h1>
        <UploadForm />
      </div>
    </Layout>
  );
}
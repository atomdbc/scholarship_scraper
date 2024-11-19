// pages/scholarships/index.tsx
import { useState } from 'react';
import { Button } from '../../components/common/Button';
import { Card } from '../../components/common/Card';
import { Upload, Plus, X } from 'lucide-react';
import { api } from '../../lib/api';

export default function UploadUrls() {
  const [urls, setUrls] = useState<string[]>(['']);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  const addUrlField = () => {
    setUrls([...urls, '']);
  };

  const removeUrlField = (index: number) => {
    const newUrls = urls.filter((_, i) => i !== index);
    setUrls(newUrls.length ? newUrls : ['']);
  };

  const updateUrl = (index: number, value: string) => {
    const newUrls = [...urls];
    newUrls[index] = value;
    setUrls(newUrls);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');

    try {
      const validUrls = urls.filter(url => url.trim());
      const response = await api.uploadUrls(validUrls);
      setMessage('URLs uploaded successfully!');
      setUrls(['']);
    } catch (error) {
      setMessage('Error uploading URLs. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">Upload Scholarship URLs</h1>
      
      <Card className="p-6">
        <form onSubmit={handleSubmit} className="space-y-4">
          {urls.map((url, index) => (
            <div key={index} className="flex gap-2">
              <input
                type="url"
                value={url}
                onChange={(e) => updateUrl(index, e.target.value)}
                placeholder="Enter scholarship URL"
                className="flex-1 px-4 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
              {urls.length > 1 && (
                <Button
                  type="button"
                  variant="destructive"
                  onClick={() => removeUrlField(index)}
                >
                  <X className="w-4 h-4" />
                </Button>
              )}
            </div>
          ))}
          
          <div className="flex gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={addUrlField}
              className="w-full"
            >
              <Plus className="w-4 h-4 mr-2" />
              Add Another URL
            </Button>
          </div>
          
          <Button
            type="submit"
            className="w-full"
            disabled={loading}
          >
            <Upload className="w-4 h-4 mr-2" />
            {loading ? 'Uploading...' : 'Upload URLs'}
          </Button>
          
          {message && (
            <div className={`p-4 rounded ${
              message.includes('Error') ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'
            }`}>
              {message}
            </div>
          )}
        </form>
      </Card>
    </div>
  );
}
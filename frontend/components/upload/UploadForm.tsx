import React, { useState } from 'react';
import { Card } from '../common/Card';
import { Input } from '../../components/ui/input';
import { Button } from '../../components/ui/button';
import { Upload, FileUp, Link as LinkIcon } from 'lucide-react';
import { api } from '../../lib/api';
import { useToast } from '../../components/ui/use-toast';

export const UploadForm = () => {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile && (selectedFile.type === 'text/csv' || selectedFile.type === 'text/plain')) {
      setFile(selectedFile);
    } else {
      toast({
        title: "Invalid file type",
        description: "Please upload a CSV or TXT file",
        variant: "destructive"
      });
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    
    setLoading(true);
    try {
      const result = await api.uploadUrlFile(file);
      toast({
        title: "Upload successful",
        description: `Created ${result.tasks_created} tasks, skipped ${result.tasks_skipped} duplicates`
      });
      setFile(null);
    } catch (error) {
      toast({
        title: "Upload failed",
        description: error instanceof Error ? error.message : "Unknown error occurred",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <Card className="p-6">
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <FileUp className="w-5 h-5" />
            <h2 className="text-lg font-semibold">Upload URL File</h2>
          </div>
          
          <div className="flex gap-4">
            <Input
              type="file"
              accept=".csv,.txt"
              onChange={handleFileChange}
              className="flex-1"
            />
            <Button
              onClick={handleUpload}
              disabled={!file || loading}
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <Upload className="w-4 h-4 animate-spin" />
                  Uploading...
                </span>
              ) : (
                <span className="flex items-center gap-2">
                  <Upload className="w-4 h-4" />
                  Upload
                </span>
              )}
            </Button>
          </div>
          
          <p className="text-sm text-gray-500">
            Upload a CSV or TXT file containing scholarship URLs (one per line)
          </p>
        </div>
      </Card>

      <Card className="p-6">
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <LinkIcon className="w-5 h-5" />
            <h2 className="text-lg font-semibold">Upload Format Example</h2>
          </div>
          
          <pre className="bg-gray-50 p-4 rounded-md text-sm">
            {`URL
https://example.com/scholarship1
https://example.com/scholarship2
https://example.com/scholarship3`}
          </pre>
        </div>
      </Card>
    </div>
  );
};
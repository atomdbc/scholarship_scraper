// lib/api.ts
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080/api';

export const api = {
  async getStatus() {
    const res = await fetch(`${API_URL}/status`);
    if (!res.ok) throw new Error('Failed to fetch status');
    return res.json();
  },

  async getScholarships(params?: {
    skip?: number;
    limit?: number;
    field_of_study?: string;
    level_of_study?: string;
    min_confidence?: number;
    deadline_after?: string;
    min_amount?: number;
    max_amount?: number;
    source_url?: string;
  }) {
    const queryParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          queryParams.append(key, value.toString());
        }
      });
    }
    const res = await fetch(`${API_URL}/scholarships?${queryParams}`);
    if (!res.ok) throw new Error('Failed to fetch scholarships');
    return res.json();
  },

  async getScholarship(id: string) {
    const res = await fetch(`${API_URL}/scholarships/${id}`);
    if (!res.ok) throw new Error('Failed to fetch scholarship');
    return res.json();
  },

  async getScholarshipStats() {
    const res = await fetch(`${API_URL}/scholarships/stats`);
    if (!res.ok) throw new Error('Failed to fetch scholarship stats');
    return res.json();
  },

  async uploadUrls(urls: string[]) {
    const res = await fetch(`${API_URL}/tasks/bulk`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ urls }),
    });
    if (!res.ok) throw new Error('Failed to upload URLs');
    return res.json();
  },

  async retryTask(taskId: number) {
    const res = await fetch(`${API_URL}/tasks/${taskId}/retry`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to retry task');
    return res.json();
  },

  async getFailedTasks(skip = 0, limit = 100) {
    const res = await fetch(`${API_URL}/tasks/failed?skip=${skip}&limit=${limit}`);
    if (!res.ok) throw new Error('Failed to fetch failed tasks');
    return res.json();
  },

  async getTaskProgress(taskId: number) {
    const res = await fetch(`${API_URL}/tasks/${taskId}/progress`);
    if (!res.ok) throw new Error('Failed to fetch task progress');
    return res.json();
  },
  
  async uploadUrlFile(file: File) {
    const formData = new FormData();
    formData.append('file', file);

    const res = await fetch(`${API_URL}/tasks/upload-urls`, {
      method: 'POST',
      body: formData,
    });
    
    if (!res.ok) throw new Error('Failed to upload file');
    return res.json();
  },

  async exportScholarships(startDate?: string, endDate?: string) {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    
    const res = await fetch(`${API_URL}/scholarships/export?${params}`);
    if (!res.ok) throw new Error('Failed to export scholarships');
    return res.json();
  },

  async exportScholarshipsCsv(startDate?: string, endDate?: string) {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    
    const res = await fetch(`${API_URL}/scholarships/export/csv?${params}`);
    if (!res.ok) throw new Error('Failed to export scholarships CSV');
    
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'scholarships_export.csv';
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  },
};




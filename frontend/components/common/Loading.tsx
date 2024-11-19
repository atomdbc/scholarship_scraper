// components/common/Loading.tsx
import { RefreshCw } from 'lucide-react';

export const Loading = () => (
  <div className="flex justify-center items-center h-64">
    <RefreshCw className="w-8 h-8 animate-spin text-primary" />
  </div>
);
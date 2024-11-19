import Link from 'next/link';
import { Home, List, Upload, FileText, Download } from 'lucide-react';

export const Sidebar = () => {
  return (
    <aside className="w-64 border-r h-screen p-4">
      <nav className="space-y-2">
        <Link href="/dashboard" className="flex items-center gap-2 p-2 hover:bg-gray-100 rounded">
          <Home className="w-4 h-4" />
          Dashboard
        </Link>
        <Link href="/scholarships" className="flex items-center gap-2 p-2 hover:bg-gray-100 rounded">
          <List className="w-4 h-4" />
          Scholarships
        </Link>
        <Link href="/upload" className="flex items-center gap-2 p-2 hover:bg-gray-100 rounded">
          <Upload className="w-4 h-4" />
          Upload URLs
        </Link>
        <Link href="/upload/csv" className="flex items-center gap-2 p-2 hover:bg-gray-100 rounded">
          <FileText className="w-4 h-4" />
          Upload CSV
        </Link>
        <Link href="/export" className="flex items-center gap-2 p-2 hover:bg-gray-100 rounded">
          <Download className="w-4 h-4" />
          Export
        </Link>
      </nav>
    </aside>
  );
};
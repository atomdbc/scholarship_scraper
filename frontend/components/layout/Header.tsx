// components/layout/Header.tsx
import { Button } from '../common/Button';
import { Upload, BarChart2 } from 'lucide-react';
import Link from 'next/link';

export const Header = () => {
  return (
    <header className="border-b">
      <div className="container mx-auto px-4 py-4 flex items-center justify-between">
        <Link href="/" className="text-xl font-bold">
          Striveopps  Scraper
        </Link>
        <nav className="flex items-center gap-4">
          <Link href="/dashboard">
            <Button variant="ghost">
              <BarChart2 className="w-4 h-4 mr-2" />
              Dashboard
            </Button>
          </Link>
          <Link href="/scholarships">
            <Button variant="ghost">
              <Upload className="w-4 h-4 mr-2" />
              Upload URLs
            </Button>
          </Link>
        </nav>
      </div>
    </header>
  );
};
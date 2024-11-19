// components/dashboard/FilterPanel.tsx
import { Button } from '../common/Button';
import { Search, Filter } from 'lucide-react';

interface FilterPanelProps {
  onFilter: (filters: any) => void;
}

export const FilterPanel = ({ onFilter }: FilterPanelProps) => {
  return (
    <div className="flex gap-4 mb-6">
      <input
        type="text"
        placeholder="Search scholarships..."
        className="flex-1 px-4 py-2 border rounded"
      />
      <select className="px-4 py-2 border rounded">
        <option value="">All Fields</option>
        <option value="engineering">Engineering</option>
        <option value="science">Science</option>
        <option value="arts">Arts</option>
      </select>
      <select className="px-4 py-2 border rounded">
        <option value="">All Levels</option>
        <option value="undergraduate">Undergraduate</option>
        <option value="graduate">Graduate</option>
        <option value="phd">PhD</option>
      </select>
      <Button>
        <Filter className="w-4 h-4 mr-2" />
        Apply Filters
      </Button>
    </div>
  );
};
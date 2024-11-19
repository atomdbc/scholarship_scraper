// components/dashboard/ScholarshipTable.tsx
import { Button } from '../common/Button';
import type { Scholarship } from '../../lib/types';
import Link from 'next/link';

interface ScholarshipTableProps {
  scholarships: Scholarship[];
}

export const ScholarshipTable = ({ scholarships }: ScholarshipTableProps) => {
  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b">
            <th className="text-left p-4">Title</th>
            <th className="text-left p-4">Amount</th>
            <th className="text-left p-4">Deadline</th>
            <th className="text-left p-4">Field of Study</th>
            <th className="text-left p-4">Actions</th>
          </tr>
        </thead>
        <tbody>
          {scholarships.map((scholarship) => (
            <tr key={scholarship.id} className="border-b hover:bg-gray-50">
              <td className="p-4">{scholarship.title}</td>
              <td className="p-4">{scholarship.amount}</td>
              <td className="p-4">
                {scholarship.deadline ? new Date(scholarship.deadline).toLocaleDateString() : 'N/A'}
              </td>
              <td className="p-4">{scholarship.field_of_study}</td>
              <td className="p-4">
                <Link href={`/scholarships/${scholarship.id}`}>
                  <Button size="sm">View Details</Button>
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
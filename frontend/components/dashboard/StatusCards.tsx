// components/dashboard/StatusCards.tsx
import { Card } from '../common/Card';
import type { ScrapingStatus } from '../../lib/types';
import { CheckCircle, AlertTriangle, Clock, Loader, Database, Activity, Percent } from 'lucide-react';

interface StatusCardsProps {
  status: ScrapingStatus;
}

export const StatusCards = ({ status }: StatusCardsProps) => {
  const cards = [
    {
      title: 'Total Tasks',
      value: status.total_tasks,
      icon: Clock,
      color: 'text-blue-500',
    },
    {
      title: 'Completed',
      value: status.completed,
      icon: CheckCircle,
      color: 'text-green-500',
    },
    {
      title: 'Pending',
      value: status.pending,
      icon: Loader,
      color: 'text-yellow-500',
      subtitle: `${status.processing_rate.toFixed(2)}/min`,
    },
    {
      title: 'Failed',
      value: status.failed,
      icon: AlertTriangle,
      color: 'text-red-500',
    },
    {
      title: 'Total Scholarships',
      value: status.total_scholarships,
      icon: Database,
      color: 'text-purple-500',
    },
    {
      title: 'Success Rate',
      value: `${status.success_rate.toFixed(1)}%`,
      icon: Percent,
      color: 'text-green-500',
    },
    {
      title: 'Avg Confidence',
      value: `${(status.average_confidence_score * 100).toFixed(1)}%`,
      icon: Activity,
      color: 'text-blue-500',
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
      {cards.map((card, index) => (
        <Card key={index} className="p-4">
          <div className="flex items-center gap-4">
            <card.icon className={`w-8 h-8 ${card.color}`} />
            <div>
              <p className="text-sm text-gray-500">{card.title}</p>
              <p className="text-2xl font-bold">{card.value}</p>
              {card.subtitle && (
                <p className="text-sm text-gray-500">{card.subtitle}</p>
              )}
            </div>
          </div>
        </Card>
      ))}
    </div>
  );
};
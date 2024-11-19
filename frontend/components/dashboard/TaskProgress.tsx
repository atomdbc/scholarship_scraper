// components/dashboard/TaskProgress.tsx
import { Progress } from '../common/Progress';
import type { TaskProgress as TaskProgressType } from '../../lib/types';

interface TaskProgressProps {
  tasks: TaskProgressType[];
}

export const TaskProgress = ({ tasks }: TaskProgressProps) => {
  return (
    <div className="space-y-4">
      {tasks.map((task) => (
        <Card key={task.task_id} className="p-4">
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <p className="font-medium truncate" title={task.url}>
                {task.url}
              </p>
              <span className={`px-2 py-1 rounded text-sm ${
                task.status === 'completed' ? 'bg-green-100 text-green-800' :
                task.status === 'failed' ? 'bg-red-100 text-red-800' :
                task.status === 'in_progress' ? 'bg-yellow-100 text-yellow-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {task.status}
              </span>
            </div>
            <Progress value={task.progress_percentage} />
            <div className="flex justify-between text-sm text-gray-500">
              <span>{task.processed_links} / {task.total_links} links</span>
              <span>{task.scholarships_found} scholarships found</span>
            </div>
            {task.error_message && (
              <p className="text-sm text-red-500 mt-2">{task.error_message}</p>
            )}
            {task.processing_duration && (
              <p className="text-sm text-gray-500">
                Duration: {task.processing_duration}
              </p>
            )}
          </div>
        </Card>
      ))}
    </div>
  );
};
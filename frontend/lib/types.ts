// lib/types.ts
export interface ScrapingStatus {
  total_tasks: number;
  pending: number;
  completed: number;
  in_progress: number;
  failed: number;
  total_scholarships: number;
  average_confidence_score: number;
  last_update: string;
  processing_rate: number;
  success_rate: number;
  system_uptime: string;
  tasks_progress: TaskProgress[];
}

export interface TaskProgress {
  task_id: number;
  url: string;
  status: string;
  total_links: number;
  processed_links: number;
  scholarships_found: number;
  progress_percentage: number;
  start_time?: string;
  end_time?: string;
  error_message?: string;
  processing_duration?: string;
  success_count: number;
  fail_count: number;
  created_at: string;
  last_run?: string;
  next_run?: string;
}

export interface Scholarship {
  id: number;
  title: string;
  amount: string;
  deadline?: string;
  field_of_study: string;
  level_of_study: string;
  eligibility_criteria: string;
  application_url: string;
  source_url: string;
  confidence_score: number;
  ai_summary?: any;
  last_updated: string;
  task_id: number;
}

export interface ScholarshipStats {
  total_count: number;
  average_confidence: number;
  by_field_of_study: Record<string, number>;
  by_level_of_study: Record<string, number>;
  recent_additions: Scholarship[];
  daily_counts: Record<string, number>;
  amount_ranges: Record<string, number>;
  deadline_distribution: Record<string, number>;
}
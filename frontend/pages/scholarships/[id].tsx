import { useRouter } from 'next/router';
import { useEffect, useState } from 'react';
import { api } from '../../lib/api';
import { Loading } from '../../components/common/Loading';
import { Button } from '../../components/common/Button';
import { Card } from '../../components/common/Card';
import { Badge } from '../../components/common/badge';
import type { Scholarship } from '../../lib/types';
import { 
  ArrowLeft, 
  ExternalLink, 
  Award, 
  Calendar, 
  Book, 
  GraduationCap, 
  Target, 
  Brain,
  DollarSign,
  ClipboardCheck,
  AlertCircle,
  CheckCircle2,
  Timer
} from 'lucide-react';

export default function ScholarshipDetail() {
  const router = useRouter();
  const { id } = router.query;
  const [scholarship, setScholarship] = useState<Scholarship | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) {
      api.getScholarship(id as string)
        .then(setScholarship)
        .catch(console.error)
        .finally(() => setLoading(false));
    }
  }, [id]);

  const parseAiSummary = (summary: any) => {
    try {
      if (typeof summary === 'string') {
        return JSON.parse(summary);
      }
      return summary;
    } catch (error) {
      console.error('Error parsing AI summary:', error);
      return null;
    }
  };

  const formatDate = (date: string | null | undefined) => {
    if (!date) return 'Not specified';
    try {
      return new Date(date).toLocaleDateString();
    } catch (error) {
      return 'Invalid date';
    }
  };

  if (loading || !scholarship) return <Loading />;

  const aiSummary = parseAiSummary(scholarship.ai_summary);

  return (
    <div className="max-w-4xl mx-auto p-4">
      <Button
        variant="ghost"
        onClick={() => router.back()}
        className="mb-6"
      >
        <ArrowLeft className="w-4 h-4 mr-2" />
        Back to List
      </Button>

      <Card className="p-6">
        <div className="border-b pb-4 mb-6">
          <h1 className="text-2xl font-bold mb-2">{scholarship.title}</h1>
          <div className="flex items-center gap-2">
            <Badge variant={scholarship.confidence_score >= 0.8 ? "success" : "warning"}>
              <Brain className="w-4 h-4 mr-1" />
              Confidence: {(scholarship.confidence_score * 100).toFixed(1)}%
            </Badge>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <div className="flex items-start gap-3">
            <Award className="w-5 h-5 text-blue-500 mt-1" />
            <div>
              <h3 className="font-semibold mb-1">Amount</h3>
              <p>{scholarship.amount || 'Not specified'}</p>
              {aiSummary?.amount_analysis?.is_renewable && (
                <Badge variant="outline" className="mt-1">Renewable</Badge>
              )}
            </div>
          </div>
          <div className="flex items-start gap-3">
            <Calendar className="w-5 h-5 text-green-500 mt-1" />
            <div>
              <h3 className="font-semibold mb-1">Deadline</h3>
              <p>{formatDate(scholarship.deadline)}</p>
              {aiSummary?.deadline_info?.is_recurring && (
                <Badge variant="outline" className="mt-1">Recurring</Badge>
              )}
            </div>
          </div>
          <div className="flex items-start gap-3">
            <Book className="w-5 h-5 text-purple-500 mt-1" />
            <div>
              <h3 className="font-semibold mb-1">Field of Study</h3>
              <p>{scholarship.field_of_study || 'Not specified'}</p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <GraduationCap className="w-5 h-5 text-yellow-500 mt-1" />
            <div>
              <h3 className="font-semibold mb-1">Level of Study</h3>
              <p>{scholarship.level_of_study || 'Not specified'}</p>
            </div>
          </div>
        </div>

        {/* Replace the existing AI Analysis section in your ScholarshipDetail component with this: */}

{aiSummary && (
  <div className="space-y-6">
    <div className="bg-gray-50 rounded-lg p-6">
      <h3 className="font-semibold mb-4 flex items-center text-lg border-b pb-2">
        <Brain className="w-5 h-5 mr-2 text-blue-500" />
        AI Analysis Summary
      </h3>
      
      <div className="grid grid-cols-1 gap-6">
        {/* Confidence and Status Section */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-white p-4 rounded-lg shadow-sm">
            <h4 className="font-medium flex items-center mb-3">
              <Brain className="w-4 h-4 mr-2 text-blue-500" />
              Analysis Confidence
            </h4>
            <div className="flex items-center">
              <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                <div 
                  className={`h-full ${
                    aiSummary.confidence_score >= 0.8 ? 'bg-green-500' : 
                    aiSummary.confidence_score >= 0.6 ? 'bg-yellow-500' : 'bg-red-500'
                  }`}
                  style={{ width: `${aiSummary.confidence_score * 100}%` }}
                />
              </div>
              <span className="ml-3 font-medium">
                {(aiSummary.confidence_score * 100).toFixed(0)}%
              </span>
            </div>
          </div>

          <div className="bg-white p-4 rounded-lg shadow-sm">
            <h4 className="font-medium flex items-center mb-2">
              <Timer className="w-4 h-4 mr-2 text-yellow-500" />
              Award Details
            </h4>
            <div className="flex flex-wrap gap-2">
              {aiSummary.amount_analysis.is_renewable && (
                <Badge variant="success" className="text-xs">
                  <CheckCircle2 className="w-3 h-3 mr-1" />
                  Renewable
                </Badge>
              )}
              {aiSummary.deadline_info.is_recurring && (
                <Badge variant="info" className="text-xs">
                  <Calendar className="w-3 h-3 mr-1" />
                  Recurring
                </Badge>
              )}
              <Badge variant={aiSummary.amount_analysis.type !== 'unknown' ? 'secondary' : 'outline'} className="text-xs">
                <DollarSign className="w-3 h-3 mr-1" />
                {aiSummary.amount_analysis.type === 'fixed' ? 'Fixed Amount' : 
                 aiSummary.amount_analysis.type === 'range' ? 'Range Amount' : 'Amount Type Unknown'}
              </Badge>
            </div>
          </div>
        </div>

        {/* Requirements and Conditions Section */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Eligibility Requirements */}
          <div className="bg-white p-4 rounded-lg shadow-sm">
            <h4 className="font-medium flex items-center mb-3">
              <ClipboardCheck className="w-4 h-4 mr-2 text-purple-500" />
              Eligibility Requirements
            </h4>
            <ul className="space-y-2">
              {aiSummary.eligibility_requirements.map((req: string, index: number) => (
                <li key={index} className="flex items-start">
                  <div className="flex-shrink-0 w-5 h-5 rounded-full bg-purple-100 flex items-center justify-center mt-0.5 mr-2">
                    <span className="text-xs text-purple-700">{index + 1}</span>
                  </div>
                  <span className="text-sm text-gray-700">{req}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Award Conditions */}
          {aiSummary.amount_analysis?.conditions?.length > 0 && (
            <div className="bg-white p-4 rounded-lg shadow-sm">
              <h4 className="font-medium flex items-center mb-3">
                <AlertCircle className="w-4 h-4 mr-2 text-blue-500" />
                Award Conditions
              </h4>
              <ul className="space-y-2">
                {aiSummary.amount_analysis.conditions.map((condition: string, index: number) => (
                  <li key={index} className="flex items-start">
                    <div className="flex-shrink-0 w-5 h-5 rounded-full bg-blue-100 flex items-center justify-center mt-0.5 mr-2">
                      <span className="text-xs text-blue-700">{index + 1}</span>
                    </div>
                    <span className="text-sm text-gray-700">{condition}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Study Information */}
        <div className="bg-white p-4 rounded-lg shadow-sm">
          <h4 className="font-medium flex items-center mb-3">
            <Book className="w-4 h-4 mr-2 text-green-500" />
            Study Information
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-500">Field of Study</p>
              <p className="font-medium">{aiSummary.field_of_study}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Level of Study</p>
              <p className="font-medium">{aiSummary.level_of_study}</p>
            </div>
          </div>
        </div>

        {/* Deadline Information */}
        <div className="bg-white p-4 rounded-lg shadow-sm">
          <h4 className="font-medium flex items-center mb-3">
            <Calendar className="w-4 h-4 mr-2 text-red-500" />
            Application Timeline
          </h4>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Application Deadline</p>
              <p className="font-medium">{formatDate(aiSummary.deadline_info.date)}</p>
            </div>
            <Badge variant={aiSummary.deadline_info.is_recurring ? "info" : "default"}>
              {aiSummary.deadline_info.is_recurring ? "Recurring Deadline" : "One-time Deadline"}
            </Badge>
          </div>
        </div>
      </div>
    </div>
  </div>
)}

        <div className="flex justify-between items-center mt-6 pt-4 border-t">
          <span className="text-sm text-gray-500">
            Last updated: {formatDate(scholarship.last_updated)}
          </span>
          {scholarship.application_url && (
            <a
              href={scholarship.application_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex"
            >
              <Button>
                Apply Now
                <ExternalLink className="w-4 h-4 ml-2" />
              </Button>
            </a>
          )}
        </div>
      </Card>
    </div>
  );
}
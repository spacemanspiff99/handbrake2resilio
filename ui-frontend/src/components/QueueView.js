import {
    AlertCircle,
    CheckCircle,
    Clock,
    Play,
    RefreshCw,
    XCircle
} from 'lucide-react';
import React, { useState } from 'react';
import toast from 'react-hot-toast';
import { useMutation, useQuery, useQueryClient } from 'react-query';
import { queueAPI } from '../services/api';

const QueueView = () => {
  const [selectedJobs, setSelectedJobs] = useState(new Set());
  const queryClient = useQueryClient();

  const { data: queueStatus, isLoading: queueLoading } = useQuery(
    'queueStatus',
    queueAPI.getQueueStatus,
    {
      refetchInterval: 3000,
    }
  );

  const { data: jobs, isLoading: jobsLoading } = useQuery(
    'jobs',
    queueAPI.getAllJobs,
    {
      refetchInterval: 5000,
    }
  );

  const cancelJobMutation = useMutation(queueAPI.cancelJob, {
    onSuccess: () => {
      queryClient.invalidateQueries('jobs');
      queryClient.invalidateQueries('queueStatus');
      toast.success('Job cancelled successfully');
    },
    onError: (error) => {
      toast.error(error.response?.data?.error || 'Failed to cancel job');
    },
  });

  const retryJobMutation = useMutation(queueAPI.retryJob, {
    onSuccess: () => {
      queryClient.invalidateQueries('jobs');
      queryClient.invalidateQueries('queueStatus');
      toast.success('Job queued for retry');
    },
    onError: (error) => {
      toast.error(error.response?.data?.error || 'Failed to retry job');
    },
  });

  const clearCompletedMutation = useMutation(queueAPI.clearCompletedJobs, {
    onSuccess: (data) => {
      queryClient.invalidateQueries('jobs');
      toast.success(`Cleared ${data.data.cleared_count} completed jobs`);
    },
    onError: (error) => {
      toast.error(error.response?.data?.error || 'Failed to clear completed jobs');
    },
  });

  const handleCancelJob = (jobId) => {
    if (window.confirm('Are you sure you want to cancel this job?')) {
      cancelJobMutation.mutate(jobId);
    }
  };

  const handleRetryJob = (jobId) => {
    retryJobMutation.mutate(jobId);
  };

  const handleClearCompleted = () => {
    if (window.confirm('Are you sure you want to clear all completed jobs?')) {
      clearCompletedMutation.mutate();
    }
  };

  const getJobStatusIcon = (status) => {
    switch (status) {
      case 'running':
        return <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600" />;
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'pending':
        return <Clock className="h-4 w-4 text-yellow-500" />;
      case 'cancelled':
        return <XCircle className="h-4 w-4 text-gray-500" />;
      default:
        return <Clock className="h-4 w-4 text-gray-400" />;
    }
  };

  const getJobStatusColor = (status) => {
    switch (status) {
      case 'running':
        return 'text-blue-600';
      case 'completed':
        return 'text-green-600';
      case 'failed':
        return 'text-red-600';
      case 'pending':
        return 'text-yellow-600';
      case 'cancelled':
        return 'text-gray-600';
      default:
        return 'text-gray-600';
    }
  };

  const formatFileName = (path) => {
    return path?.split('/').pop() || path || 'Unknown file';
  };

  const formatProgress = (progress) => {
    return `${progress || 0}%`;
  };

  const queueData = queueStatus?.data || queueStatus || {};
  const jobsData = jobs?.data || jobs || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Queue Management</h1>
          <p className="text-gray-600">Monitor and manage conversion jobs</p>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={handleClearCompleted}
            className="bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500"
            disabled={clearCompletedMutation.isLoading}
          >
            {clearCompletedMutation.isLoading ? 'Clearing...' : 'Clear Completed'}
          </button>
        </div>
      </div>

      {/* Queue Status Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Running</p>
              <p className="text-2xl font-bold text-blue-600">
                {queueData?.running || 0}
              </p>
            </div>
            <Play className="h-8 w-8 text-blue-600" />
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Pending</p>
              <p className="text-2xl font-bold text-yellow-600">
                {queueData?.pending || 0}
              </p>
            </div>
            <Clock className="h-8 w-8 text-yellow-600" />
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Completed</p>
              <p className="text-2xl font-bold text-green-600">
                {queueData?.completed || 0}
              </p>
            </div>
            <CheckCircle className="h-8 w-8 text-green-600" />
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Failed</p>
              <p className="text-2xl font-bold text-red-600">
                {queueData?.failed || 0}
              </p>
            </div>
            <XCircle className="h-8 w-8 text-red-600" />
          </div>
        </div>
      </div>

      {/* Jobs List */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">All Jobs</h3>
        </div>
        
        {jobsLoading ? (
          <div className="p-6 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          </div>
        ) : jobsData?.length > 0 ? (
          <div className="divide-y divide-gray-200">
            {jobsData.map((job) => (
              <div key={job.id} className="p-6">
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-3">
                      {getJobStatusIcon(job.status)}
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 truncate">
                          {formatFileName(job.source_path)}
                        </p>
                        <p className="text-xs text-gray-500">
                          {job.source_path} → {job.destination_path}
                        </p>
                      </div>
                    </div>
                    
                    <div className="mt-2 flex items-center space-x-4 text-xs text-gray-500">
                      <span className={`font-medium ${getJobStatusColor(job.status)}`}>
                        {job.status?.toUpperCase() || 'UNKNOWN'}
                      </span>
                      {job.progress > 0 && (
                        <span>Progress: {formatProgress(job.progress)}</span>
                      )}
                      {job.retry_count > 0 && (
                        <span>Retries: {job.retry_count}</span>
                      )}
                      {job.created_at && (
                        <span>Created: {new Date(job.created_at).toLocaleString()}</span>
                      )}
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2 ml-4">
                    {job.status === 'failed' && (
                      <button
                        onClick={() => handleRetryJob(job.id)}
                        className="p-2 text-gray-400 hover:text-blue-600 transition-colors"
                        title="Retry Job"
                        disabled={retryJobMutation.isLoading}
                      >
                        <RefreshCw className="h-4 w-4" />
                      </button>
                    )}
                    {(job.status === 'running' || job.status === 'pending') && (
                      <button
                        onClick={() => handleCancelJob(job.id)}
                        className="p-2 text-gray-400 hover:text-red-600 transition-colors"
                        title="Cancel Job"
                        disabled={cancelJobMutation.isLoading}
                      >
                        <XCircle className="h-4 w-4" />
                      </button>
                    )}
                  </div>
                </div>
                
                {job.error_message && (
                  <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-md">
                    <div className="flex items-center space-x-2">
                      <AlertCircle className="h-4 w-4 text-red-500" />
                      <span className="text-sm text-red-700">
                        Error: {job.error_message}
                      </span>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="p-6 text-center text-gray-500">
            <Clock className="h-12 w-12 mx-auto mb-2 text-gray-300" />
            <p>No jobs in queue</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default QueueView;
import {
    Activity,
    AlertCircle,
    CheckCircle,
    Clock,
    Cpu,
    Database,
    HardDrive,
    Play,
    XCircle
} from 'lucide-react';
import React from 'react';
import { useQuery } from 'react-query';
import { queueAPI, systemAPI } from '../services/api';

const Dashboard = () => {
  console.log('🔧 Dashboard component rendering...');

  const { data: systemLoad, isLoading: systemLoading, error: systemError } = useQuery(
    'systemLoad',
    systemAPI.getSystemLoad,
    {
      refetchInterval: 5000,
      onSuccess: (data) => {
        console.log('✅ System load query successful:', data);
      },
      onError: (error) => {
        console.error('❌ System load query failed:', error);
      }
    }
  );

  const { data: queueStatus, isLoading: queueLoading, error: queueError } = useQuery(
    'queueStatus',
    queueAPI.getQueueStatus,
    {
      refetchInterval: 3000,
      onSuccess: (data) => {
        console.log('✅ Queue status query successful:', data);
      },
      onError: (error) => {
        console.error('❌ Queue status query failed:', error);
      }
    }
  );

  const { data: jobs, error: jobsError } = useQuery(
    'jobs',
    queueAPI.getAllJobs,
    {
      refetchInterval: 5000,
      onSuccess: (data) => {
        console.log('✅ Jobs query successful:', data);
      },
      onError: (error) => {
        console.error('❌ Jobs query failed:', error);
      }
    }
  );

  React.useEffect(() => {
    console.log('🔧 Dashboard component mounted');
    console.log('🔧 Current state:', {
      systemLoad,
      systemLoading,
      systemError,
      queueStatus,
      queueLoading,
      queueError,
      jobs,
      jobsError
    });
  }, [systemLoad, systemLoading, systemError, queueStatus, queueLoading, queueError, jobs, jobsError]);

  const getSystemStatusColor = () => {
    if (!systemLoad) return 'text-gray-400';
    const { cpu_percent, memory_percent } = systemLoad.data || systemLoad;
    if (cpu_percent > 80 || memory_percent > 80) return 'text-red-500';
    if (cpu_percent > 60 || memory_percent > 60) return 'text-yellow-500';
    return 'text-green-500';
  };

  const getQueueStatusColor = () => {
    if (!queueStatus) return 'text-gray-400';
    const { running, pending } = queueStatus.data || queueStatus;
    if (running > 0) return 'text-yellow-500';
    if (pending > 0) return 'text-blue-500';
    return 'text-green-500';
  };

  const getRecentJobs = () => {
    const jobsData = jobs?.data || jobs?.jobs || [];
    if (!jobsData) return [];
    return jobsData.slice(0, 5); // Show last 5 jobs
  };

  const systemData = systemLoad?.data || systemLoad || {};
  const queueData = queueStatus?.data || queueStatus || {};

  console.log('🔧 Dashboard render data:', {
    systemData,
    queueData,
    recentJobs: getRecentJobs()
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600">System overview and quick actions</p>
      </div>

      {/* System Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* CPU Usage */}
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">CPU Usage</p>
              <p className="text-2xl font-bold text-gray-900">
                {systemLoading ? '...' : `${systemData?.cpu_percent || 0}%`}
              </p>
            </div>
            <Cpu className={`h-8 w-8 ${getSystemStatusColor()}`} />
          </div>
          <div className="mt-4">
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${systemData?.cpu_percent || 0}%` }}
              ></div>
            </div>
          </div>
        </div>

        {/* Memory Usage */}
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Memory Usage</p>
              <p className="text-2xl font-bold text-gray-900">
                {systemLoading ? '...' : `${systemData?.memory_percent || 0}%`}
              </p>
            </div>
            <Database className={`h-8 w-8 ${getSystemStatusColor()}`} />
          </div>
          <div className="mt-4">
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${systemData?.memory_percent || 0}%` }}
              ></div>
            </div>
          </div>
        </div>

        {/* Queue Status */}
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Queue Status</p>
              <p className="text-2xl font-bold text-gray-900">
                {queueLoading ? '...' : `${queueData?.running || 0} running`}
              </p>
              <p className="text-sm text-gray-500">
                {queueData?.pending || 0} pending
              </p>
            </div>
            <Activity className={`h-8 w-8 ${getQueueStatusColor()}`} />
          </div>
        </div>

        {/* HandBrake Processes */}
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">HandBrake Processes</p>
              <p className="text-2xl font-bold text-gray-900">
                {systemLoading ? '...' : systemData?.handbrake_processes || 0}
              </p>
            </div>
            <HardDrive className="h-8 w-8 text-blue-500" />
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Jobs */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Jobs</h3>
                           {getRecentJobs().length > 0 ? (
            <div className="space-y-3">
              {getRecentJobs().map((job) => (
                <div key={job.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {job.source_path?.split('/').pop() || `Job ${job.id}`}
                    </p>
                    <p className="text-xs text-gray-500">
                      {job.status} • {job.progress}% complete
                    </p>
                  </div>
                  <div className="flex items-center space-x-2">
                    {job.status === 'running' && (
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                    )}
                    {job.status === 'completed' && (
                      <CheckCircle className="h-4 w-4 text-green-500" />
                    )}
                    {job.status === 'failed' && (
                      <XCircle className="h-4 w-4 text-red-500" />
                    )}
                    {job.status === 'pending' && (
                      <Clock className="h-4 w-4 text-yellow-500" />
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <Clock className="h-12 w-12 mx-auto mb-2 text-gray-300" />
              <p>No recent jobs</p>
            </div>
          )}
        </div>

        {/* System Health */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">System Health</h3>
          <div className="space-y-4">
            {/* CPU Health */}
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">CPU</span>
              <div className="flex items-center space-x-2">
                {systemData?.cpu_percent > 80 ? (
                  <AlertCircle className="h-4 w-4 text-red-500" />
                ) : systemData?.cpu_percent > 60 ? (
                  <AlertCircle className="h-4 w-4 text-yellow-500" />
                ) : (
                  <CheckCircle className="h-4 w-4 text-green-500" />
                )}
                <span className="text-sm font-medium">
                  {systemData?.cpu_percent || 0}%
                </span>
              </div>
            </div>

            {/* Memory Health */}
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Memory</span>
              <div className="flex items-center space-x-2">
                {systemData?.memory_percent > 80 ? (
                  <AlertCircle className="h-4 w-4 text-red-500" />
                ) : systemData?.memory_percent > 60 ? (
                  <AlertCircle className="h-4 w-4 text-yellow-500" />
                ) : (
                  <CheckCircle className="h-4 w-4 text-green-500" />
                )}
                <span className="text-sm font-medium">
                  {systemData?.memory_percent || 0}%
                </span>
              </div>
            </div>

            {/* Disk Health */}
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Disk</span>
              <div className="flex items-center space-x-2">
                {systemData?.disk_percent > 90 ? (
                  <AlertCircle className="h-4 w-4 text-red-500" />
                ) : systemData?.disk_percent > 80 ? (
                  <AlertCircle className="h-4 w-4 text-yellow-500" />
                ) : (
                  <CheckCircle className="h-4 w-4 text-green-500" />
                )}
                <span className="text-sm font-medium">
                  {systemData?.disk_percent || 0}%
                </span>
              </div>
            </div>

            {/* Queue Health */}
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Queue</span>
              <div className="flex items-center space-x-2">
                {queueData?.failed > 0 ? (
                  <AlertCircle className="h-4 w-4 text-red-500" />
                ) : queueData?.running > 0 ? (
                  <Play className="h-4 w-4 text-yellow-500" />
                ) : (
                  <CheckCircle className="h-4 w-4 text-green-500" />
                )}
                <span className="text-sm font-medium">
                  {queueData?.running || 0} running
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
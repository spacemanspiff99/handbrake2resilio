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
  const { data: health, isLoading: healthLoading } = useQuery(
    'health',
    systemAPI.getHealth,
    {
      refetchInterval: 10000,
    }
  );

  const { data: systemLoad, isLoading: systemLoading, error: systemError } = useQuery(
    'systemLoad',
    systemAPI.getSystemLoad,
    {
      refetchInterval: 5000,
      onError: (err) => {
        console.error('System load query failed:', err);
      },
    }
  );

  const { data: queueStatus, isLoading: queueLoading, error: queueError } = useQuery(
    'queueStatus',
    queueAPI.getQueueStatus,
    {
      refetchInterval: 3000,
      onError: (err) => {
        console.error('Queue status query failed:', err);
      },
    }
  );

  const { data: jobs, error: jobsError } = useQuery(
    'jobs',
    queueAPI.getAllJobs,
    {
      refetchInterval: 5000,
      onError: (err) => {
        console.error('Jobs query failed:', err);
      },
    }
  );

  const getSystemStatusColor = () => {
    const data = systemLoad?.data || systemLoad || {};
    const { cpu_percent, memory_percent } = data;
    if (cpu_percent === undefined) return 'text-gray-400';
    if (cpu_percent > 80 || memory_percent > 80) return 'text-red-500';
    if (cpu_percent > 60 || memory_percent > 60) return 'text-yellow-500';
    return 'text-green-500';
  };

  const getQueueStatusColor = () => {
    const data = queueStatus?.data || queueStatus || {};
    const { running, pending } = data;
    if (running === undefined) return 'text-gray-400';
    if (running > 0) return 'text-yellow-500';
    if (pending > 0) return 'text-blue-500';
    return 'text-green-500';
  };

  const getRecentJobs = () => {
    const jobsData = jobs?.data || jobs?.jobs || (Array.isArray(jobs) ? jobs : []);
    if (!Array.isArray(jobsData)) return [];
    return jobsData.slice(0, 5);
  };

  const systemData = systemLoad?.data || systemLoad || {};
  const queueData = queueStatus?.data || queueStatus || {};
  const healthData =
    health && typeof health === 'object' && !Array.isArray(health) ? health : {};

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600">System overview and quick actions</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">API health</p>
              <p className="text-2xl font-bold text-gray-900">
                {healthLoading
                  ? '...'
                  : healthData?.status === 'healthy'
                    ? 'Healthy'
                    : healthData?.status || 'Unknown'}
              </p>
              <p className="text-sm text-gray-500">
                {healthData?.database
                  ? typeof healthData.database === 'string'
                    ? `DB: ${healthData.database}`
                    : 'DB: ok'
                  : ''}
              </p>
            </div>
            <Database
              className={`h-8 w-8 ${
                healthData?.status === 'healthy' ? 'text-green-500' : 'text-gray-400'
              }`}
            />
          </div>
        </div>

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
              />
            </div>
          </div>
        </div>

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
              />
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Queue Status</p>
              <p className="text-2xl font-bold text-gray-900">
                {queueLoading ? '...' : `${queueData?.running || 0} running`}
              </p>
              <p className="text-sm text-gray-500">{queueData?.pending || 0} pending</p>
            </div>
            <Activity className={`h-8 w-8 ${getQueueStatusColor()}`} />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">HandBrake Processes</p>
              <p className="text-2xl font-bold text-gray-900">
                {systemLoading ? '...' : systemData?.handbrake_processes ?? 0}
              </p>
            </div>
            <HardDrive className="h-8 w-8 text-blue-500" />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Jobs</h3>
          {getRecentJobs().length > 0 ? (
            <div className="space-y-3">
              {getRecentJobs().map((job) => (
                <div key={job.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {(job.input_path || job.source_path)?.split('/').pop() || `Job ${job.id}`}
                    </p>
                    <p className="text-xs text-gray-500">
                      {job.status} • {job.progress ?? 0}% complete
                    </p>
                  </div>
                  <div className="flex items-center space-x-2">
                    {job.status === 'running' && (
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600" />
                    )}
                    {job.status === 'completed' && (
                      <CheckCircle className="h-4 w-4 text-green-500" />
                    )}
                    {job.status === 'failed' && <XCircle className="h-4 w-4 text-red-500" />}
                    {job.status === 'pending' && <Clock className="h-4 w-4 text-yellow-500" />}
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

        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">System Health</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">API gateway</span>
              <div className="flex items-center space-x-2">
                {healthData?.status === 'healthy' ? (
                  <CheckCircle className="h-4 w-4 text-green-500" />
                ) : (
                  <AlertCircle className="h-4 w-4 text-red-500" />
                )}
                <span className="text-sm font-medium">{healthData?.status || '—'}</span>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Database</span>
              <div className="flex items-center space-x-2">
                {typeof healthData?.database === 'string' &&
                healthData.database.toLowerCase().includes('error') ? (
                  <AlertCircle className="h-4 w-4 text-red-500" />
                ) : healthData?.database ? (
                  <CheckCircle className="h-4 w-4 text-green-500" />
                ) : (
                  <AlertCircle className="h-4 w-4 text-gray-400" />
                )}
                <span className="text-sm font-medium">
                  {typeof healthData?.database === 'string'
                    ? healthData.database
                    : healthData?.database
                      ? 'ok'
                      : '—'}
                </span>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">HandBrake service</span>
              <div className="flex items-center space-x-2">
                {healthData?.handbrake_service ? (
                  <CheckCircle className="h-4 w-4 text-green-500" />
                ) : (
                  <AlertCircle className="h-4 w-4 text-yellow-500" />
                )}
                <span className="text-sm font-medium">
                  {healthData?.handbrake_service ? 'Reachable' : 'Unreachable'}
                </span>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Disk (host)</span>
              <div className="flex items-center space-x-2">
                {systemData?.disk_percent > 90 ? (
                  <AlertCircle className="h-4 w-4 text-red-500" />
                ) : systemData?.disk_percent > 80 ? (
                  <AlertCircle className="h-4 w-4 text-yellow-500" />
                ) : (
                  <CheckCircle className="h-4 w-4 text-green-500" />
                )}
                <span className="text-sm font-medium">{systemData?.disk_percent ?? 0}%</span>
              </div>
            </div>

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
                <span className="text-sm font-medium">{queueData?.running || 0} running</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {(systemError || queueError || jobsError) && (
        <p className="text-sm text-amber-700">
          Some dashboard data could not be loaded. Check the browser console for details.
        </p>
      )}
    </div>
  );
};

export default Dashboard;

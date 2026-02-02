import {
    Activity,
    AlertCircle,
    CheckCircle,
    Cpu,
    Database,
    FileText,
    HardDrive,
    Server,
    Settings
} from 'lucide-react';
import React from 'react';
import { useQuery } from 'react-query';
import { systemAPI } from '../services/api';

const SystemView = () => {
  const { data: systemLoad, isLoading: systemLoading } = useQuery(
    'systemLoad',
    systemAPI.getSystemLoad,
    {
      refetchInterval: 5000,
    }
  );

  const { data: health, isLoading: healthLoading } = useQuery(
    'health',
    systemAPI.getHealth,
    {
      refetchInterval: 10000,
    }
  );

  const { data: processes, isLoading: processesLoading } = useQuery(
    'processes',
    systemAPI.getProcesses,
    {
      refetchInterval: 5000,
    }
  );

  const { data: logs, isLoading: logsLoading } = useQuery(
    'logs',
    systemAPI.getRecentLogs,
    {
      refetchInterval: 10000,
    }
  );

  const { data: config, isLoading: configLoading } = useQuery(
    'config',
    systemAPI.getConfig,
    {
      refetchInterval: 30000,
    }
  );

  const { data: diskUsage, isLoading: diskLoading } = useQuery(
    'diskUsage',
    systemAPI.getDiskUsage,
    {
      refetchInterval: 30000,
    }
  );

  const getHealthStatusColor = () => {
    if (!health) return 'text-gray-400';
    const healthData = health.data || health;
    return healthData?.status === 'healthy' ? 'text-green-500' : 'text-red-500';
  };

  const getHealthStatusIcon = () => {
    if (!health) return <AlertCircle className="h-4 w-4" />;
    const healthData = health.data || health;
    return healthData?.status === 'healthy' ? (
      <CheckCircle className="h-4 w-4" />
    ) : (
      <AlertCircle className="h-4 w-4" />
    );
  };

  const systemData = systemLoad?.data || systemLoad || {};
  const healthData = health?.data || health || {};
  const processesData = processes?.data || processes || {};
  const logsData = logs?.data || logs || {};
  const configData = config?.data || config || {};
  const diskData = diskUsage?.data || diskUsage || {};

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">System Monitoring</h1>
        <p className="text-gray-600">Monitor system health and configuration</p>
      </div>

      {/* System Health */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Health Status */}
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">System Health</p>
              <p className={`text-2xl font-bold ${getHealthStatusColor()}`}>
                {healthLoading ? '...' : healthData?.status || 'Unknown'}
              </p>
            </div>
            <div className={getHealthStatusColor()}>
              {getHealthStatusIcon()}
            </div>
          </div>
          {healthData?.warnings && healthData.warnings.length > 0 && (
            <div className="mt-3 p-2 bg-yellow-50 border border-yellow-200 rounded-md">
              <p className="text-xs text-yellow-700">
                {healthData.warnings[0]}
              </p>
            </div>
          )}
        </div>

        {/* CPU Usage */}
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">CPU Usage</p>
              <p className="text-2xl font-bold text-gray-900">
                {systemLoading ? '...' : `${systemData?.cpu_percent || 0}%`}
              </p>
            </div>
            <Cpu className="h-8 w-8 text-blue-500" />
          </div>
          <div className="mt-4">
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className={`h-2 rounded-full transition-all duration-300 ${
                  (systemData?.cpu_percent || 0) > 80 ? 'bg-red-500' :
                  (systemData?.cpu_percent || 0) > 60 ? 'bg-yellow-500' : 'bg-green-500'
                }`}
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
              <p className="text-xs text-gray-500">
                {systemData ? `${systemData.memory_used_gb?.toFixed(1) || 0} / ${systemData.memory_total_gb?.toFixed(1) || 0} GB` : ''}
              </p>
            </div>
            <Database className="h-8 w-8 text-green-500" />
          </div>
          <div className="mt-4">
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className={`h-2 rounded-full transition-all duration-300 ${
                  (systemData?.memory_percent || 0) > 80 ? 'bg-red-500' :
                  (systemData?.memory_percent || 0) > 60 ? 'bg-yellow-500' : 'bg-green-500'
                }`}
                style={{ width: `${systemData?.memory_percent || 0}%` }}
              ></div>
            </div>
          </div>
        </div>

        {/* Disk Usage */}
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Disk Usage</p>
              <p className="text-2xl font-bold text-gray-900">
                {diskLoading ? '...' : `${diskData?.main?.percent || systemData?.disk_percent || 0}%`}
              </p>
              <p className="text-xs text-gray-500">
                {diskData?.main ? `${diskData.main.free_gb?.toFixed(1)} GB free` : ''}
              </p>
            </div>
            <HardDrive className="h-8 w-8 text-purple-500" />
          </div>
          <div className="mt-4">
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className={`h-2 rounded-full transition-all duration-300 ${
                  (diskData?.main?.percent || systemData?.disk_percent || 0) > 90 ? 'bg-red-500' :
                  (diskData?.main?.percent || systemData?.disk_percent || 0) > 80 ? 'bg-yellow-500' : 'bg-green-500'
                }`}
                style={{ width: `${diskData?.main?.percent || systemData?.disk_percent || 0}%` }}
              ></div>
            </div>
          </div>
        </div>
      </div>

      {/* Configuration and Processes */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Configuration */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <Settings className="h-5 w-5 mr-2" />
            Configuration
          </h3>
          {configLoading ? (
            <div className="text-center py-4">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            </div>
          ) : (
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Scan Interval</span>
                <span className="text-sm font-medium">{configData?.scan_interval || 60}s</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Max Concurrent Jobs</span>
                <span className="text-sm font-medium">{configData?.max_concurrent_jobs || 2}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">CPU Limit</span>
                <span className="text-sm font-medium">{configData?.cpu_limit || 80}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Memory Limit</span>
                <span className="text-sm font-medium">{configData?.memory_limit || 80}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Log Retention</span>
                <span className="text-sm font-medium">{configData?.log_retention_days || 7} days</span>
              </div>
            </div>
          )}
        </div>

        {/* HandBrake Processes */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <Activity className="h-5 w-5 mr-2" />
            HandBrake Processes
          </h3>
          {processesLoading ? (
            <div className="text-center py-4">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            </div>
          ) : processesData?.handbrake_processes?.length > 0 ? (
            <div className="space-y-3">
              {processesData.handbrake_processes.map((process, index) => (
                <div key={index} className="p-3 bg-gray-50 rounded-lg">
                  <div className="flex justify-between items-center">
                    <div>
                      <p className="text-sm font-medium">PID {process.pid}</p>
                      <p className="text-xs text-gray-500">
                        CPU: {process.cpu_percent}% | Memory: {process.memory_percent}%
                      </p>
                    </div>
                    <div className="text-xs text-gray-500">
                      {new Date(process.create_time).toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-4 text-gray-500">
              <Server className="h-8 w-8 mx-auto mb-2 text-gray-300" />
              <p>No HandBrake processes running</p>
            </div>
          )}
        </div>
      </div>

      {/* Recent Logs */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <FileText className="h-5 w-5 mr-2" />
          Recent Logs
        </h3>
        {logsLoading ? (
          <div className="text-center py-4">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          </div>
        ) : logsData?.logs?.length > 0 ? (
          <div className="bg-gray-900 text-gray-100 p-4 rounded-lg font-mono text-sm overflow-x-auto">
            {logsData.logs.map((log, index) => (
              <div key={index} className="mb-1">
                {log}
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-4 text-gray-500">
            <FileText className="h-8 w-8 mx-auto mb-2 text-gray-300" />
            <p>No logs available</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default SystemView;
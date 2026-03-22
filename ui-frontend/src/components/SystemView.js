import { AlertCircle, CheckCircle, Database, Server } from 'lucide-react';
import React from 'react';
import { useQuery } from 'react-query';
import { systemAPI } from '../services/api';

const SystemView = () => {
  const { data: health, isLoading: healthLoading, error } = useQuery(
    'health',
    systemAPI.getHealth,
    {
      refetchInterval: 10000,
    }
  );

  const healthData =
    health && typeof health === 'object' && !Array.isArray(health) ? health : {};

  const statusOk = healthData?.status === 'healthy' && !error;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">System Monitoring</h1>
        <p className="text-gray-600">API gateway health (from /health)</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Gateway status</p>
              <p
                className={`text-2xl font-bold ${
                  healthLoading ? 'text-gray-400' : statusOk ? 'text-green-600' : 'text-red-600'
                }`}
              >
                {healthLoading ? '…' : healthData?.status || (error ? 'unavailable' : 'Unknown')}
              </p>
            </div>
            <div className={statusOk ? 'text-green-500' : 'text-red-500'}>
              {healthLoading ? (
                <Server className="h-8 w-8 text-gray-300" />
              ) : statusOk ? (
                <CheckCircle className="h-8 w-8" />
              ) : (
                <AlertCircle className="h-8 w-8" />
              )}
            </div>
          </div>
          {healthData?.service && (
            <p className="mt-2 text-sm text-gray-500">Service: {healthData.service}</p>
          )}
          {healthData?.version && (
            <p className="text-sm text-gray-500">Version: {healthData.version}</p>
          )}
          {healthData?.timestamp && (
            <p className="text-xs text-gray-400 mt-2">
              Last check: {new Date(healthData.timestamp).toLocaleString()}
            </p>
          )}
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center">
              <Database className="h-5 w-5 mr-2" />
              Dependencies
            </h3>
          </div>
          <ul className="space-y-3 text-sm">
            <li className="flex justify-between">
              <span className="text-gray-600">Database</span>
              <span className="font-medium text-gray-900">
                {healthLoading
                  ? '…'
                  : typeof healthData?.database === 'string'
                    ? healthData.database
                    : healthData?.database
                      ? 'ok'
                      : '—'}
              </span>
            </li>
            <li className="flex justify-between">
              <span className="text-gray-600">HandBrake service reachable</span>
              <span className="font-medium text-gray-900">
                {healthLoading ? '…' : healthData?.handbrake_service ? 'Yes' : 'No'}
              </span>
            </li>
          </ul>
          {healthData?.handbrake_status && (
            <div className="mt-4 p-3 bg-gray-50 rounded-md text-xs text-gray-700 overflow-x-auto font-mono">
              <pre className="whitespace-pre-wrap break-all">
                {JSON.stringify(healthData.handbrake_status, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-sm text-red-800">
          Could not load health data. Is the API gateway running and proxied correctly?
        </div>
      )}
    </div>
  );
};

export default SystemView;

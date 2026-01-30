import {
    Activity,
    Cpu,
    Database,
    HardDrive,
    Monitor,
    RefreshCw
} from 'lucide-react';
import React from 'react';
import { useQuery } from 'react-query';
import { useLocation, useNavigate } from 'react-router-dom';
import { systemAPI } from '../services/api';

const Header = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const { data: systemLoad, isLoading } = useQuery(
    'systemLoad',
    systemAPI.getSystemLoad,
    {
      refetchInterval: 5000, // Refresh every 5 seconds
    }
  );

  const { data: queueStatus } = useQuery(
    'queueStatus',
    () => systemAPI.getQueueStatus(),
    {
      refetchInterval: 3000, // Refresh every 3 seconds
    }
  );

  const getSystemStatusColor = () => {
    if (!systemLoad) return 'text-gray-400';
    const { cpu_percent, memory_percent } = systemLoad;
    if (cpu_percent > 80 || memory_percent > 80) return 'text-error-500';
    if (cpu_percent > 60 || memory_percent > 60) return 'text-warning-500';
    return 'text-success-500';
  };

  const getQueueStatusColor = () => {
    if (!queueStatus) return 'text-gray-400';
    const { running, pending } = queueStatus;
    if (running > 0) return 'text-warning-500';
    if (pending > 0) return 'text-primary-500';
    return 'text-success-500';
  };

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo and Title */}
          <div className="flex items-center">
            <Monitor className="h-8 w-8 text-primary-600" />
            <h1 className="ml-3 text-xl font-semibold text-gray-900">
              HandBrake2Resilio UI
            </h1>
          </div>

          {/* System Indicators */}
          <div className="flex items-center space-x-6">
            {/* CPU Usage */}
            <div className="flex items-center space-x-2">
              <Cpu className="h-4 w-4 text-gray-400" />
              <span className="text-sm text-gray-600">
                CPU: {isLoading ? '...' : `${systemLoad?.cpu_percent || 0}%`}
              </span>
            </div>

            {/* Memory Usage */}
            <div className="flex items-center space-x-2">
              <Database className="h-4 w-4 text-gray-400" />
              <span className="text-sm text-gray-600">
                RAM: {isLoading ? '...' : `${systemLoad?.memory_percent || 0}%`}
              </span>
            </div>

            {/* Queue Status */}
            <div className="flex items-center space-x-2">
              <Activity className={`h-4 w-4 ${getQueueStatusColor()}`} />
              <span className="text-sm text-gray-600">
                Queue: {queueStatus?.running || 0} running, {queueStatus?.pending || 0} pending
              </span>
            </div>

            {/* HandBrake Processes */}
            <div className="flex items-center space-x-2">
              <HardDrive className="h-4 w-4 text-gray-400" />
              <span className="text-sm text-gray-600">
                HandBrake: {systemLoad?.handbrake_processes || 0}
              </span>
            </div>

            {/* Navigation */}
            <div className="flex items-center space-x-2">
              <button
                onClick={() => navigate('/')}
                className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
                  location.pathname === '/'
                    ? 'bg-primary-100 text-primary-700'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Dashboard
              </button>
              <button
                onClick={() => navigate('/queue')}
                className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
                  location.pathname === '/queue'
                    ? 'bg-primary-100 text-primary-700'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Queue
              </button>
              <button
                onClick={() => navigate('/system')}
                className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
                  location.pathname === '/system'
                    ? 'bg-primary-100 text-primary-700'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                System
              </button>
            </div>

            {/* Refresh Button */}
            <button
              onClick={() => window.location.reload()}
              className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
              title="Refresh"
            >
              <RefreshCw className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
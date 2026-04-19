import React, { useState, useEffect } from 'react';
import { useMutation, useQueryClient } from 'react-query';
import { queueAPI, filesystemAPI } from '../services/api';
import FileBrowser from './common/FileBrowser';
import { X, HardDrive } from 'lucide-react';
import toast from 'react-hot-toast';

/**
 * Paths the user sees and types are always host paths (e.g. /mnt/tv/show.mkv).
 * On submit we translate host → container path before sending to the API.
 *
 * roots.input  = { host_path: '/mnt/tv',                    path: '/media/input'  }
 * roots.output = { host_path: '/mnt/archive/Resilio_sync',  path: '/media/output' }
 */
const toContainerPath = (hostPath, roots) => {
  if (!roots || !hostPath) return hostPath;
  if (hostPath.startsWith(roots.input.host_path)) {
    return hostPath.replace(roots.input.host_path, roots.input.path);
  }
  if (hostPath.startsWith(roots.output.host_path)) {
    return hostPath.replace(roots.output.host_path, roots.output.path);
  }
  // Already a container path (e.g. user typed /media/input/…)
  return hostPath;
};

const toHostPath = (containerPath, roots) => {
  if (!roots || !containerPath) return containerPath;
  if (containerPath.startsWith(roots.input.path)) {
    return containerPath.replace(roots.input.path, roots.input.host_path);
  }
  if (containerPath.startsWith(roots.output.path)) {
    return containerPath.replace(roots.output.path, roots.output.host_path);
  }
  return containerPath;
};

const NewJobModal = ({ onClose }) => {
  // State stores host paths — what the user sees
  const [inputHostPath, setInputHostPath] = useState('');
  const [outputHostPath, setOutputHostPath] = useState('');
  const [showInputBrowser, setShowInputBrowser] = useState(false);
  const [showOutputBrowser, setShowOutputBrowser] = useState(false);
  const [roots, setRoots] = useState(null);
  const [quality, setQuality] = useState(23);
  const [profile, setProfile] = useState('standard');

  const queryClient = useQueryClient();

  useEffect(() => {
    filesystemAPI.roots()
      .then((data) => { if (data?.success) setRoots(data.data); })
      .catch(() => {});
  }, []);

  const addJobMutation = useMutation(queueAPI.addToQueue, {
    onSuccess: () => {
      queryClient.invalidateQueries('jobs');
      queryClient.invalidateQueries('queueStatus');
      toast.success('Job added to queue');
      onClose();
    },
    onError: (error) => {
      toast.error(error.response?.data?.error || 'Failed to add job');
    },
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!inputHostPath || !outputHostPath) {
      toast.error('Please select input and output paths');
      return;
    }
    addJobMutation.mutate({
      input_path: toContainerPath(inputHostPath, roots),
      output_path: toContainerPath(outputHostPath, roots),
      quality: Number(quality),
      resolution: profile === 'high' ? '1920x1080' : '1280x720',
    });
  };

  // When the file browser selects a container path, convert it to a host path for display
  const handleInputSelect = (containerPath) => {
    setInputHostPath(toHostPath(containerPath, roots));
    setShowInputBrowser(false);
  };

  const handleOutputSelect = (containerPath) => {
    let base = 'converted_video.mp4';
    if (inputHostPath) {
      const stem = inputHostPath.split('/').pop().split('.').slice(0, -1).join('.') || inputHostPath.split('/').pop();
      base = stem + '.mp4';
    }
    const dir = toHostPath(containerPath, roots);
    setOutputHostPath(dir.endsWith('/') ? dir + base : dir + '/' + base);
    setShowOutputBrowser(false);
  };

  const inputPlaceholder = roots
    ? `e.g. ${roots.input.host_path}/ShowName/episode.mkv`
    : 'Type a path or use Browse…';
  const outputPlaceholder = roots
    ? `e.g. ${roots.output.host_path}/output.mp4`
    : 'Type a path or use Browse…';

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Add New Conversion Job</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-500">
            <X className="h-6 w-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">

          {/* Quick Access */}
          {roots && (
            <div className="flex gap-2 flex-wrap items-center">
              <span className="text-xs text-gray-500 flex items-center gap-1">
                <HardDrive className="h-3 w-3" /> Quick access:
              </span>
              <button
                type="button"
                onClick={() => { setShowInputBrowser(true); setShowOutputBrowser(false); }}
                className="text-xs bg-blue-50 text-blue-700 border border-blue-200 px-2 py-1 rounded hover:bg-blue-100"
              >
                {roots.input.host_path}
              </button>
              <button
                type="button"
                onClick={() => { setShowOutputBrowser(true); setShowInputBrowser(false); }}
                className="text-xs bg-green-50 text-green-700 border border-green-200 px-2 py-1 rounded hover:bg-green-100"
              >
                {roots.output.host_path}
              </button>
            </div>
          )}

          {/* Input File */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Input File</label>
            <div className="flex space-x-2">
              <input
                type="text"
                value={inputHostPath}
                onChange={(e) => setInputHostPath(e.target.value)}
                className="block w-full border-gray-300 rounded-md shadow-sm bg-white px-3 py-2 border focus:outline-none focus:ring-1 focus:ring-blue-500"
                placeholder={inputPlaceholder}
              />
              <button
                type="button"
                onClick={() => { setShowInputBrowser(!showInputBrowser); setShowOutputBrowser(false); }}
                className="bg-gray-100 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-200 border border-gray-300 whitespace-nowrap"
              >
                Browse
              </button>
            </div>
            {showInputBrowser && (
              <div className="mt-2 h-64 border rounded-md">
                <FileBrowser
                  mode="file"
                  startPath="/media/input"
                  onSelect={handleInputSelect}
                />
              </div>
            )}
          </div>

          {/* Output Directory */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Output Directory</label>
            <div className="flex space-x-2">
              <input
                type="text"
                value={outputHostPath}
                onChange={(e) => setOutputHostPath(e.target.value)}
                className="block w-full border-gray-300 rounded-md shadow-sm bg-white px-3 py-2 border focus:outline-none focus:ring-1 focus:ring-blue-500"
                placeholder={outputPlaceholder}
              />
              <button
                type="button"
                onClick={() => { setShowOutputBrowser(!showOutputBrowser); setShowInputBrowser(false); }}
                className="bg-gray-100 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-200 border border-gray-300 whitespace-nowrap"
              >
                Browse
              </button>
            </div>
            {showOutputBrowser && (
              <div className="mt-2 h-64 border rounded-md">
                <FileBrowser
                  mode="directory"
                  startPath="/media/output"
                  onSelect={handleOutputSelect}
                />
              </div>
            )}
          </div>

          {/* Settings */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Profile</label>
              <select
                value={profile}
                onChange={(e) => setProfile(e.target.value)}
                className="block w-full border-gray-300 rounded-md shadow-sm py-2 px-3 border"
              >
                <option value="standard">Standard (720p)</option>
                <option value="high">High (1080p)</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Quality (RF)</label>
              <input
                type="number"
                min="0"
                max="51"
                value={quality}
                onChange={(e) => setQuality(e.target.value)}
                className="block w-full border-gray-300 rounded-md shadow-sm py-2 px-3 border"
              />
            </div>
          </div>

          <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
            <button
              type="button"
              onClick={onClose}
              className="bg-white text-gray-700 px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={addJobMutation.isLoading}
              className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {addJobMutation.isLoading ? 'Starting...' : 'Start Job'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default NewJobModal;

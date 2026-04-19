import React, { useState, useEffect } from 'react';
import { useMutation, useQueryClient } from 'react-query';
import { queueAPI, filesystemAPI } from '../services/api';
import FileBrowser from './common/FileBrowser';
import { X, HardDrive } from 'lucide-react';
import toast from 'react-hot-toast';

const NewJobModal = ({ onClose }) => {
  const [inputPath, setInputPath] = useState('');
  const [outputPath, setOutputPath] = useState('');
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
    if (!inputPath || !outputPath) {
      toast.error('Please select input and output paths');
      return;
    }

    addJobMutation.mutate({
      input_path: inputPath,
      output_path: outputPath,
      quality: Number(quality),
      resolution: profile === 'high' ? '1920x1080' : '1280x720',
    });
  };

  // Build a human-readable path label using host_path when available
  const displayPath = (containerPath, rootKey) => {
    if (!roots || !containerPath) return containerPath;
    const root = roots[rootKey];
    if (!root) return containerPath;
    const relative = containerPath.replace(root.path, '').replace(/^\//, '');
    return relative
      ? `${root.host_path}/${relative}`
      : root.host_path;
  };

  const inputDisplayPath = displayPath(inputPath, 'input');
  const outputDisplayPath = displayPath(outputPath, 'output');

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

          {/* Quick Access shortcuts */}
          {roots && (
            <div className="flex gap-2 flex-wrap">
              <span className="text-xs text-gray-500 flex items-center gap-1 mr-1">
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
                value={inputDisplayPath}
                onChange={(e) => setInputPath(e.target.value)}
                className="block w-full border-gray-300 rounded-md shadow-sm bg-white px-3 py-2 border focus:outline-none focus:ring-1 focus:ring-blue-500"
                placeholder={roots ? `e.g. ${roots.input.host_path}/ShowName/episode.mkv` : 'Type a path or use Browse…'}
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
                  onSelect={(containerPath) => {
                    setInputPath(containerPath);
                    setShowInputBrowser(false);
                  }}
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
                value={outputDisplayPath}
                onChange={(e) => setOutputPath(e.target.value)}
                className="block w-full border-gray-300 rounded-md shadow-sm bg-white px-3 py-2 border focus:outline-none focus:ring-1 focus:ring-blue-500"
                placeholder={roots ? `e.g. ${roots.output.host_path}` : 'Type a path or use Browse…'}
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
                  onSelect={(containerPath) => {
                    let filename = 'converted_video.mp4';
                    if (inputPath) {
                      const base = inputPath.split('/').pop().split('.').slice(0, -1).join('.') || inputPath.split('/').pop();
                      filename = base + '.mp4';
                    }
                    const finalPath = containerPath.endsWith('/') ? containerPath + filename : containerPath + '/' + filename;
                    setOutputPath(finalPath);
                    setShowOutputBrowser(false);
                  }}
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

import React, { useState } from 'react';
import { useMutation, useQueryClient } from 'react-query';
import { queueAPI } from '../services/api';
import FileBrowser from './common/FileBrowser';
import { X, Folder, FileVideo } from 'lucide-react';
import toast from 'react-hot-toast';

const NewJobModal = ({ onClose }) => {
  const [inputPath, setInputPath] = useState('');
  const [outputPath, setOutputPath] = useState('');
  const [showInputBrowser, setShowInputBrowser] = useState(false);
  const [showOutputBrowser, setShowOutputBrowser] = useState(false);
  
  // Default settings
  const [quality, setQuality] = useState(23);
  const [profile, setProfile] = useState('standard');

  const queryClient = useQueryClient();

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
      output_path: outputPath, // HandBrake expects full output path usually, or dir? Service logic implies path.
      quality: Number(quality),
      resolution: profile === 'high' ? '1920x1080' : '1280x720', // Simplified logic
    });
  };

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
          {/* Input Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Input File</label>
            <div className="flex space-x-2">
              <input
                type="text"
                value={inputPath}
                readOnly
                className="block w-full border-gray-300 rounded-md shadow-sm bg-gray-50 px-3 py-2 border"
                placeholder="Select a video file..."
              />
              <button
                type="button"
                onClick={() => { setShowInputBrowser(!showInputBrowser); setShowOutputBrowser(false); }}
                className="bg-gray-100 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-200 border border-gray-300"
              >
                Browse
              </button>
            </div>
            {showInputBrowser && (
              <div className="mt-2 h-64 border rounded-md">
                <FileBrowser
                  mode="file"
                  onSelect={(path) => {
                    setInputPath(path);
                    setShowInputBrowser(false);
                  }}
                />
              </div>
            )}
          </div>

          {/* Output Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Output Directory</label>
            <div className="flex space-x-2">
              <input
                type="text"
                value={outputPath}
                readOnly
                className="block w-full border-gray-300 rounded-md shadow-sm bg-gray-50 px-3 py-2 border"
                placeholder="Select destination folder..."
              />
              <button
                type="button"
                onClick={() => { setShowOutputBrowser(!showOutputBrowser); setShowInputBrowser(false); }}
                className="bg-gray-100 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-200 border border-gray-300"
              >
                Browse
              </button>
            </div>
            {showOutputBrowser && (
              <div className="mt-2 h-64 border rounded-md">
                <FileBrowser
                  mode="directory"
                  onSelect={(path) => {
                    // For now, simple append filename logic would be needed in backend or here.
                    // Assuming backend handles dir or full path. Prompt implies "Output Directory".
                    // Let's assume we append the input filename + .mp4
                    const filename = inputPath.split('/').pop().replace(/\.[^/.]+$/, "") + ".mp4";
                    setOutputPath(path + "/" + filename);
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
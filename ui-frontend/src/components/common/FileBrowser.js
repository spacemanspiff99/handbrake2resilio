import React, { useState, useEffect } from 'react';
import { filesystemAPI } from '../../services/api';
import { Folder, File, ArrowUp, Loader, FolderPlus, X, Check } from 'lucide-react';
import toast from 'react-hot-toast';

const FileBrowser = ({ onSelect, mode = 'file', startPath = '' }) => {
  const [currentPath, setCurrentPath] = useState(startPath);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isCreatingFolder, setIsCreatingFolder] = useState(false);
  const [newFolderName, setNewFolderName] = useState('');

  useEffect(() => {
    loadPath(currentPath);
  }, [currentPath]);

  const loadPath = async (path) => {
    setLoading(true);
    setError(null);
    try {
      // Default to /mnt if path is empty
      const targetPath = path || '/mnt';
      console.log('📂 Browsing path:', targetPath);
      const data = await filesystemAPI.browse(targetPath);
      
      if (data && data.success) {
        setItems(data.data.items);
        setCurrentPath(data.data.current_path);
      } else {
        throw new Error(data?.error || 'Failed to load directory');
      }
    } catch (err) {
      console.error('❌ Failed to load path:', err);
      setError(err.response?.data?.error || err.message || 'Failed to load directory. Access denied or invalid path.');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateFolder = async () => {
    if (!newFolderName.trim()) return;
    
    try {
      const response = await filesystemAPI.mkdir(currentPath, newFolderName);
      if (response.success) {
        toast.success(`Folder "${newFolderName}" created`);
        setNewFolderName('');
        setIsCreatingFolder(false);
        loadPath(currentPath); // Refresh
      } else {
        toast.error(response.error || 'Failed to create folder');
      }
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to create folder');
    }
  };

  const handleItemClick = (item) => {
    if (item.is_directory || item.name === '..') {
      // Use item.path from backend if available, otherwise calculate it
      let targetPath = item.path;
      
      if (item.name === '..' && !targetPath) {
        targetPath = currentPath.split('/').slice(0, -1).join('/') || '/';
      }
      
      console.log('📂 Navigating to:', targetPath);
      loadPath(targetPath);
    } else if (mode === 'file') {
      onSelect(item.path);
    }
  };

  const handleSelectCurrentDir = () => {
    if (mode === 'directory') {
      onSelect(currentPath);
    }
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm h-full flex flex-col">
      <div className="p-3 border-b border-gray-200 flex items-center justify-between bg-gray-50">
        <h3 className="text-sm font-medium text-gray-700 truncate mr-2" title={currentPath}>
          {currentPath || 'Root'}
        </h3>
        <div className="flex items-center space-x-2 shrink-0">
          <button
            onClick={() => setIsCreatingFolder(true)}
            className="p-1 text-gray-500 hover:text-blue-600 transition-colors"
            title="Create New Folder"
          >
            <FolderPlus className="h-4 w-4" />
          </button>
          {mode === 'directory' && (
            <button
              onClick={handleSelectCurrentDir}
              className="text-xs bg-blue-600 text-white px-2 py-1 rounded hover:bg-blue-700 whitespace-nowrap"
            >
              Select
            </button>
          )}
        </div>
      </div>

      {isCreatingFolder && (
        <div className="p-2 border-b border-gray-100 bg-blue-50 flex items-center space-x-2">
          <input
            autoFocus
            type="text"
            value={newFolderName}
            onChange={(e) => setNewFolderName(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleCreateFolder();
              if (e.key === 'Escape') setIsCreatingFolder(false);
            }}
            placeholder="Folder name..."
            className="flex-1 text-sm px-2 py-1 border border-blue-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
          <button
            onClick={handleCreateFolder}
            className="p-1 text-green-600 hover:bg-green-100 rounded"
          >
            <Check className="h-4 w-4" />
          </button>
          <button
            onClick={() => setIsCreatingFolder(false)}
            className="p-1 text-red-600 hover:bg-red-100 rounded"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      <div className="overflow-y-auto flex-1 p-2 scrollbar-thin scrollbar-thumb-gray-300">
        {loading ? (
          <div className="flex justify-center items-center h-32">
            <Loader className="animate-spin h-6 w-6 text-blue-500" />
          </div>
        ) : error ? (
          <div className="text-red-500 text-sm text-center p-4">{error}</div>
        ) : (
          <div className="space-y-0.5">
            {items.map((item, index) => (
              <div
                key={index}
                onClick={() => handleItemClick(item)}
                className={`flex items-center px-2 py-1.5 rounded cursor-pointer hover:bg-blue-50 transition-colors ${
                  item.name === '..' ? 'text-gray-500 border-b border-gray-100 mb-1' : 'text-gray-700'
                }`}
              >
                <div className="mr-3 text-gray-400">
                  {item.name === '..' ? (
                    <ArrowUp className="h-4 w-4" />
                  ) : item.is_directory ? (
                    <Folder className="h-4 w-4 text-blue-400" />
                  ) : (
                    <File className="h-4 w-4 text-gray-400" />
                  )}
                </div>
                <span className="text-sm truncate flex-1">{item.name}</span>
                {item.size && (
                  <span className="text-xs text-gray-400">
                    {(item.size / 1024 / 1024).toFixed(1)} MB
                  </span>
                )}
              </div>
            ))}
            {items.length === 0 && (
              <div className="text-center text-gray-400 text-sm py-4">Empty directory</div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default FileBrowser;
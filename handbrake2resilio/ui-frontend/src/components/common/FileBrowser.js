import React, { useState, useEffect } from 'react';
import { filesystemAPI } from '../../services/api';
import { Folder, File, ArrowUp, Loader } from 'lucide-react';

const FileBrowser = ({ onSelect, mode = 'file', startPath = '' }) => {
  const [currentPath, setCurrentPath] = useState(startPath);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadPath(currentPath);
  }, [currentPath]);

  const loadPath = async (path) => {
    setLoading(true);
    setError(null);
    try {
      const response = await filesystemAPI.browse(path);
      setItems(response.data.items);
      setCurrentPath(response.data.path);
    } catch (err) {
      console.error('Failed to load path:', err);
      setError('Failed to load directory. Access denied or invalid path.');
    } finally {
      setLoading(false);
    }
  };

  const handleItemClick = (item) => {
    if (item.type === 'directory') {
      loadPath(item.path);
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
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm max-h-96 flex flex-col">
      <div className="p-3 border-b border-gray-200 flex items-center justify-between bg-gray-50">
        <h3 className="text-sm font-medium text-gray-700 truncate" title={currentPath}>
          {currentPath || 'Root'}
        </h3>
        {mode === 'directory' && (
          <button
            onClick={handleSelectCurrentDir}
            className="text-xs bg-blue-600 text-white px-2 py-1 rounded hover:bg-blue-700"
          >
            Select This Folder
          </button>
        )}
      </div>

      <div className="overflow-y-auto flex-1 p-2">
        {loading ? (
          <div className="flex justify-center items-center h-32">
            <Loader className="animate-spin h-6 w-6 text-blue-500" />
          </div>
        ) : error ? (
          <div className="text-red-500 text-sm text-center p-4">{error}</div>
        ) : (
          <div className="space-y-1">
            {items.map((item, index) => (
              <div
                key={index}
                onClick={() => handleItemClick(item)}
                className={`flex items-center p-2 rounded cursor-pointer hover:bg-blue-50 ${
                  item.name === '..' ? 'text-gray-500' : 'text-gray-700'
                }`}
              >
                <div className="mr-3 text-gray-400">
                  {item.name === '..' ? (
                    <ArrowUp className="h-4 w-4" />
                  ) : item.type === 'directory' ? (
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
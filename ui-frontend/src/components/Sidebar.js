import {
    ChevronDown,
    ChevronRight,
    Film,
    Folder,
    Plus,
    RefreshCw,
    Settings,
    Trash2,
    Tv,
    Search
} from 'lucide-react';
import React, { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import { useMutation, useQuery, useQueryClient } from 'react-query';
import { tabsAPI, filesystemAPI } from '../services/api';
import FileBrowser from './common/FileBrowser';

const Sidebar = () => {
  const [expandedTabs, setExpandedTabs] = useState(new Set());
  const [expandedShows, setExpandedShows] = useState(new Set());
  const [selectedTab, setSelectedTab] = useState(null);
  const [showAddTab, setShowAddTab] = useState(false);
  const [newTabData, setNewTabData] = useState({
    name: '',
    source_path: '',
    destination_path: '',
    source_type: 'tv'
  });
  
  // Scan Cache State
  const [scanCaches, setScanCaches] = useState({});
  const [scanningPaths, setScanningPaths] = useState(new Set());

  // File Browser State
  const [activeBrowserField, setActiveBrowserField] = useState(null); // 'source' or 'destination' or null

  // Tab Settings/Edit State
  const [editingTab, setEditingTab] = useState(null);

  const queryClient = useQueryClient();

  const { data: tabs, isLoading } = useQuery('tabs', tabsAPI.getTabs);

  const createTabMutation = useMutation(tabsAPI.createTab, {
    onSuccess: () => {
      queryClient.invalidateQueries('tabs');
      setShowAddTab(false);
      setNewTabData({ name: '', source_path: '', destination_path: '', source_type: 'tv' });
      toast.success('Tab created successfully');
    },
    onError: (error) => {
      toast.error(error.response?.data?.error || 'Failed to create tab');
    },
  });

  const updateTabMutation = useMutation(
    (data) => tabsAPI.updateTab(data.id, data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('tabs');
        setEditingTab(null);
        toast.success('Tab updated successfully');
      },
      onError: (error) => {
        toast.error(error.response?.data?.error || 'Failed to update tab');
      },
    }
  );

  const deleteTabMutation = useMutation(tabsAPI.deleteTab, {
    onSuccess: () => {
      queryClient.invalidateQueries('tabs');
      toast.success('Tab deleted successfully');
    },
    onError: (error) => {
      toast.error(error.response?.data?.error || 'Failed to delete tab');
    },
  });

  const toggleTabExpanded = (tabId) => {
    const newExpanded = new Set(expandedTabs);
    if (newExpanded.has(tabId)) {
      newExpanded.delete(tabId);
    } else {
      newExpanded.add(tabId);
    }
    setExpandedTabs(newExpanded);
  };

  const toggleShowExpanded = (showId) => {
    const newExpanded = new Set(expandedShows);
    if (newExpanded.has(showId)) {
      newExpanded.delete(showId);
    } else {
      newExpanded.add(showId);
    }
    setExpandedShows(newExpanded);
  };

  const handleCreateTab = (e) => {
    e.preventDefault();
    if (!newTabData.name || !newTabData.source_path || !newTabData.destination_path) {
      toast.error('Please fill in all fields');
      return;
    }
    createTabMutation.mutate(newTabData);
  };

  const handleUpdateTab = (e) => {
    e.preventDefault();
    if (!editingTab.name || !editingTab.source_path || !editingTab.destination_path) {
      toast.error('Please fill in all fields');
      return;
    }
    updateTabMutation.mutate(editingTab);
  };

  const handleDeleteTab = (tabId) => {
    if (window.confirm('Are you sure you want to delete this tab?')) {
      deleteTabMutation.mutate(tabId);
    }
  };

  const handleScan = async (path) => {
    if (!path) return;
    
    setScanningPaths(prev => new Set(prev).add(path));
    try {
      const response = await filesystemAPI.scan(path);
      if (response.success) {
        setScanCaches(prev => ({
          ...prev,
          [path]: {
            last_scanned: new Date().toISOString(),
            file_count: response.data.file_count,
            files: response.data.files
          }
        }));
        toast.success(`Scan complete for ${path}`);
      }
    } catch (err) {
      toast.error(`Scan failed: ${err.response?.data?.error || err.message}`);
    } finally {
      setScanningPaths(prev => {
        const next = new Set(prev);
        next.delete(path);
        return next;
      });
    }
  };

  const loadCache = async (path) => {
    if (!path || scanCaches[path]) return;
    
    try {
      const response = await filesystemAPI.getCachedContent(path);
      if (response.success) {
        setScanCaches(prev => ({
          ...prev,
          [path]: response.data
        }));
      }
    } catch (err) {
      // Ignore cache miss errors
    }
  };

  // Load cache when tab is expanded
  useEffect(() => {
    const tabsData = Array.isArray(tabs?.data) ? tabs.data : (Array.isArray(tabs) ? tabs : []);
    expandedTabs.forEach(tabId => {
      const tab = tabsData.find(t => t.id === tabId);
      if (tab?.source_path) {
        loadCache(tab.source_path);
      }
    });
  }, [expandedTabs, tabs]);

  return (
    <div className="w-80 bg-white border-r border-gray-200 h-screen overflow-y-auto">
      <div className="p-4">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Tabs</h2>
          <button
            onClick={() => {
              setShowAddTab(true);
              setEditingTab(null);
            }}
            className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
            title="Add Tab"
          >
            <Plus className="h-4 w-4" />
          </button>
        </div>

        {/* Edit Tab Form */}
        {editingTab && (
          <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg shadow-sm">
            <h3 className="text-sm font-bold text-blue-800 mb-3 flex items-center">
              <Settings className="h-4 w-4 mr-2" />
              Edit Tab: {editingTab.name}
            </h3>
            <form onSubmit={handleUpdateTab}>
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Tab Name
                  </label>
                  <input
                    type="text"
                    value={editingTab.name}
                    onChange={(e) => setEditingTab({ ...editingTab, name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Source Path
                  </label>
                  <div className="flex space-x-2">
                    <input
                      type="text"
                      value={editingTab.source_path}
                      readOnly
                      className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 focus:outline-none"
                    />
                    <button
                      type="button"
                      onClick={() => setActiveBrowserField(activeBrowserField === 'edit-source' ? null : 'edit-source')}
                      className="px-3 py-2 border border-gray-300 rounded-md bg-white hover:bg-gray-100 text-sm"
                    >
                      Browse
                    </button>
                  </div>
                  {activeBrowserField === 'edit-source' && (
                    <div className="mt-2 h-64 border rounded-md overflow-hidden shadow-inner bg-white">
                      <FileBrowser
                        mode="directory"
                        startPath={editingTab.source_path}
                        onSelect={(path) => {
                          setEditingTab({ ...editingTab, source_path: path });
                          setActiveBrowserField(null);
                        }}
                      />
                    </div>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Destination Path
                  </label>
                  <div className="flex space-x-2">
                    <input
                      type="text"
                      value={editingTab.destination_path}
                      readOnly
                      className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 focus:outline-none"
                    />
                    <button
                      type="button"
                      onClick={() => setActiveBrowserField(activeBrowserField === 'edit-destination' ? null : 'edit-destination')}
                      className="px-3 py-2 border border-gray-300 rounded-md bg-white hover:bg-gray-100 text-sm"
                    >
                      Browse
                    </button>
                  </div>
                  {activeBrowserField === 'edit-destination' && (
                    <div className="mt-2 h-64 border rounded-md overflow-hidden shadow-inner bg-white">
                      <FileBrowser
                        mode="directory"
                        startPath={editingTab.destination_path}
                        onSelect={(path) => {
                          setEditingTab({ ...editingTab, destination_path: path });
                          setActiveBrowserField(null);
                        }}
                      />
                    </div>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Source Type
                  </label>
                  <select
                    value={editingTab.source_type}
                    onChange={(e) => setEditingTab({ ...editingTab, source_type: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="tv">TV Shows</option>
                    <option value="movies">Movies</option>
                  </select>
                </div>
                <div className="flex space-x-2 pt-2">
                  <button
                    type="submit"
                    className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    disabled={updateTabMutation.isLoading}
                  >
                    {updateTabMutation.isLoading ? 'Saving...' : 'Save Changes'}
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setEditingTab(null);
                      setActiveBrowserField(null);
                    }}
                    className="bg-gray-300 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-500"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </form>
          </div>
        )}

        {/* Add Tab Form */}
        {showAddTab && (
          <div className="mb-4 p-4 bg-gray-50 rounded-lg">
            <form onSubmit={handleCreateTab}>
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Tab Name
                  </label>
                  <input
                    type="text"
                    value={newTabData.name}
                    onChange={(e) => setNewTabData({ ...newTabData, name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="e.g., TV Syncer"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Source Path
                  </label>
                  <div className="flex space-x-2">
                    <input
                      type="text"
                      value={newTabData.source_path}
                      readOnly
                      className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 focus:outline-none"
                      placeholder="/mnt/tv"
                    />
                    <button
                      type="button"
                      onClick={() => setActiveBrowserField(activeBrowserField === 'source' ? null : 'source')}
                      className="px-3 py-2 border border-gray-300 rounded-md bg-gray-100 hover:bg-gray-200 text-sm"
                    >
                      Browse
                    </button>
                  </div>
                  {activeBrowserField === 'source' && (
                    <div className="mt-2 h-64 border rounded-md overflow-hidden shadow-inner">
                      <FileBrowser
                        mode="directory"
                        onSelect={(path) => {
                          setNewTabData({ ...newTabData, source_path: path });
                          setActiveBrowserField(null);
                        }}
                      />
                    </div>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Destination Path
                  </label>
                  <div className="flex space-x-2">
                    <input
                      type="text"
                      value={newTabData.destination_path}
                      readOnly
                      className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 focus:outline-none"
                      placeholder="/mnt/archive..."
                    />
                    <button
                      type="button"
                      onClick={() => setActiveBrowserField(activeBrowserField === 'destination' ? null : 'destination')}
                      className="px-3 py-2 border border-gray-300 rounded-md bg-gray-100 hover:bg-gray-200 text-sm"
                    >
                      Browse
                    </button>
                  </div>
                  {activeBrowserField === 'destination' && (
                    <div className="mt-2 h-64 border rounded-md overflow-hidden shadow-inner">
                      <FileBrowser
                        mode="directory"
                        onSelect={(path) => {
                          setNewTabData({ ...newTabData, destination_path: path });
                          setActiveBrowserField(null);
                        }}
                      />
                    </div>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Source Type
                  </label>
                  <select
                    value={newTabData.source_type}
                    onChange={(e) => setNewTabData({ ...newTabData, source_type: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="tv">TV Shows</option>
                    <option value="movies">Movies</option>
                  </select>
                </div>
                <div className="flex space-x-2">
                  <button
                    type="submit"
                    className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    disabled={createTabMutation.isLoading}
                  >
                    {createTabMutation.isLoading ? 'Creating...' : 'Create Tab'}
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowAddTab(false)}
                    className="bg-gray-300 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-500"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </form>
          </div>
        )}

        {/* Tabs List */}
        {isLoading ? (
          <div className="text-center py-4">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          </div>
        ) : (
          <div className="space-y-2">
            {/* Standardize data extraction */}
            {(() => {
              const tabsData = Array.isArray(tabs?.data) ? tabs.data : (Array.isArray(tabs) ? tabs : []);
              return tabsData.map((tab) => (
                <div key={tab.id} className="border border-gray-200 rounded-lg">
                  <div className="flex items-center justify-between p-3">
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => toggleTabExpanded(tab.id)}
                        className="text-gray-400 hover:text-gray-600"
                      >
                        {expandedTabs.has(tab.id) ? (
                          <ChevronDown className="h-4 w-4" />
                        ) : (
                          <ChevronRight className="h-4 w-4" />
                        )}
                      </button>
                      {tab.source_type === 'tv' ? (
                        <Tv className="h-4 w-4 text-blue-500" />
                      ) : (
                        <Film className="h-4 w-4 text-purple-500" />
                      )}
                      <span className="text-sm font-medium text-gray-900">
                        {tab.name}
                      </span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <button
                        onClick={() => {
                          setEditingTab(tab);
                          setShowAddTab(false);
                          setActiveBrowserField(null);
                        }}
                        className={`p-1 transition-colors ${editingTab?.id === tab.id ? 'text-blue-600 bg-blue-50 rounded' : 'text-gray-400 hover:text-gray-600'}`}
                        title="Settings"
                      >
                        <Settings className="h-3 w-3" />
                      </button>
                      <button
                        onClick={() => handleDeleteTab(tab.id)}
                        className="p-1 text-gray-400 hover:text-red-600 transition-colors"
                        title="Delete"
                      >
                        <Trash2 className="h-3 w-3" />
                      </button>
                    </div>
                  </div>
                  
                  {expandedTabs.has(tab.id) && (
                    <div className="px-3 pb-3">
                      <div className="text-xs text-gray-500 mb-1">
                        <span className="font-semibold">Source:</span> {tab.source_path}
                      </div>
                      <div className="text-xs text-gray-500 mb-2">
                        <span className="font-semibold">Destination:</span> {tab.destination_path}
                      </div>
                      <div className="text-xs text-gray-500">
                        Type: {tab.source_type === 'tv' ? 'TV Shows' : 'Movies'}
                      </div>
                      
                      <div className="mt-3 pt-3 border-t border-gray-100">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-xs font-semibold text-gray-700">Content Scan</span>
                          <button
                            onClick={() => handleScan(tab.source_path)}
                            disabled={scanningPaths.has(tab.source_path)}
                            className="text-[10px] flex items-center bg-blue-50 text-blue-600 px-2 py-0.5 rounded hover:bg-blue-100 disabled:opacity-50"
                          >
                            <RefreshCw className={`h-2.5 w-2.5 mr-1 ${scanningPaths.has(tab.source_path) ? 'animate-spin' : ''}`} />
                            {scanningPaths.has(tab.source_path) ? 'Scanning...' : 'Scan Now'}
                          </button>
                        </div>
                        
                        {scanCaches[tab.source_path] ? (
                          <div className="space-y-1">
                            <div className="text-[10px] text-gray-400 flex justify-between">
                              <span>Found {scanCaches[tab.source_path].file_count} files</span>
                              <span>Last: {new Date(scanCaches[tab.source_path].last_scanned).toLocaleDateString()}</span>
                            </div>
                            <div className="max-h-32 overflow-y-auto bg-gray-50 rounded p-1.5 space-y-1 scrollbar-thin">
                              {scanCaches[tab.source_path].files?.slice(0, 10).map((file, i) => (
                                <div key={i} className="text-[10px] text-gray-600 truncate flex items-center">
                                  <Film className="h-2 w-2 mr-1 shrink-0 text-gray-400" />
                                  <span title={file.relative_path}>{file.name}</span>
                                </div>
                              ))}
                              {scanCaches[tab.source_path].file_count > 10 && (
                                <div className="text-[10px] text-gray-400 text-center italic">
                                  + {scanCaches[tab.source_path].file_count - 10} more files
                                </div>
                              )}
                            </div>
                          </div>
                        ) : (
                          <div className="text-[10px] text-gray-400 flex items-center justify-center py-2 bg-gray-50 rounded border border-dashed border-gray-200">
                            <Search className="h-3 w-3 mr-1" />
                            No scan data cached
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              ));
            })()}
          </div>
        )}

        {/* Show empty state when no tabs */}
        {(() => {
          const tabsData = Array.isArray(tabs?.data) ? tabs.data : (Array.isArray(tabs) ? tabs : []);
          if (tabsData.length === 0 && !isLoading) {
            return (
              <div className="text-center py-8 text-gray-500">
                <Folder className="h-12 w-12 mx-auto mb-2 text-gray-300" />
                <p>No tabs created yet</p>
                <p className="text-sm">Create your first tab to get started</p>
              </div>
            );
          }
          return null;
        })()}
      </div>
    </div>
  );
};

export default Sidebar;
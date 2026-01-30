import {
    ChevronDown,
    ChevronRight,
    Film,
    Folder,
    Plus,
    Settings,
    Trash2,
    Tv
} from 'lucide-react';
import React, { useState } from 'react';
import toast from 'react-hot-toast';
import { useMutation, useQuery, useQueryClient } from 'react-query';
import { tabsAPI } from '../services/api';

const Sidebar = () => {
  const [expandedTabs, setExpandedTabs] = useState(new Set());
  const [expandedShows, setExpandedShows] = useState(new Set());
  const [selectedTab, setSelectedTab] = useState(null);
  const [showAddTab, setShowAddTab] = useState(false);
  const [newTabData, setNewTabData] = useState({
    name: '',
    destination: '',
    source_type: 'tv'
  });

  const queryClient = useQueryClient();

  const { data: tabs, isLoading } = useQuery('tabs', tabsAPI.getTabs);

  const createTabMutation = useMutation(tabsAPI.createTab, {
    onSuccess: () => {
      queryClient.invalidateQueries('tabs');
      setShowAddTab(false);
      setNewTabData({ name: '', destination: '', source_type: 'tv' });
      toast.success('Tab created successfully');
    },
    onError: (error) => {
      toast.error(error.response?.data?.error || 'Failed to create tab');
    },
  });

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
    if (!newTabData.name || !newTabData.destination) {
      toast.error('Please fill in all fields');
      return;
    }
    createTabMutation.mutate(newTabData);
  };

  const handleDeleteTab = (tabId) => {
    if (window.confirm('Are you sure you want to delete this tab?')) {
      deleteTabMutation.mutate(tabId);
    }
  };

  return (
    <div className="w-80 bg-white border-r border-gray-200 h-screen overflow-y-auto">
      <div className="p-4">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Tabs</h2>
          <button
            onClick={() => setShowAddTab(true)}
            className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
            title="Add Tab"
          >
            <Plus className="h-4 w-4" />
          </button>
        </div>

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
                    Destination Path
                  </label>
                  <input
                    type="text"
                    value={newTabData.destination}
                    onChange={(e) => setNewTabData({ ...newTabData, destination: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="/mnt/archive/Resilio_sync/tv_syncer"
                  />
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
            {/* Add null checks and proper array handling */}
            {Array.isArray(tabs?.data) && tabs.data.map((tab) => (
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
                      onClick={() => setSelectedTab(tab)}
                      className="p-1 text-gray-400 hover:text-gray-600"
                      title="Settings"
                    >
                      <Settings className="h-3 w-3" />
                    </button>
                    <button
                      onClick={() => handleDeleteTab(tab.id)}
                      className="p-1 text-gray-400 hover:text-red-600"
                      title="Delete"
                    >
                      <Trash2 className="h-3 w-3" />
                    </button>
                  </div>
                </div>
                
                {expandedTabs.has(tab.id) && (
                  <div className="px-3 pb-3">
                    <div className="text-xs text-gray-500 mb-2">
                      Destination: {tab.destination}
                    </div>
                    <div className="text-xs text-gray-500">
                      Source: {tab.source_type === 'tv' ? 'TV Shows' : 'Movies'}
                    </div>
                    {/* Content tree would go here */}
                    <div className="mt-2 text-xs text-gray-400">
                      Content scanning not yet implemented
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Show empty state when no tabs */}
        {(!tabs?.data || tabs.data.length === 0) && !isLoading && (
          <div className="text-center py-8 text-gray-500">
            <Folder className="h-12 w-12 mx-auto mb-2 text-gray-300" />
            <p>No tabs created yet</p>
            <p className="text-sm">Create your first tab to get started</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default Sidebar;
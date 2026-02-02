// Status constants
export const STATUS = {
  SYNCED: 'synced',
  TRANSCODING: 'transcoding',
  PENDING: 'pending',
  NOT_SYNCED: 'not_synced',
  WATCHED: 'watched',
};

// Status icons and colors
export const STATUS_CONFIG = {
  [STATUS.SYNCED]: {
    icon: '🟢',
    label: 'Synced',
    className: 'status-synced',
    color: 'text-green-600',
  },
  [STATUS.TRANSCODING]: {
    icon: '🟡',
    label: 'Transcoding',
    className: 'status-transcoding',
    color: 'text-yellow-600',
  },
  [STATUS.PENDING]: {
    icon: '🟠',
    label: 'Pending',
    className: 'status-pending',
    color: 'text-yellow-500',
  },
  [STATUS.NOT_SYNCED]: {
    icon: '🔴',
    label: 'Not Synced',
    className: 'status-not-synced',
    color: 'text-red-600',
  },
  [STATUS.WATCHED]: {
    icon: '👁️',
    label: 'Watched',
    className: 'status-watched',
    color: 'text-gray-600',
  },
};

// Get status configuration
export const getStatusConfig = (status) => {
  return STATUS_CONFIG[status] || STATUS_CONFIG[STATUS.NOT_SYNCED];
};

// Format file size
export const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

// Format duration
export const formatDuration = (seconds) => {
  if (!seconds) return '0s';
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;
  
  if (hours > 0) {
    return `${hours}h ${minutes}m ${secs}s`;
  } else if (minutes > 0) {
    return `${minutes}m ${secs}s`;
  } else {
    return `${secs}s`;
  }
};

// Format progress percentage
export const formatProgress = (progress) => {
  return `${Math.round(progress || 0)}%`;
};

// Get status from file existence
export const getFileStatus = (sourceExists, destExists, isConverting = false) => {
  if (isConverting) {
    return STATUS.TRANSCODING;
  }
  if (!sourceExists) {
    return STATUS.NOT_SYNCED;
  }
  if (destExists) {
    return STATUS.SYNCED;
  }
  return STATUS.NOT_SYNCED;
};
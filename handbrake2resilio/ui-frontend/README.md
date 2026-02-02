# HandBrake2Resilio UI

A modern React frontend for the HandBrake2Resilio video conversion system.

## Features

- **Real-time System Monitoring**: Dashboard with CPU, memory, and disk usage
- **Queue Management**: Monitor and manage conversion jobs with real-time updates
- **Tab Management**: Create and manage tabs for different video sources
- **System Health**: Comprehensive system monitoring and configuration
- **Modern UI**: Built with React 18, Tailwind CSS, and Lucide React icons
- **Real-time Updates**: Uses React Query for efficient data fetching and caching

## Technology Stack

- **React 18** - Modern React with hooks and concurrent features
- **React Router** - Client-side routing
- **React Query** - Data fetching, caching, and synchronization
- **Tailwind CSS** - Utility-first CSS framework
- **Lucide React** - Beautiful, customizable icons
- **React Hot Toast** - Elegant toast notifications
- **Axios** - HTTP client for API calls

## Project Structure

```
src/
├── components/          # React components
│   ├── Dashboard.js     # Main dashboard with system overview
│   ├── Header.js        # Top navigation and system indicators
│   ├── QueueView.js     # Job queue management
│   ├── Sidebar.js       # Tab management sidebar
│   └── SystemView.js    # Detailed system monitoring
├── services/
│   └── api.js          # API service layer
├── utils/
│   └── status.js       # Status utilities and formatters
├── App.js              # Main app component
├── index.js            # React app entry point
└── index.css           # Tailwind CSS and custom styles
```

## Components

### Dashboard

- System resource monitoring (CPU, Memory, Disk)
- Recent jobs overview
- System health indicators
- Real-time status updates

### Queue Management

- View all conversion jobs
- Monitor job progress
- Cancel, retry, and clear jobs
- Error handling and notifications

### Tab Management

- Create tabs for different video sources
- Configure source types (TV/Movies)
- Set destination paths
- Expandable tab details

### System Monitoring

- Detailed system metrics
- Configuration overview
- HandBrake process monitoring
- Recent logs display

## API Integration

The frontend integrates with the HandBrake2Resilio API Gateway:

- **Tabs API**: `/api/tabs` - Tab management
- **Queue API**: `/api/queue` - Job queue operations
- **System API**: `/api/system` - System monitoring and health
- **Content API**: `/api/content` - Content scanning (future)

## Development

### Prerequisites

- Node.js 18+
- npm or yarn

### Getting Started

1. **Install dependencies:**

   ```bash
   npm install
   ```

2. **Start development server:**

   ```bash
   npm start
   ```

3. **Build for production:**

   ```bash
   npm run build
   ```

4. **Run tests:**
   ```bash
   npm test
   ```

### Environment Variables

Set these in `.env` file:

```bash
REACT_APP_API_URL=http://localhost:8080
REACT_APP_WS_URL=ws://localhost:8080
REACT_APP_SOCKET_PATH=/socket.io/
```

## Docker Deployment

### Build Docker image:

```bash
docker build -t handbrake2resilio-ui .
```

### Run container:

```bash
docker run -d -p 3000:80 handbrake2resilio-ui
```

## Features in Detail

### Real-time Updates

- **React Query**: Automatic background refetching
- **WebSocket Support**: Real-time job status updates
- **Optimistic Updates**: Immediate UI feedback

### Responsive Design

- **Mobile-first**: Works on all screen sizes
- **Tailwind CSS**: Consistent, utility-based styling
- **Modern UI**: Clean, professional interface

### Error Handling

- **Toast Notifications**: User-friendly error messages
- **Retry Logic**: Automatic retry for failed requests
- **Graceful Degradation**: Handles API unavailability

### Performance

- **Code Splitting**: Optimized bundle sizes
- **React Query Caching**: Efficient data management
- **Lazy Loading**: Components loaded on demand

## Contributing

1. Follow React best practices
2. Use functional components with hooks
3. Implement proper error boundaries
4. Write unit tests for components
5. Follow the existing code style

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## License

This project is part of the HandBrake2Resilio system.

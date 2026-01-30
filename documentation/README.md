# Scripts Workspace

A comprehensive development workspace containing multiple services and tools for automation, content publishing, video processing, and infrastructure management.

## 🚀 Quick Start

This workspace is configured with a devcontainer that includes all necessary development tools. To get started:

1. **Open in VS Code** with the Dev Containers extension
2. **Reopen in Container** when prompted
3. **Authenticate** with Google Cloud (automatic on first run)

## 📁 Project Structure

### Core Services

#### 🤖 **alt-cliff-mass/** - Content Publishing Automation
- Automated content generation and publishing
- Multi-platform social media posting
- RSS feed monitoring and processing
- **Tech**: Python, Google APIs, OpenAI

#### 🎬 **handbrake2resilio/** - Video Conversion System
- Automated video transcoding with HandBrake
- Web UI for job management
- Real-time progress monitoring
- **Tech**: Python (Flask), React, Docker, HandBrake

#### ⚡ **server-power-management/** - Server Management
- Web-based server power management
- Proxmox integration
- Scheduled power operations
- **Tech**: Python (Flask), HTML/CSS, Proxmox API

#### 🗺️ **strava-heatmap/** - Strava Heatmap Extension
- Browser extension for Strava heatmaps
- Tile processing and visualization
- **Tech**: JavaScript, Chrome Extension API

### Text Services

#### 📱 **text-services/** - SMS/Text Messaging Platform
- **text-gpt/** - GPT-powered text responses
- **text-router/** - Intelligent text routing
- **text-send/** - SMS sending service
- **text-weather/** - Weather information via SMS
- **text-weather-gfs/** - GFS weather data service
- **text-send-php/** - PHP-based SMS service

### Infrastructure

#### 🏗️ **terraform/** - Infrastructure as Code
- Google Cloud Platform resources
- Cloud Functions deployment
- Storage and Pub/Sub configuration
- **Tech**: Terraform, Google Cloud

## 🛠️ Development Environment

### Included Tools
- **Python 3.11** with common packages
- **Node.js 18** with npm
- **Terraform** for infrastructure
- **Google Cloud SDK** for cloud operations
- **Docker-in-Docker** for containerized development

### VS Code Extensions
- Python development tools
- React/TypeScript support
- Terraform support
- Docker support
- Code formatting and linting

## 🔧 Development Workflow

### Python Projects
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest
```

### Node.js Projects
```bash
# Install dependencies
npm install

# Start development server
npm start

# Run tests
npm test
```

### Terraform
```bash
# Initialize
terraform init

# Plan changes
terraform plan

# Apply changes
terraform apply
```

## 🌐 Port Forwarding

The devcontainer automatically forwards these ports:
- **3000**: React development server
- **5000**: Flask development server
- **8000**: Alternative Flask port
- **8080**: API server

## 🔐 Configuration

Environment variables and configuration are stored in:
- `config/environment.txt` - Global configuration
- Individual project `.env` files - Project-specific settings

## 📚 Documentation

Each project contains its own README with specific setup and usage instructions. See the `.devcontainer/README.md` for detailed devcontainer information.

## 🤝 Contributing

1. Use the devcontainer for consistent development environment
2. Follow project-specific coding standards
3. Run tests before committing changes
4. Update documentation as needed

## 🚨 Important Notes

- **Google Cloud Authentication**: Automatically handled by the devcontainer
- **Project ID**: Set to `homelab-462217` by default
- **Dependencies**: Most common packages are pre-installed in the container
- **Port Conflicts**: Check forwarded ports if services don't start

## 📞 Support

For issues with:
- **DevContainer**: Check `.devcontainer/README.md`
- **Individual Projects**: Check project-specific README files
- **Infrastructure**: Check `terraform/README.md` 
# MedAssure AI - Healthcare Test Case Management Platform

![MedAssure AI](https://img.shields.io/badge/MedAssure%20AI-Healthcare%20Testing-blue?style=for-the-badge)
![Version](https://img.shields.io/badge/version-1.0.0-green?style=for-the-badge)
![License](https://img.shields.io/badge/license-MIT-yellow?style=for-the-badge)

## 🏥 Overview

MedAssure AI is a comprehensive, AI-driven healthcare test case management platform designed to streamline the creation, management, and execution of test cases for healthcare applications. The platform ensures compliance with healthcare standards while providing intelligent automation for test case generation and management.

## ✨ Key Features

### 🤖 AI-Powered Test Generation
- **Intelligent Test Case Creation**: Generate comprehensive test cases from requirement documents
- **Multi-format Support**: Process PDF, DOCX, and TXT requirement files
- **Smart Analysis**: AI-driven requirement analysis and clarification
- **Automated Enhancement**: Improve existing test cases with AI suggestions

### 📊 Advanced Analytics & Reporting
- **Real-time Dashboards**: Comprehensive project insights and metrics
- **Test Coverage Analysis**: Track and visualize test coverage percentages
- **Compliance Tracking**: Monitor adherence to healthcare standards (FDA, HIPAA, etc.)
- **Performance Analytics**: Test execution trends and statistics

### 🔄 Migration & Integration
- **Test Case Migration**: Seamlessly migrate test cases between formats
- **Multiple Export Formats**: Support for Excel, PDF, Word, and JSON exports
- **Legacy System Integration**: Import from existing test management tools
- **Data Validation**: Ensure data integrity during migration processes

### 🎯 User Experience
- **Intuitive Interface**: Modern, responsive Material-UI design
- **Real-time Chat Support**: Integrated Dialogflow chatbot assistance
- **Multi-step Workflows**: Guided processes for complex operations
- **Collaborative Features**: Team-based test case management

## 🏗️ Architecture

### Frontend (React)
- **Framework**: React 18.2+ with Material-UI
- **State Management**: React Hooks and Context API
- **Routing**: React Router DOM
- **Charts**: Recharts for data visualization
- **File Processing**: Support for multiple document formats

### Backend (FastAPI)
- **Framework**: FastAPI with Python 3.8+
- **Database**: Google Cloud Firestore
- **Storage**: Google Cloud Storage for file handling
- **AI Integration**: Advanced language models for content analysis
- **APIs**: RESTful API design with OpenAPI documentation

### Infrastructure
- **Frontend Hosting**: Firebase Hosting
- **Backend Deployment**: Google Cloud Run
- **Database**: Google Cloud Firestore (NoSQL)
- **File Storage**: Google Cloud Storage
- **CDN**: Firebase CDN for global content delivery

## 🚀 Quick Start

### Prerequisites

- **Node.js** (v16 or higher)
- **Python** (v3.8 or higher)
- **Google Cloud Account** with billing enabled
- **Firebase CLI** (`npm install -g firebase-tools`)
- **Git** for version control

### 1. Clone the Repository

```bash
git clone https://github.com/sureshsoft09/GPCP_Hack_Test_Generator.git
cd "MedAssure AI"
```

### 2. Frontend Setup

```bash
cd Frontend

# Install dependencies
npm install

# Set up environment variables
cp .env.example .env.local
# Edit .env.local with your configuration

# Start development server
npm start
```

**Frontend Environment Variables** (`.env.local`):
```bash
REACT_APP_API_BASE_URL=http://localhost:8083
# For production: https://your-backend-url.run.app
```

### 3. Backend Setup

```bash
cd Backend

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your Google Cloud configuration

# Start development server
uvicorn main:app --reload --port 8083
```

**Backend Environment Variables** (`.env`):
```bash
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
ENVIRONMENT=development
```

### 4. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8083
- **API Documentation**: http://localhost:8083/docs

## 📁 Project Structure

```
MedAssure AI/
├── Frontend/                 # React.js frontend application
│   ├── public/              # Static assets
│   ├── src/                 # Source code
│   │   ├── components/      # Reusable UI components
│   │   ├── pages/          # Main application pages
│   │   ├── contexts/       # React context providers
│   │   ├── services/       # API and external services
│   │   └── utils/          # Utility functions
│   ├── build/              # Production build output
│   ├── firebase.json       # Firebase hosting configuration
│   └── package.json        # Dependencies and scripts
│
├── Backend/                 # FastAPI backend application
│   ├── app/                # Application source code
│   │   ├── api/           # API route handlers
│   │   ├── core/          # Core configuration
│   │   ├── models/        # Data models
│   │   └── services/      # Business logic services
│   ├── requirements.txt    # Python dependencies
│   └── main.py            # Application entry point
│
├── Agents/                 # AI agents and automation scripts
├── MCP Servers/           # Model Context Protocol servers
├── .vscode/               # VS Code configuration
├── .git/                  # Git repository data
└── README.md              # This file
```

## 🛠️ Development

### Frontend Development

```bash
cd Frontend

# Development server with hot reload
npm start

# Build for production
npm run build

# Run tests
npm test

# Lint code
npm run lint
```

### Backend Development

```bash
cd Backend

# Start with auto-reload
uvicorn main:app --reload --port 8083

# Run tests
pytest

# Format code
black .

# Type checking
mypy .
```

## 🚀 Deployment

### Frontend Deployment (Firebase Hosting)

```bash
cd Frontend

# Build the application
npm run build

# Deploy to Firebase
firebase deploy --only hosting
```

**Live URL**: https://gen-lang-client-0182599221.web.app

### Backend Deployment (Google Cloud Run)

```bash
cd Backend

# Build and deploy
gcloud run deploy medassure-backend \
  --source . \
  --platform managed \
  --region europe-west1 \
  --allow-unauthenticated
```

### Environment-Specific Configuration

#### Production
- **Frontend**: Automated builds on main branch
- **Backend**: Cloud Run with autoscaling
- **Database**: Production Firestore instance
- **Monitoring**: Cloud Monitoring and Logging

#### Development
- **Frontend**: Local development server
- **Backend**: Local FastAPI server
- **Database**: Development Firestore instance

## 📖 API Documentation

The backend provides comprehensive API documentation available at:

- **Development**: http://localhost:8083/docs
- **Production**: https://your-backend-url.run.app/docs

### Key API Endpoints

| Endpoint | Method | Description |
|----------|---------|-------------|
| `/dashboard_summary` | GET | Dashboard analytics data |
| `/upload_requirement_file` | POST | Upload requirement documents |
| `/generate_test_cases` | POST | Generate AI-powered test cases |
| `/enhance_test_cases` | POST | Enhance existing test cases |
| `/migrate_test_cases` | POST | Migrate test cases between formats |
| `/analytics_summary` | GET | Analytics and reporting data |
| `/api/projects` | GET | Project management endpoints |

## 🔒 Security & Compliance

### Healthcare Standards
- **HIPAA Compliance**: Protected health information handling
- **FDA 21 CFR Part 820**: Quality system regulation compliance
- **IEC 62304**: Medical device software lifecycle processes
- **ISO 13485**: Quality management systems for medical devices

### Security Features
- **Authentication**: Secure user authentication and authorization
- **Data Encryption**: End-to-end encryption for sensitive data
- **Audit Trails**: Comprehensive logging and audit capabilities
- **Access Controls**: Role-based access control (RBAC)

## 🤝 Contributing

We welcome contributions to MedAssure AI! Please follow these guidelines:

1. **Fork the Repository**
2. **Create a Feature Branch** (`git checkout -b feature/amazing-feature`)
3. **Commit Changes** (`git commit -m 'Add amazing feature'`)
4. **Push to Branch** (`git push origin feature/amazing-feature`)
5. **Open a Pull Request**

### Development Guidelines
- Follow existing code style and conventions
- Write comprehensive tests for new features
- Update documentation for any API changes
- Ensure all tests pass before submitting PR

## 📊 Monitoring & Analytics

### Application Monitoring
- **Performance Metrics**: Response times and throughput
- **Error Tracking**: Automated error detection and alerting
- **User Analytics**: Usage patterns and feature adoption
- **Health Checks**: Automated service health monitoring

### Business Intelligence
- **Test Coverage Metrics**: Track testing completeness
- **Compliance Reporting**: Automated compliance status reports
- **Resource Utilization**: Infrastructure usage and optimization
- **User Engagement**: Platform usage analytics

## 🆘 Support & Documentation

### Getting Help
- **Documentation**: Comprehensive guides in `/docs` directory
- **Issues**: Report bugs via GitHub Issues
- **Discussions**: Community discussions for feature requests
- **Chat Support**: Integrated Dialogflow chatbot for immediate assistance

### Resources
- **Video Tutorials**: Step-by-step feature walkthroughs
- **Best Practices**: Healthcare testing methodology guides
- **API Reference**: Complete API documentation
- **Troubleshooting**: Common issues and solutions

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Healthcare Community**: For valuable feedback and requirements
- **Open Source Contributors**: For the amazing libraries and tools
- **Google Cloud Platform**: For robust infrastructure and AI services
- **Material-UI Team**: For the excellent React component library

## 📞 Contact

- **Project Lead**: Suresh Kumar
- **Repository**: [GPCP_Hack_Test_Generator](https://github.com/sureshsoft09/GPCP_Hack_Test_Generator)
- **Issues**: [GitHub Issues](https://github.com/sureshsoft09/GPCP_Hack_Test_Generator/issues)

---

**Built with ❤️ for Healthcare Innovation**

*MedAssure AI - Ensuring Quality, Compliance, and Excellence in Healthcare Testing*

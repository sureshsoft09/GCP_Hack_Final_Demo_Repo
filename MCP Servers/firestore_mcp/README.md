# Firestore MCP Server for Test Case Management

A comprehensive MCP (Model Context Protocol) server that provides intelligent agents with tools to manage healthcare software test cases stored in Google Cloud Firestore.

## 🚀 Features

### Core Functionality
- **Project Management**: Create, read, update, delete test projects
- **Hierarchical Structure**: Manage epics → features → use cases → test cases
- **Compliance Tracking**: FDA, IEC 62304, ISO 13485 compliance mapping
- **Jira Integration**: Track synchronization status with Jira
- **Bulk Operations**: Import complete test structures from agent-generated data

### Agent Tools
- `create_project` - Create new test projects
- `get_project` - Retrieve project details
- `list_projects` - List projects with filtering
- `update_project` - Update project information
- `delete_project` - Delete projects
- `import_test_structure` - Bulk import agent-generated test structures
- `add_epic` - Add epics to projects
- `add_feature` - Add features to epics
- `add_use_case` - Add use cases to features
- `add_test_case` - Add test cases to use cases
- `update_epic_jira_status` - Update Jira sync status
- `search_test_cases` - Search within projects
- `get_project_statistics` - Get analytics and statistics

## 📋 Data Structure

The server manages test data in this hierarchical format:

```json
{
  "project_id": "PROJ_abc123",
  "project_name": "MedAssure AI Test Suite",
  "epics": [
    {
      "epic_id": "E001",
      "epic_name": "User Authentication & Access Control",
      "jira_status": "Pushed",
      "features": [
        {
          "feature_id": "F001",
          "feature_name": "Login Validation",
          "use_cases": [
            {
              "use_case_id": "UC001",
              "title": "User logs in with valid credentials",
              "test_cases": [
                {
                  "test_case_id": "TC001",
                  "title": "Verify successful login",
                  "preconditions": ["User exists", "Valid credentials"],
                  "test_steps": ["Navigate to login", "Enter credentials", "Click login"],
                  "expected_result": "User successfully logged in",
                  "test_type": "Functional",
                  "compliance_mapping": ["FDA 820.30(g)", "IEC 62304:5.1"]
                }
              ]
            }
          ]
        }
      ]
    }
  ],
  "coverage_summary": "Generated 15 test cases across 4 epics and 9 features"
}
```

## ⚙️ Installation

### Prerequisites
- Python 3.8+
- Google Cloud Project with Firestore enabled
- Google Cloud credentials

### Setup

1. **Install dependencies:**
   ```bash
   cd "MCP Servers/firestore_mcp"
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   # Copy and edit environment template
   cp ../../../.env.template ../../../.env
   
   # Set required variables:
   GOOGLE_CLOUD_PROJECT=your-project-id
   GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
   FIRESTORE_DATABASE=(default)
   ```

3. **Start the MCP server:**
   ```bash
   python server.py
   ```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_CLOUD_PROJECT` | Google Cloud project ID | `gen-lang-client-0182599221` |
| `GOOGLE_CLOUD_LOCATION` | GCP region | `global` |
| `FIRESTORE_DATABASE` | Firestore database ID | `(default)` |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to service account JSON | - |
| `LOG_LEVEL` | Logging level | `INFO` |

### Firestore Collections

- `test_projects` - Main project documents
- Each project contains nested arrays for epics, features, use cases, and test cases

## 🤖 Agent Integration

### Agent Tool Usage

Agents can interact with the MCP server using these tools:

```python
# Example: Create a new project
result = await mcp_client.call_tool("create_project", {
    "project_name": "Healthcare Portal Tests",
    "description": "Test suite for patient portal",
    "compliance_frameworks": ["FDA 820.30", "IEC 62304"],
    "jira_project_key": "HPT"
})

# Example: Import agent-generated test structure
test_structure = {
    "epics": [
        {
            "epic_id": "E001",
            "epic_name": "User Authentication",
            "features": [...]
        }
    ],
    "coverage_summary": "Generated 25 test cases..."
}

result = await mcp_client.call_tool("import_test_structure", {
    "project_id": "PROJ_abc123",
    "test_structure": json.dumps(test_structure)
})
```

### Integration with Test Generator Agent

The MCP server is designed to work seamlessly with the test generator agent:

1. **Agent generates test structure** using the sequential pipeline
2. **Agent calls `import_test_structure`** to store in Firestore
3. **Agent can query and update** individual components as needed
4. **Agent tracks Jira synchronization** status

## 📊 Analytics and Reporting

### Project Statistics

Get comprehensive analytics:

```python
stats = await mcp_client.call_tool("get_project_statistics", {
    "project_id": "PROJ_abc123"
})

# Returns:
{
    "epic_count": 4,
    "feature_count": 12,
    "test_case_count": 45,
    "jira_sync_stats": {
        "pushed": 3,
        "not_pushed": 1,
        "failed": 0
    },
    "test_type_distribution": {
        "Functional": 30,
        "API": 10,
        "Integration": 5
    },
    "compliance_coverage": ["FDA 820.30(g)", "IEC 62304:5.1"]
}
```

### Search Capabilities

Search across test cases:

```python
results = await mcp_client.call_tool("search_test_cases", {
    "project_id": "PROJ_abc123",
    "search_term": "authentication"
})
```

## 🔒 Security and Compliance

### Data Protection
- All PII and PHI data is excluded from storage
- GDPR and HIPAA compliant data handling
- Audit trails for all modifications

### Access Control
- Service account authentication
- Project-level access control
- Audit logging for all operations

## 🚀 Deployment

### Local Development
```bash
python server.py
```

### Production Deployment
1. Deploy to Google Cloud Run or Compute Engine
2. Set environment variables
3. Configure Firestore security rules
4. Set up monitoring and logging

## 🔍 Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Verify `GOOGLE_APPLICATION_CREDENTIALS` path
   - Check service account permissions

2. **Firestore Permissions**
   - Ensure service account has Firestore read/write access
   - Check Firestore security rules

3. **Import Failures**
   - Validate JSON structure matches expected format
   - Check for required fields in test structure

### Logging

Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
python server.py
```

## 📝 API Reference

### Tool Signatures

#### Project Management
- `create_project(project_name, description?, compliance_frameworks?, jira_project_key?, created_by?)`
- `get_project(project_id)`
- `list_projects(status?, compliance_framework?, text_search?, limit?)`
- `update_project(project_id, project_name?, description?, status?, compliance_frameworks?, updated_by?)`
- `delete_project(project_id)`

#### Structure Management
- `import_test_structure(project_id, test_structure)`
- `add_epic(project_id, epic_name, description?, epic_id?)`
- `add_feature(project_id, epic_id, feature_name, description?, feature_id?)`
- `add_use_case(project_id, epic_id, feature_id, title, description, test_scenarios_outline?, compliance_mapping?, use_case_id?)`
- `add_test_case(project_id, epic_id, feature_id, use_case_id, title, preconditions, test_steps, expected_result, test_type?, compliance_mapping?, test_case_id?)`

#### Jira Integration
- `update_epic_jira_status(project_id, epic_id, jira_status, jira_key?)`

#### Analytics
- `search_test_cases(project_id, search_term)`
- `get_project_statistics(project_id)`

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Submit pull request

## 📄 License

Copyright 2025 MedAssure AI Team. All rights reserved.
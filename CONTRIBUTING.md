# Contributing to GoPredict

Thanks for your interest in contributing! This guide will help you get started with development and frontend integration.

## Ground Rules

- **Be kind and respectful.** Follow our Code of Conduct.
- **Open an issue first** for major changes to discuss the approach.
- **Add tests** for any bug fix or new feature.
- **Keep PRs focused** and small when possible.

## Project Setup

### Backend API Development

```bash
# Install Python dependencies
pip install -r requirements.txt

# Start the API server
python start_api.py

# Test the API
python test_api.py

# View API documentation
# Visit http://localhost:8000/docs
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Run tests
npm run test:run

# Run tests with coverage
npm run test:coverage
```

### Python ML Development (Optional)

```bash
pip install -r requirements.txt

# Run the complete ML pipeline
python main.py

# Run with specific models
python main.py --models XGB,RF

# Add tests under tests/ if contributing Python code
```

## Frontend Integration Guide

### API Client Usage

The frontend uses the API client in `frontend/src/lib/api.ts` for backend communication:

#### Basic Trip Prediction

```typescript
import { predictTravelTime } from "@/lib/api";

const prediction = await predictTravelTime({
  from: {
    id: "start",
    name: "Start Location",
    lat: 40.767937,
    lon: -73.982155,
  },
  to: {
    id: "end",
    name: "End Location",
    lat: 40.748817,
    lon: -73.985428,
  },
  startTime: "2016-01-01T17:00:00",
  city: "new_york",
});

console.log(`Predicted duration: ${prediction.minutes} minutes`);
```

#### Error Handling

```typescript
try {
  const prediction = await predictTravelTime(tripData);
  setPrediction(prediction);
} catch (error) {
  console.error("Prediction failed:", error);
  setError(error.message);
}
```

#### Model Status Check

```typescript
import { getModelStatus } from "@/lib/api";

const status = await getModelStatus();
console.log(`API Status: ${status.status}`);
```

### API Endpoints Reference

#### Prediction Endpoint

- **URL**: `POST /predict`
- **Body**: Trip data with from/to locations, startTime, city
- **Response**: Duration in minutes, confidence, distance

#### Health Check

- **URL**: `GET /health`
- **Response**: API health status

#### Status Check

- **URL**: `GET /status`
- **Response**: Detailed API status and model information

### Environment Configuration

Create `frontend/.env.local` for local development:

```env
# API Configuration
VITE_API_URL=http://localhost:8000

# Development Settings
VITE_DEV_MODE=true
```

## Branching & Commits

- Create a feature branch from `main`:
  - `feature/<short-description>`
  - `fix/<short-description>`
- Use conventional-style commit messages when possible (e.g., `feat: add vitest setup`).

## Testing

### Frontend Testing

- **Framework**: Vitest + React Testing Library
- **Location**: `frontend/src/test/*`
- **Commands**:
  - `npm run test:run` - Run tests once
  - `npm run test:coverage` - Run with coverage

### Backend Testing

- **Framework**: Python requests + pytest
- **Location**: `test_api.py`
- **Command**: `python test_api.py`

### API Testing Examples

```bash
# Test all endpoints
python test_api.py

# Test specific endpoint
python -c "
import requests
response = requests.get('http://localhost:8000/health')
print('Status:', response.status_code)
print('Response:', response.json())
"
```

## Linting & Formatting

### Frontend

- Use Prettier defaults (Vite + React)
- Keep code idiomatic and typed
- Follow React best practices

### Backend

- Follow PEP 8 Python style guide
- Use type hints where possible
- Document functions with docstrings

## Pull Requests

- Fill in the PR template
- Link related issues
- Describe the change, screenshots if UI
- Checklist must pass: tests, CI, and review comments

### PR Checklist

- [ ] Tests pass (`npm run test:run` and `python test_api.py`)
- [ ] Code follows style guidelines
- [ ] Documentation updated if needed
- [ ] No console errors in frontend
- [ ] API endpoints tested manually

## Development Workflow

### 1. Setting Up Development Environment

```bash
# Clone and setup
git clone <your-repo-url>
cd GoPredict

# Backend setup
pip install -r requirements.txt
python start_api.py  # Keep running in terminal 1

# Frontend setup (new terminal)
cd frontend
npm install
npm run dev  # Keep running in terminal 2
```

### 2. Making Changes

1. Create feature branch: `git checkout -b feature/your-feature`
2. Make changes to frontend or backend
3. Test your changes:
   - Frontend: Check browser console, run tests
   - Backend: Test API endpoints
4. Commit with descriptive message
5. Push and create PR

### 3. Testing Integration

```bash
# Test frontend-backend connection
python -c "
import requests
data = {
    'from': {'lat': 40.767937, 'lon': -73.982155},
    'to': {'lat': 40.748817, 'lon': -73.985428},
    'startTime': '2016-01-01T17:00:00',
    'city': 'new_york'
}
response = requests.post('http://localhost:8000/predict', json=data)
print('Status:', response.status_code)
print('Response:', response.json())
"
```

## Releases

- Maintainers use GitHub Releases and tags
- Version numbers follow semantic versioning
- Changelog updated for each release

## Troubleshooting

### Common Issues

#### Frontend Can't Connect to Backend

- Ensure API server is running: `python start_api.py`
- Check API URL in frontend: `VITE_API_URL=http://localhost:8000`
- Verify CORS settings in `api/main.py`

#### API Tests Failing

- Check if server is running: `curl http://localhost:8000/health`
- Verify dependencies: `pip install -r requirements.txt`
- Check Python path and imports

#### Frontend Build Issues

- Clear node_modules: `rm -rf node_modules && npm install`
- Check Node.js version compatibility
- Verify all dependencies installed

## Questions?

- Open a Discussion or an Issue on GitHub
- Check existing issues for similar problems
- Review API documentation at `http://localhost:8000/docs`

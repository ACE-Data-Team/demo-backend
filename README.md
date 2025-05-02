# Demo Project

This repository contains the **Demo Backend** and **Demo Frontend** applications for managing and visualizing data trends.

## Project Structure

- **Backend**: Located in the `demo-backend` folder, built with FastAPI for handling API requests and generating data visualizations.
- **Frontend**: Located in the `demo-frontend` folder, built with modern web technologies for rendering charts and user interfaces.

## Features

- **Backend**:
  - API endpoints for generating charts (e.g., student trends, staff trends).
  - Data aggregation and visualization using Plotly.
  - Fast and scalable API built with FastAPI.

- **Frontend**:
  - Dynamic chart rendering using data from the backend.
  - Interactive user interface for exploring trends.

## Requirements

- Python 3.9+
- Node.js (for frontend development)
- Plotly for data visualization
- FastAPI for backend API

## Setup Instructions

### Backend
1. Navigate to the `demo-backend` folder:
```bash
cd demo-backend
```
   
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the backend server
```bash
uvicorn app.main:app --reload
```
4. Access the API documentation at: `http://127.0.0.1:8000/docs`


## Usage
1. Start the backend and frontend servers.
2. Access the frontend in your browser to interact with the application.
3. Use the API endpoints (e.g., /charts/student-trend) to fetch chart data.

## Contributing
Feel free to submit issues or pull requests to improve the project.

## License
This project is licensed under the MIT License.

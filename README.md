# Demo Backend

This repository contains the **Demo Backend** application for managing and visualizing data trends. It is built with FastAPI and uses Plotly for data visualization.

## Features

- API endpoints for generating charts (e.g., student trends, staff trends).
- Data aggregation and visualization using Plotly.
- Fast and scalable API built with FastAPI.

## Requirements

- Python 3.9+
- Plotly for data visualization
- FastAPI for backend API

## Setup Instructions

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
- Use the API endpoints to fetch chart data and visualizations.
- Example endpoints:
  - `/charts/student-trend`
  - `/charts/staff-trend`

## Contributing
Feel free to submit issues or pull requests to improve the project.

## License
This project is licensed under the MIT License.

# GitHub PR Fetcher

**GitHub PR Fetcher** is an API that allows you to fetch and analyze GitHub Pull Requests (PRs) asynchronously. This project utilizes FastAPI, Celery, and Redis to retrieve PR details and perform code analysis using AI-based review tools. The analysis includes checks for code quality, security vulnerabilities, adherence to best practices, and other potential issues.

## Table of Contents

- [Features](#features)
- [Project Setup Instructions](#project-setup-instructions)
  - [Prerequisites](#prerequisites)
  - [Installation Steps](#installation-steps)
- [API Documentation](#api-documentation)
  - [Base URL](#base-url)
  - [API Endpoints](#api-endpoints)
    - [Analyze PR](#analyze-pr)
    - [Get Task Status](#get-task-status)
    - [Get Task Result](#get-task-result)
- [Design Decisions](#design-decisions)
- [Future Improvements](#future-improvements)
- [Contributing](#contributing)
- [License](#license)

## Features

- Asynchronous fetching and analysis of GitHub Pull Requests.
- AI-powered code review for quality, security, and best practices.
- Background task processing using Celery and Redis.
- Comprehensive API documentation with easy-to-use endpoints.

## Project Setup Instructions

### Prerequisites

To set up and run this project, ensure you have the following installed:

- **Python 3.8+**: Make sure Python is installed on your system. You can download it from the [official Python website](https://www.python.org/downloads/).
- **Redis**: The Redis service must be running locally or on a remote server.
  - Install Redis: Follow the instructions in the [Redis Installation Guide](https://redis.io/docs/getting-started/installation/).
  - Alternatively, you can use Docker to run Redis:
    ```
    docker run --name redis -p 6379:6379 -d redis
    ```
- **OpenAI API Key**: Required for using the AI-powered code analysis feature. Obtain your API key from the [OpenAI website](https://openai.com/).

### Installation Steps

1. **Clone the repository**:
   git clone https://github.com/your-username/github-pr-fetcher.git
   cd github-pr-fetcher
2. **Install required Python packages**:
   pip install -r requirements.txt
3. **Set up environment variables**:

- Create a `.env` file in the root directory.
- Add your OpenAI API Key to the `.env` file:
  ```
  OPENAI_API_KEY=your-openai-api-key
  ```

4. **Run the FastAPI server**:
   uvicorn main:app --reload
5. **Start the Celery worker to process background tasks**:

```
celery -A app.celery.celery_app.celery worker --loglevel=info
```

### Running Redis

Ensure that Redis is running before starting the FastAPI app and Celery worker. You can run it locally or connect to a remote Redis instance.

## API Documentation

### Base URL

The base URL for the API is:

```
http://localhost:8000
```

### API Endpoints

#### Analyze PR

**POST /analyze-pr**

This endpoint triggers the analysis of a GitHub PR asynchronously.

**Request Body**
The request body should be a JSON object structured as follows:

```
{
    "github_repo_url": "https://github.com/owner/repo",
    "pr_number": 1,
    "access_token": "your-github-token"
}
```

- `github_repo_url` (string): URL of the GitHub repository (e.g., `https://github.com/owner/repo`).
- `pr_number` (integer): The pull request number to fetch.
- `access_token` (string, optional): GitHub personal access token (if required).

**Response**
On success, you will receive a JSON object containing the task ID for tracking:

```
{
    "task_id": "some-task-id"
}
```

#### Get Task Status

**GET /status/{task_id}**

This endpoint returns the current status of the background task based on the provided task ID.

**URL Parameters**

- `task_id` (string): The ID of the background task.

**Response**
The response includes the current status of the task along with additional information:

```
{
    "task_id": "some-task-id",
    "status": "success",
    "result": { ... } // The result of the task when completed
}
```

Possible statuses include:

- **PENDING**: Task is waiting to be processed.
- **PROCESSING**: Task is currently being processed.
- **SUCCESS**: Task has been completed successfully.
- **FAILURE**: Task has failed with an error message.

#### Get Task Result

**GET /results/{task_id}**

This endpoint retrieves the result of the task once it is completed.

**URL Parameters**

- `task_id` (string): The ID of the background task.

**Response**
If the task is completed, you will receive a JSON object containing the result of the PR analysis:

```
{
    "task_id": "some-task-id",
    "status": "completed",
    "result": {
        "files": [
            {
                "name": "file1.py",
                "issues": [
                    {
                        "type": "style",
                        "line": 42,
                        "description": "Line exceeds recommended length of 100 characters",
                        "suggestion": "Consider breaking this line into multiple lines"
                    },
                    {
                        "type": "maintenance",
                        "line": 88,
                        "description": "TODO comment found",
                        "suggestion": "Implement the TODO or create a ticket for tracking"
                    }
                ]
            }
        ],
        "summary": {
            "total_files": 1,
            "total_issues": 2,
            "critical_issues": 1
        }
    }
}

```
If the task is not ready, it will return a `404` status code with this message:
```
{
    "detail": "Task result not ready yet"
}
```

## Design Decisions
- **FastAPI**: Selected for its speed, modern features, and automatic generation of OpenAPI documentation.
- **Celery with Redis**: Chosen for background task processing to handle long-running tasks without blocking the main API thread.
- **Langchain & OpenAI**: Utilized for AI-based code review and analysis, enabling flexible and customizable feedback on pull requests.
- **Asynchronous Processing**: Implemented asynchronous fetching and analysis to enhance API responsiveness and allow users to check status/results later.
- **Caching Mechanism**: Introduced caching for frequently accessed PRs to minimize redundant fetches and analyses.
- **Logging Framework**: Implemented logging to track application events and errors effectively, aiding in troubleshooting and performance monitoring.
- **Error Handling**: Employed proper HTTP exceptions to manage errors like invalid PR URLs or GitHub issues, providing detailed error messages.

## Future Improvements
- **Authentication & Authorization**: Implement OAuth for GitHub authentication to streamline user access without manual token entry.
- **Enhanced AI Review Capabilities**: Expand AI review features to identify additional code quality issues, bugs, and performance improvements.
- **Scalability Enhancements**: Deploy API and Celery workers on cloud platforms with auto-scaling capabilities for better traffic management.
- **Webhooks Integration**: Implement GitHub webhooks to automatically trigger PR analysis upon new PR creation or updates, reducing manual requests.
- **Front-End Interface Development**: Create a user-friendly dashboard to display PR details, analysis results, and task statuses for easier interaction.
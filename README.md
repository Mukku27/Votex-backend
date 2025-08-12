# Votex: Professor Feedback Analysis API

[![Python Version](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Framework](https://img.shields.io/badge/Framework-FastAPI-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Votex is a powerful backend API designed to analyze student feedback for professors using the high-speed Groq LLM API. It processes raw feedback to generate insightful, actionable reports by performing sentiment analysis, PII redaction, and summarization, helping educators quickly understand and act upon student input.

## ✨ Key Features

-   **Intelligent Feedback Analysis**: Leverages Large Language Models (LLMs) to understand the nuances of student feedback.
-   **PII & Inappropriate Content Filtering**: Automatically detects and redacts Personally Identifiable Information (PII) and filters out inappropriate content to ensure privacy and focus.
-   **Sentiment Analysis**: Classifies feedback into positive, neutral, and negative categories, providing a quantitative overview of student sentiment.
-   **Automated Summarization**: Generates concise summaries of overarching themes and key points from large volumes of feedback.
-   **Actionable Insights**: Produces a clear, bulleted list of suggested actions for professors to improve their teaching methods.
-   **Robust & Scalable**: Built with FastAPI, ensuring high performance and asynchronous capabilities.
-   **Resilient API Calls**: Implements an automatic retry mechanism with exponential backoff for handling API rate limits.

---

## 🚀 Technology Stack

-   **Backend**: FastAPI
-   **LLM**: Groq API (with `llama-3.3-70b-versatile`)
-   **Data Validation**: Pydantic
-   **Server**: Uvicorn
-   **Dependencies**: Python-dotenv

---

## 🔧 Installation & Setup

Follow these steps to get the project running locally.

### 1. Prerequisites

-   Python 3.8+
-   A GroqCloud API Key

### 2. Clone the Repository

```bash
git clone https://github.com/mukku27/votex-backend.git
cd votex-backend
```

### 3. Create a Virtual Environment

It's recommended to use a virtual environment to manage dependencies.

```bash
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## ⚙️ Configuration

The application requires environment variables for configuration. Create a `.env` file in the project root:

```bash
touch .env
```

Add the following variables to the `.env` file. Your Groq API key is required.

```env
# Required
GROQ_API_KEY="your-groq-api-key"

# Optional (defaults are provided)
MODEL_NAME="llama-3.3-70b-versatile"
MAX_RETRIES="5"
```

---

## ▶️ Running the Application

You can run the API server using Uvicorn. The application will be available at `http://127.0.0.1:8000`.

```bash
uvicorn main:app --reload
```

---

## 📁 Project Structure

The project follows a modular structure to separate concerns:

```
└── mukku27-votex-backend/
    ├── main.py             # FastAPI app entry point
    ├── requirements.txt    # Project dependencies
    ├── setup.py            # Package setup script
    ├── api/                # FastAPI routers and endpoints
    │   └── routes/
    ├── core/               # Core logic (config, LLM client)
    ├── models/             # Pydantic schemas
    ├── services/           # Business logic for feedback processing
    └── utils/              # Utility functions (e.g., redaction)
```

---

## 📖 API Endpoints

The API provides the following endpoints:

### Health Check

-   **Endpoint**: `GET /health`
-   **Description**: Checks the health of the API and returns the currently configured model.
-   **Response**:
    ```json
    {
      "status": "healthy",
      "model": "llama-3.3-70b-versatile"
    }
    ```

### Generate Feedback Report

-   **Endpoint**: `POST /report`
-   **Description**: The main endpoint that accepts a list of feedback strings and returns a comprehensive analysis.
-   **Request Body**:
    ```json
    {
      "feedback": [
        "The professor explains concepts clearly, but the lectures can be a bit fast.",
        "I loved the hands-on labs, they were very helpful.",
        "The final exam was too difficult and didn't reflect the course material."
      ]
    }
    ```
-   **Success Response (200 OK)**:
    ```json
    {
      "summary": "The feedback indicates that while the professor's explanations and hands-on labs are appreciated, the lecture pace can be fast and the final exam was perceived as overly difficult.",
      "sentiment": {
        "positive": 1,
        "neutral": 1,
        "negative": 1
      },
      "actions": [
        "Consider adjusting the lecture pace to ensure all students can follow along.",
        "Review the final exam's difficulty and alignment with course content.",
        "Continue incorporating hands-on labs as they are highly valued by students."
      ],
      "raw_feedback_count": 3,
      "clean_feedback_count": 3
    }
    ```
-   **Error Response (422 Unprocessable Entity)**:
    Triggered if all feedback items are filtered out (e.g., due to being empty or containing PII).
    ```json
    {
        "detail": "No valid feedback after filtering."
    }
    ```

---

## 📜 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

---

## ✍️ Author

This project is maintained by **Mukku27**.

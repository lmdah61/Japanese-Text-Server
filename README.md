# Japanese Text Generator

A Python backend service that uses Google's Gemini API to generate short random Japanese texts for students based on JLPT level and theme specified by the user.

## Features

- Generate Japanese text appropriate for specific JLPT levels (N5-N1)
- Customize text generation based on themes
- Receive structured responses with:
  - Japanese text
  - English translation
  - Vocabulary list with readings and meanings
  - Grammar points with explanations
- Rate limiting to prevent API abuse

## Prerequisites

- Python 3.8 or higher
- Google Gemini API key

## Installation

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file based on the `.env.example` template and add your Google Gemini API key:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```

## Usage

### Starting the server

```
python app.py
```

The server will start on port 5000 by default. You can change this by setting the `PORT` environment variable in your `.env` file.

### API Endpoints

#### Health Check

```
GET /health
```

Returns the health status of the service.

#### Generate Japanese Text

```
POST /generate
```

Request body:

```json
{
  "jlpt_level": "N5",  // Must be one of: N5, N4, N3, N2, N1
  "theme": "Travel"    // Any theme you want the text to be about
}
```

Response:

```json
{
  "japanese_text": "日本語のテキスト...",
  "english_translation": "English translation...",
  "vocabulary": [
    {
      "word": "旅行",
      "reading": "りょこう",
      "meaning": "travel"
    },
    // more vocabulary items
  ],
  "grammar_points": [
    {
      "pattern": "〜ます",
      "explanation": "Polite form of verbs"
    },
    // more grammar points
  ]
}
```

## Rate Limiting

The API is rate-limited to prevent abuse:
- 50 requests per hour
- 5 requests per minute

## Error Handling

The API returns appropriate HTTP status codes and error messages for different error scenarios:

- 400: Bad Request (invalid input parameters)
- 429: Too Many Requests (rate limit exceeded)
- 500: Internal Server Error

<sub>**Leave a Tip:** opulentmenu06@walletofsatoshi.com</sub>

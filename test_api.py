import os
import json
import unittest
import requests
import time
import subprocess
import signal
import sys
from unittest import mock
from dotenv import load_dotenv

# Import test configuration
from test_config import BASE_URL, TEST_JLPT_LEVELS

# Load environment variables from .env file
load_dotenv()

# Set environment variable for testing
os.environ['FLASK_TESTING'] = 'True'

# Base URL for the API (assuming it's running locally)
BASE_URL = "http://localhost:5000"

class JapaneseTextAPITest(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        # Start the Flask server with testing mode enabled
        print("Starting Flask server in testing mode...")
        cls.flask_process = None
        try:
            # Try to connect to an existing server first
            response = requests.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                print("Server is already running")
                return
        except requests.exceptions.ConnectionError:
            # Start a new server if one isn't running
            print("Starting new server instance")
            # Use subprocess to start the server in the background
            cls.flask_process = subprocess.Popen(
                [sys.executable, "-c", 
                 "import os; os.environ['FLASK_TESTING'] = 'True'; " +
                 "from app import app; app.run(host='0.0.0.0', port=5000)"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            # Wait for the server to start
            max_retries = 5
            retry_delay = 1
            for i in range(max_retries):
                try:
                    response = requests.get(f"{BASE_URL}/health")
                    if response.status_code == 200:
                        print("Server started successfully")
                        break
                except requests.exceptions.ConnectionError:
                    if i < max_retries - 1:
                        print(f"Waiting for server to start (attempt {i+1}/{max_retries})...")
                        time.sleep(retry_delay)
                    else:
                        print("Failed to start server")
    
    @classmethod
    def tearDownClass(cls):
        # Stop the Flask server if we started it
        if cls.flask_process:
            print("Stopping Flask server...")
            if sys.platform == 'win32':
                cls.flask_process.terminate()
            else:
                os.kill(cls.flask_process.pid, signal.SIGTERM)
            cls.flask_process.wait()
            print("Server stopped")
    
    def setUp(self):
        # Check if the server is running before each test
        try:
            response = requests.get(f"{BASE_URL}/health")
            if response.status_code != 200:
                self.skipTest("API server is not running or not healthy")
        except requests.exceptions.ConnectionError:
            self.skipTest("API server is not running")
            
    def make_request(self, method, endpoint, **kwargs):
        """Helper method to make requests with retry logic for rate limiting and connection errors"""
        max_retries = 5
        retry_delay = 1  # seconds
        
        for attempt in range(max_retries):
            try:
                response = method(f"{BASE_URL}/{endpoint}", **kwargs)
                
                # If not rate limited or last attempt, return the response
                if response.status_code != 429 or attempt == max_retries - 1:
                    return response
                
                # If rate limited, wait and retry
                print(f"Rate limited. Waiting {retry_delay} seconds before retry...")
            except requests.exceptions.ConnectionError as e:
                if attempt == max_retries - 1:
                    raise
                print(f"Connection error: {e}. Retrying in {retry_delay} seconds...")
            
            time.sleep(retry_delay)
            retry_delay *= 1.5  # Exponential backoff
    
    def test_health_endpoint(self):
        """Test the health check endpoint"""
        response = self.make_request(requests.get, "health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
    
    def test_generate_valid_request(self):
        """Test the generate endpoint with valid request data"""
        # Test with valid JLPT level and theme
        payload = {
            "jlpt_level": "N5",
            "theme": "Travel"
        }
        response = self.make_request(requests.post, "generate", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify response structure
        self.assertIn("japanese_text", data)
        self.assertIn("english_translation", data)
        self.assertIn("vocabulary", data)
        self.assertIn("grammar_points", data)
        
        # Verify vocabulary structure
        for vocab in data["vocabulary"]:
            self.assertIn("word", vocab)
            self.assertIn("reading", vocab)
            self.assertIn("meaning", vocab)
        
        # Verify grammar points structure
        for grammar in data["grammar_points"]:
            self.assertIn("pattern", grammar)
            self.assertIn("explanation", grammar)
    
    def test_generate_all_jlpt_levels(self):
        """Test the generate endpoint with all JLPT levels"""
        for level in TEST_JLPT_LEVELS:
            with self.subTest(level=level):
                payload = {
                    "jlpt_level": level,
                    "theme": "Food"
                }
                response = self.make_request(requests.post, "generate", json=payload)
                self.assertEqual(response.status_code, 200)
                data = response.json()
                self.assertIn("japanese_text", data)
                # Add a longer delay between requests to avoid rate limiting
                time.sleep(2)
    
    def test_generate_invalid_jlpt_level(self):
        """Test the generate endpoint with invalid JLPT level"""
        payload = {
            "jlpt_level": "N6",  # Invalid level
            "theme": "Travel"
        }
        response = self.make_request(requests.post, "generate", json=payload)
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("error", data)
        self.assertIn("Invalid JLPT level", data["error"])
    
    def test_generate_missing_theme(self):
        """Test the generate endpoint with missing theme"""
        payload = {
            "jlpt_level": "N5"
            # Missing theme
        }
        response = self.make_request(requests.post, "generate", json=payload)
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("error", data)
        self.assertIn("Theme is required", data["error"])
    
    def test_generate_empty_theme(self):
        """Test the generate endpoint with empty theme"""
        payload = {
            "jlpt_level": "N5",
            "theme": ""  # Empty theme
        }
        response = self.make_request(requests.post, "generate", json=payload)
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("error", data)
        self.assertIn("Theme is required", data["error"])
    
    def test_generate_invalid_json(self):
        """Test the generate endpoint with invalid JSON"""
        # Send invalid JSON
        response = self.make_request(
            requests.post,
            "generate", 
            data="This is not JSON",
            headers={"Content-Type": "application/json"}
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("error", data)
        self.assertIn("Invalid JSON format", data["error"])

if __name__ == "__main__":
    unittest.main()
# Test configuration
import os

# Set testing mode for Flask app
os.environ['FLASK_TESTING'] = 'True'

# Mock API key for testing
os.environ['MOCK_API_KEY'] = 'test_api_key'

# Test server URL
BASE_URL = "http://localhost:5000"

# Test data
TEST_JLPT_LEVELS = ["N5", "N4", "N3", "N2", "N1"]
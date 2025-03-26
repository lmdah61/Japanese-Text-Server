import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import google.generativeai as genai
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Set testing mode for tests
app.config['TESTING'] = os.environ.get('FLASK_TESTING', 'False').lower() == 'true'

# Configure rate limiting
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["50 per hour", "5 per minute"],
    storage_uri="memory://",
)

# Disable rate limiting for tests
@app.before_request
def check_testing():
    if app.config.get('TESTING'):
        limiter.enabled = False

# Configure Google Gemini API
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    logger.error("GEMINI_API_KEY not found in environment variables")
    if not app.config.get('TESTING'):
        raise ValueError("GEMINI_API_KEY environment variable is required")
    else:
        api_key = "mock_api_key"
        logger.info("Using mock API key for testing")

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-2.0-flash')

# JLPT levels and their descriptions
JLPT_LEVELS = {
    "N5": "Basic Japanese knowledge. ~800 basic vocabulary words, basic grammar patterns.",
    "N4": "Basic Japanese ability. ~1,500 vocabulary words, basic grammar patterns.",
    "N3": "Intermediate Japanese ability. ~3,000 vocabulary words, intermediate grammar.",
    "N2": "Pre-advanced Japanese ability. ~6,000 vocabulary words, advanced grammar.",
    "N1": "Advanced Japanese ability. ~10,000 vocabulary words, complex grammar patterns."
}

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy"})

@app.route('/generate', methods=['POST'])
@limiter.limit("5 per minute")
def generate_text():
    """Generate Japanese text based on JLPT level and theme"""
    try:
        # Parse and validate request data
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is required"}), 400
    except Exception as e:
        # Handle invalid JSON format
        return jsonify({"error": f"Invalid JSON format: {str(e)}"}), 400
        
    try:
        
        jlpt_level = data.get('jlpt_level', '').upper()
        theme = data.get('theme', '')
        
        # Validate inputs
        if not jlpt_level or jlpt_level not in JLPT_LEVELS:
            return jsonify({"error": f"Invalid JLPT level. Must be one of: {', '.join(JLPT_LEVELS.keys())}"}), 400
        
        if not theme or not isinstance(theme, str):
            return jsonify({"error": "Theme is required and must be a string"}), 400
        
        # Log request information
        logger.info(f"Generating text for JLPT level: {jlpt_level}, Theme: {theme}")
        
        # Use mock response in testing mode
        if app.config.get('TESTING'):
            try:
                from mock_responses import MOCK_RESPONSE
                logger.info("Using mock response for testing")
                return jsonify(MOCK_RESPONSE)
            except ImportError:
                logger.warning("Mock responses not found, falling back to API call")
        
        # Create prompt for Gemini
        prompt = create_gemini_prompt(jlpt_level, theme)
        
        # Generate text using Gemini API
        response = model.generate_content(prompt)
        
        # Process the response
        try:
            # Extract, clean and parse JSON from the response
            json_str = extract_json_from_response(response.text)
            result = json.loads(json_str)
            
            # Validate required fields
            if 'japanese_text' not in result:
                raise ValueError("Response missing 'japanese_text' field")
                
            return jsonify(result)
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Error processing response: {e}")
            return jsonify({
                "error": f"Failed to process response: {str(e)}",
                "japanese_text": response.text  # Fallback to raw text
            }), 500
            
    except Exception as e:
        logger.error(f"Error generating text: {e}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

def create_gemini_prompt(jlpt_level, theme):
    """Create a prompt for the Gemini model based on JLPT level and theme"""
    return f"""
    Generate a short Japanese text (100-150 words) about the theme: {theme}.
    
    The text should be appropriate for JLPT level {jlpt_level} students.
    {JLPT_LEVELS[jlpt_level]}
    
    Please format your response as a JSON object with the following structure:
    {{"japanese_text": "[Japanese text here]", 
      "english_translation": "[English translation here]",
      "vocabulary": [{{"word": "[Japanese word]", "reading": "[reading in hiragana]", "meaning": "[English meaning]"}}],
      "grammar_points": [{{"pattern": "[grammar pattern]", "explanation": "[explanation in English]"}}]
    }}
    
    Ensure the text uses vocabulary and grammar appropriate for JLPT {jlpt_level} level.
    """

def extract_json_from_response(response_text):
    """Extract and clean JSON from model response text"""
    # Check if the response contains a code block with JSON
    if "```json" in response_text and "```" in response_text.split("```json", 1)[1]:
        json_str = response_text.split("```json", 1)[1].split("```", 1)[0].strip()
    else:
        json_str = response_text
        
    # Clean up any potential markdown or text formatting
    return json_str.replace('```', '').strip()

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
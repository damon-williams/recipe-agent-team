# test_web.py - Minimal Flask test
from flask import Flask
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

@app.route('/')
def hello():
    return '<h1>Flask is working!</h1><p>If you see this, Flask is running correctly.</p>'

@app.route('/test')
def test():
    return {
        'status': 'ok',
        'anthropic_key_exists': bool(os.getenv('ANTHROPIC_API_KEY')),
        'supabase_url_exists': bool(os.getenv('SUPABASE_URL')),
        'supabase_key_exists': bool(os.getenv('SUPABASE_ANON_KEY'))
    }

if __name__ == '__main__':
    print("🧪 Starting test Flask app...")
    app.run(debug=True, port=5001)  # Different port to avoid conflicts
# web_app.py - Cleaned version for Railway deployment

import os
import sys
import time
import traceback
from datetime import datetime
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv

# Optional: Supabase client
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Add agents folder to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'agents'))

# Import agent orchestrator
try:
    from main import RecipeAgentTeam
    recipe_team = RecipeAgentTeam()
    print("✅ Full RecipeAgentTeam initialized")
except ImportError as e:
    print(f"❌ Could not import RecipeAgentTeam: {e}")
    recipe_team = None

# Flask app setup
app = Flask(__name__, static_folder='web/static', template_folder='web/templates')
CORS(app)

# Supabase setup
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_ANON_KEY')
# supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
supabase: Client = create_client(supabase_url, supabase_key) if supabase_url and supabase_key else None
print("✅ Supabase client initialized" if supabase else "❌ Supabase client not initialized")


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/generate-recipe', methods=['POST'])
def generate_recipe():
    if not recipe_team:
        return jsonify({'error': 'Recipe agent not available'}), 500

    try:
        data = request.get_json()
        user_request = data.get('recipe_request', '').strip()
        complexity = data.get('complexity', 'Medium')  # Default to Medium if not provided

        if not user_request:
            return jsonify({'error': 'Recipe request is required'}), 400

        # Validate complexity level and map frontend values to backend values
        complexity_mapping = {
            'Simple': 'Easy',    # Map frontend "Simple" to backend "Easy"
            'Medium': 'Medium',  # Direct mapping
            'Gourmet': 'High'    # Map frontend "Gourmet" to backend "High"
        }
        
        # Map the complexity or use original if not in mapping
        backend_complexity = complexity_mapping.get(complexity, complexity)
        
        # Validate backend complexity level
        valid_complexity_levels = ['Easy', 'Medium', 'High']
        if backend_complexity not in valid_complexity_levels:
            backend_complexity = 'Medium'  # Fallback to Medium for invalid values

        print(f"🌐 Received request: {user_request} (Frontend: {complexity} → Backend: {backend_complexity})")

        start_time = time.time()
        result = recipe_team.generate_recipe(user_request, backend_complexity)
        generation_time = int(time.time() - start_time)

        if result.get('success'):
            recipe_data = {
                'title': result['recipe'].get('title'),
                'description': result['recipe'].get('description'),
                'original_request': user_request,
                'complexity': complexity,  # Store the frontend complexity value
                'backend_complexity': backend_complexity,  # Store the backend complexity value
                'prep_time': result['recipe'].get('prep_time'),
                'cook_time': result['recipe'].get('cook_time'),
                'total_time': result['recipe'].get('total_time'),
                'servings': result['recipe'].get('servings'),
                'difficulty': result['recipe'].get('difficulty'),
                'ingredients': result['recipe'].get('ingredients', []),
                'instructions': result['recipe'].get('instructions', []),
                'tags': result['recipe'].get('tags', []),
                'cuisine_type': result['recipe'].get('cuisine_type'),
                'meal_type': result['recipe'].get('meal_type'),
                'enhanced': result['recipe'].get('enhanced', False),
                'enhancements_made': result['recipe'].get('enhancements_made', []),
                'chef_notes': result['recipe'].get('chef_notes', []),
                'quality_score': result.get('quality', {}).get('score', 7.0),
                'quality_level': result.get('quality', {}).get('quality_level', 'Good'),
                'iterations_count': result.get('iterations', 1),
                'nutrition_data': result.get('nutrition'),
                'nutrition_score': result.get('nutrition', {}).get('nutrition_score'),
                'dietary_tags': result.get('nutrition', {}).get('dietary_tags', []),
                'generation_time_seconds': generation_time
            }

            if supabase:
                try:
                    supabase.table('recipes').insert(recipe_data).execute()
                except Exception as db_error:
                    print(f"⚠️ Database save failed: {db_error}")

            return jsonify({
                'success': True,
                'recipe': result['recipe'],
                'nutrition': result.get('nutrition'),
                'quality': result.get('quality'),
                'iterations': result.get('iterations'),
                'generation_time': generation_time,
                'process_log': result.get('process_log', []),
                'complexity_requested': complexity
            })

        return jsonify({
            'success': False,
            'error': result.get('error', 'Recipe generation failed'),
            'process_log': result.get('process_log', [])
        }), 500

    except Exception as e:
        print(f"❌ API Error: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/recipes', methods=['GET'])
def get_recipes():
    print("About to query recipes")

    try:
        # Optional: get limit param, default to 10
        limit = int(request.args.get("limit", 10))
        
        print("About to query recipes")
        # Fetch rows from Supabase
        result = supabase.table("recipes").select("*").order("created_at", desc=True).limit(limit).execute()

        # Log and return the results
        print("Done querying recipes")

        return jsonify({
            "success": True,
            "recipes": result.data,
            "count": len(result.data)
        })

    except Exception as e:
        print("Error in get_recipes:", str(e))
        return jsonify({
            "success": False,
            "message": "Failed to retrieve recipes",
            "error": str(e)
        }), 500


@app.route('/api/recipes/<recipe_id>', methods=['GET'])
def get_recipe_by_id(recipe_id):
    print(f"Fetching recipe by ID: {recipe_id}")
    result = supabase.table('recipes').select("*").eq('id', recipe_id).single().execute()
    if result.data:
        return jsonify({
            'success': True,
            'recipe': result.data
        })
    else:
        return jsonify({'success': False, 'error': 'Recipe not found'}), 404



@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'recipe-agent-team',
        'timestamp': datetime.now().isoformat(),
        'agents_available': recipe_team is not None,
        'database_connected': supabase is not None
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
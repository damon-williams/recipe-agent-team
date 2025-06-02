# web_app.py - Optimized with async queue support
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

# Import optimized agent orchestrator
try:
    from main import get_recipe_team
    recipe_team = get_recipe_team()
    print("✅ Optimized RecipeAgentTeam initialized")
except ImportError as e:
    print(f"❌ Could not import RecipeAgentTeam: {e}")
    recipe_team = None

# Flask app setup
app = Flask(__name__, static_folder='web/static', template_folder='web/templates')
CORS(app)

# Supabase setup
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_ANON_KEY')
supabase: Client = create_client(supabase_url, supabase_key) if supabase_url and supabase_key else None
print("✅ Supabase client initialized" if supabase else "❌ Supabase client not initialized")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/generate-recipe', methods=['POST'])
def generate_recipe():
    """Queue a recipe generation request"""
    if not recipe_team:
        return jsonify({'error': 'Recipe agent not available'}), 500

    try:
        data = request.get_json()
        user_request = data.get('recipe_request', '').strip()
        complexity = data.get('complexity', 'Medium')

        if not user_request:
            return jsonify({'error': 'Recipe request is required'}), 400

        # Validate and map complexity
        complexity_mapping = {
            'Simple': 'Easy',
            'Medium': 'Medium',
            'Gourmet': 'High'
        }
        
        backend_complexity = complexity_mapping.get(complexity, complexity)
        valid_complexity_levels = ['Easy', 'Medium', 'High']
        if backend_complexity not in valid_complexity_levels:
            backend_complexity = 'Medium'

        print(f"🌐 Queueing request: {user_request} (Complexity: {backend_complexity})")

        # Queue the recipe generation (non-blocking)
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        task_id = loop.run_until_complete(
            recipe_team.queue_recipe_generation(user_request, backend_complexity)
        )
        
        loop.close()

        # Return task ID for polling
        return jsonify({
            'success': True,
            'task_id': task_id,
            'status': 'queued',
            'message': 'Recipe generation queued. Use task_id to check status.'
        })

    except Exception as e:
        print(f"❌ API Error: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/recipe-status/<task_id>', methods=['GET'])
def get_recipe_status(task_id):
    """Get status of a queued recipe generation"""
    if not recipe_team:
        return jsonify({'error': 'Recipe agent not available'}), 500

    try:
        status = recipe_team.get_recipe_status(task_id)
        
        if 'error' in status:
            return jsonify(status), 404
        
        # If completed, save to database
        if status['status'] == 'completed' and status['result'] and supabase:
            try:
                result = status['result']
                recipe_data = {
                    'title': result['recipe'].get('title'),
                    'description': result['recipe'].get('description'),
                    'original_request': result['recipe'].get('original_request'),
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
                    'generation_time_seconds': result.get('generation_time', 0)
                }

                supabase.table('recipes').insert(recipe_data).execute()
                print(f"✅ Recipe saved to database: {recipe_data.get('title')}")
                
            except Exception as db_error:
                print(f"⚠️ Database save failed: {db_error}")

        return jsonify(status)

    except Exception as e:
        print(f"❌ Status check error: {str(e)}")
        return jsonify({'error': f'Status check failed: {str(e)}'}), 500

@app.route('/api/recipes', methods=['GET'])
def get_recipes():
    """Get recipes with filters (cached for performance)"""
    try:
        # Get parameters from request
        limit = min(int(request.args.get("limit", 10)), 50)  # Cap at 50
        search = request.args.get("search", "").strip()
        meal_type = request.args.get("meal_type", "").strip()
        difficulty = request.args.get("difficulty", "").strip()
        
        # Start with base query
        query = supabase.table("recipes").select("*")
        
        # Apply filters
        if search:
            query = query.or_(f"title.ilike.%{search}%,description.ilike.%{search}%")
        
        if meal_type and meal_type != "all":
            query = query.eq("meal_type", meal_type)
        
        if difficulty and difficulty != "all":
            query = query.eq("difficulty", difficulty)
        
        # Apply ordering and limit
        query = query.order("created_at", desc=True).limit(limit)
        
        result = query.execute()

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
    """Get individual recipe by ID"""
    try:
        result = supabase.table('recipes').select("*").eq('id', recipe_id).single().execute()
        if result.data:
            return jsonify({
                'success': True,
                'recipe': result.data
            })
        else:
            return jsonify({'success': False, 'error': 'Recipe not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    queue_stats = {}
    if recipe_team:
        queue_stats = {
            'processing_count': recipe_team.queue.processing_count,
            'max_concurrent': recipe_team.queue.max_concurrent,
            'total_tasks': len(recipe_team.queue.tasks)
        }
    
    return jsonify({
        'status': 'healthy',
        'service': 'recipe-agent-team',
        'timestamp': datetime.now().isoformat(),
        'agents_available': recipe_team is not None,
        'database_connected': supabase is not None,
        'queue_stats': queue_stats
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, threaded=True)  # Enable threading
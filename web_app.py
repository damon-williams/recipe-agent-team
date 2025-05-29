# web_app.py
import os
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from supabase import create_client, Client
import json
from datetime import datetime
import time
from main import RecipeAgentTeam
import traceback

load_dotenv()

app = Flask(__name__, template_folder='web/templates', static_folder='web/static')
CORS(app)

# Initialize Supabase
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_ANON_KEY')
supabase: Client = create_client(supabase_url, supabase_key)

# Initialize Recipe Agent Team
recipe_team = RecipeAgentTeam()

@app.route('/')
def index():
    """Serve the main recipe generator page"""
    return render_template('index.html')

@app.route('/api/generate-recipe', methods=['POST'])
def generate_recipe():
    """Generate a new recipe using the agent team"""
    
    try:
        data = request.get_json()
        user_request = data.get('recipe_request', '').strip()
        
        if not user_request:
            return jsonify({'error': 'Recipe request is required'}), 400
        
        # Get user IP for simple tracking
        user_ip = request.remote_addr
        
        print(f"🌐 Web request: '{user_request}' from {user_ip}")
        
        # Generate recipe using the agent team
        start_time = time.time()
        result = recipe_team.generate_recipe(user_request)
        generation_time = int(time.time() - start_time)
        
        if result.get('success'):
            # Save recipe to Supabase
            recipe_data = {
                'title': result['recipe'].get('title'),
                'description': result['recipe'].get('description'),
                'original_request': user_request,
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
                'quality_score': result['quality'].get('score'),
                'quality_level': result['quality'].get('quality_level'),
                'iterations_count': result.get('iterations', 1),
                'nutrition_data': result.get('nutrition'),
                'nutrition_score': result.get('nutrition', {}).get('nutrition_score'),
                'dietary_tags': result.get('nutrition', {}).get('dietary_tags', []),
                'generation_time_seconds': generation_time
            }
            
            # Insert into Supabase
            recipe_response = supabase.table('recipes').insert(recipe_data).execute()
            
            if recipe_response.data:
                recipe_id = recipe_response.data[0]['id']
                
                # Log the generation
                log_data = {
                    'recipe_id': recipe_id,
                    'original_request': user_request,
                    'agent_logs': result.get('process_log', []),
                    'success': True,
                    'generation_time_seconds': generation_time
                }
                supabase.table('generation_logs').insert(log_data).execute()
                
                # Return success response
                return jsonify({
                    'success': True,
                    'recipe_id': recipe_id,
                    'recipe': result['recipe'],
                    'nutrition': result.get('nutrition'),
                    'quality': result.get('quality'),
                    'iterations': result.get('iterations'),
                    'generation_time': generation_time,
                    'process_log': result.get('process_log', [])
                })
            
        else:
            # Handle generation failure
            error_log = {
                'original_request': user_request,
                'agent_logs': result.get('process_log', []),
                'error_message': result.get('error', 'Unknown error'),
                'success': False,
                'generation_time_seconds': generation_time
            }
            supabase.table('generation_logs').insert(error_log).execute()
            
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
    """Get recent recipes with optional filtering"""
    
    try:
        # Get query parameters
        limit = int(request.args.get('limit', 20))
        meal_type = request.args.get('meal_type')
        difficulty = request.args.get('difficulty')
        min_quality = float(request.args.get('min_quality', 0))
        
        # Build query
        query = supabase.table('recipes').select('*')
        
        if meal_type:
            query = query.eq('meal_type', meal_type)
        if difficulty:
            query = query.eq('difficulty', difficulty)
        if min_quality > 0:
            query = query.gte('quality_score', min_quality)
        
        # Execute query
        response = query.order('created_at', desc=True).limit(limit).execute()
        
        return jsonify({
            'success': True,
            'recipes': response.data,
            'count': len(response.data)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/recipes/<recipe_id>', methods=['GET'])
def get_recipe(recipe_id):
    """Get a specific recipe by ID"""
    
    try:
        # Get recipe
        response = supabase.table('recipes').select('*').eq('id', recipe_id).execute()
        
        if not response.data:
            return jsonify({'error': 'Recipe not found'}), 404
        
        recipe = response.data[0]
        
        # Increment view count
        supabase.table('recipes').update({
            'views_count': recipe['views_count'] + 1
        }).eq('id', recipe_id).execute()
        
        return jsonify({
            'success': True,
            'recipe': recipe
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/recipes/<recipe_id>/rate', methods=['POST'])
def rate_recipe(recipe_id):
    """Rate a recipe"""
    
    try:
        data = request.get_json()
        rating = data.get('rating')
        comment = data.get('comment', '')
        
        if not rating or rating < 1 or rating > 5:
            return jsonify({'error': 'Rating must be between 1 and 5'}), 400
        
        # Insert rating
        rating_data = {
            'recipe_id': recipe_id,
            'user_ip': request.remote_addr,
            'rating': rating,
            'comment': comment
        }
        
        supabase.table('recipe_ratings').insert(rating_data).execute()
        
        return jsonify({'success': True, 'message': 'Rating submitted'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get app statistics"""
    
    try:
        # Get recipe count
        recipes_response = supabase.table('recipes').select('id', count='exact').execute()
        recipe_count = recipes_response.count
        
        # Get average quality score
        quality_response = supabase.table('recipes').select('quality_score').execute()
        quality_scores = [r['quality_score'] for r in quality_response.data if r['quality_score']]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        # Get popular meal types
        meal_types_response = supabase.table('recipes').select('meal_type').execute()
        meal_type_counts = {}
        for recipe in meal_types_response.data:
            meal_type = recipe['meal_type']
            meal_type_counts[meal_type] = meal_type_counts.get(meal_type, 0) + 1
        
        return jsonify({
            'success': True,
            'stats': {
                'total_recipes': recipe_count,
                'average_quality_score': round(avg_quality, 1),
                'popular_meal_types': dict(sorted(meal_type_counts.items(), key=lambda x: x[1], reverse=True))
            }
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'recipe-agent-team',
        'timestamp': datetime.now().isoformat()
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Check required environment variables
    required_vars = ['ANTHROPIC_API_KEY', 'SUPABASE_URL', 'SUPABASE_ANON_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Please add them to your .env file")
        exit(1)
    
    print("🚀 Starting Recipe Agent Team Web App...")
    print("📡 API endpoints available at http://localhost:5001/api/")
    print("🌐 Web interface at http://localhost:5001/")
    
    app.run(debug=True, port=5001)
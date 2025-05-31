# web_app.py - Full-featured version for Vercel
import os
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from dotenv import load_dotenv
from supabase import create_client, Client
import json
from datetime import datetime
import time
from main import RecipeAgentTeam
import traceback

load_dotenv()

app = Flask(__name__)
CORS(app)

# Initialize Supabase
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_ANON_KEY')
supabase: Client = create_client(supabase_url, supabase_key) if supabase_url and supabase_key else None

# Initialize Recipe Agent Team
recipe_team = RecipeAgentTeam()

# Embed the HTML template directly to avoid file path issues
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Recipe Generator - Multi-Agent Cooking Assistant</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh; color: #333;
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { text-align: center; color: white; margin-bottom: 40px; }
        .header h1 { font-size: 3rem; font-weight: 700; margin-bottom: 10px; text-shadow: 0 2px 4px rgba(0,0,0,0.3); }
        .header p { font-size: 1.2rem; opacity: 0.9; max-width: 600px; margin: 0 auto; }
        .recipe-generator { background: white; border-radius: 20px; box-shadow: 0 20px 40px rgba(0,0,0,0.1); padding: 40px; margin-bottom: 40px; }
        .input-group { margin-bottom: 20px; }
        .input-group label { display: block; font-weight: 600; margin-bottom: 8px; color: #555; }
        .recipe-input { width: 100%; padding: 15px 20px; border: 2px solid #e1e5e9; border-radius: 12px; font-size: 1rem; transition: all 0.3s ease; }
        .recipe-input:focus { outline: none; border-color: #667eea; box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1); }
        .generate-btn { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; padding: 15px 30px; border-radius: 12px; font-size: 1.1rem; font-weight: 600; cursor: pointer; transition: all 0.3s ease; width: 100%; }
        .generate-btn:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3); }
        .generate-btn:disabled { opacity: 0.6; cursor: not-allowed; }
        .loading { display: none; text-align: center; padding: 40px; }
        .loading-spinner { width: 40px; height: 40px; border: 4px solid #f3f3f3; border-top: 4px solid #667eea; border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 20px; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .progress-log { background: #f8f9fa; border-radius: 12px; padding: 20px; margin-top: 20px; max-height: 200px; overflow-y: auto; }
        .progress-item { padding: 8px 0; border-bottom: 1px solid #eee; }
        .progress-item:last-child { border-bottom: none; }
        .progress-item.completed { color: #28a745; font-weight: 500; }
        .progress-item.in-progress { color: #007bff; font-weight: 500; }
        .recipe-result { display: none; background: white; border-radius: 20px; box-shadow: 0 20px 40px rgba(0,0,0,0.1); padding: 40px; margin-bottom: 40px; }
        .recipe-title { font-size: 2.5rem; font-weight: 700; color: #333; margin-bottom: 10px; text-align: center; }
        .recipe-meta { display: flex; justify-content: center; gap: 20px; margin: 20px 0; flex-wrap: wrap; }
        .meta-item { background: #f8f9fa; padding: 8px 16px; border-radius: 20px; font-weight: 500; color: #666; }
        .quality-score { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 8px 16px; border-radius: 20px; font-weight: 600; }
        .section-title { font-size: 1.5rem; font-weight: 600; color: #333; margin: 20px 0 15px 0; }
        .ingredients-list { background: #f8f9fa; padding: 20px; border-radius: 12px; margin-bottom: 20px; }
        .ingredients-list li { margin-bottom: 8px; padding: 8px; background: white; border-radius: 6px; border-left: 4px solid #667eea; }
        .instructions-list { counter-reset: step-counter; }
        .instruction-item { background: #f8f9fa; padding: 20px; border-radius: 12px; margin-bottom: 12px; counter-increment: step-counter; position: relative; padding-left: 60px; line-height: 1.6; }
        .instruction-item::before { content: counter(step-counter); position: absolute; left: 20px; top: 20px; background: #667eea; color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 600; font-size: 0.9rem; }
        .nutrition-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin: 20px 0; }
        .nutrition-card { background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; }
        .nutrition-value { font-size: 1.5rem; font-weight: 700; color: #667eea; }
        .nutrition-label { color: #666; font-weight: 500; margin-top: 5px; font-size: 0.9rem; }
        .tags { display: flex; flex-wrap: wrap; gap: 8px; margin: 20px 0; }
        .tag { background: #667eea; color: white; padding: 6px 12px; border-radius: 16px; font-size: 0.9rem; font-weight: 500; }
        .enhancement-list { background: #e8f5e8; padding: 20px; border-radius: 12px; border-left: 4px solid #28a745; margin: 20px 0; }
        .enhancement-list ul { margin: 0; padding-left: 20px; }
        .enhancement-list li { margin-bottom: 8px; color: #155724; }
        .error-message { background: #f8d7da; color: #721c24; padding: 15px 20px; border-radius: 8px; margin-top: 20px; display: none; }
        .generation-stats { background: #f8f9fa; border-radius: 12px; padding: 20px; text-align: center; margin-top: 30px; color: #666; }
        @media (max-width: 768px) {
            .header h1 { font-size: 2rem; }
            .recipe-generator, .recipe-result { padding: 20px; }
            .nutrition-grid { grid-template-columns: repeat(2, 1fr); }
            .recipe-title { font-size: 2rem; }
        }
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <h1>🤖 AI Recipe Generator</h1>
            <p>Multi-agent cooking assistant that creates, enhances, and analyzes recipes using advanced AI</p>
        </header>
        
        <div class="recipe-generator">
            <div class="input-group">
                <label for="recipeInput">What would you like to cook?</label>
                <input type="text" id="recipeInput" class="recipe-input" 
                       placeholder="e.g., 'spicy chicken tacos', 'healthy pasta dish', 'chocolate dessert for date night'" 
                       maxlength="200">
            </div>
            
            <button id="generateBtn" class="generate-btn">
                🚀 Generate Recipe with AI Agents
            </button>
            
            <div id="loading" class="loading">
                <div class="loading-spinner"></div>
                <h3>AI agents are working on your recipe...</h3>
                <p>This may take 30-60 seconds</p>
                <div id="progressLog" class="progress-log"></div>
            </div>
            
            <div id="errorMessage" class="error-message"></div>
        </div>
        
        <div id="recipeResult" class="recipe-result">
            <!-- Recipe content will be dynamically inserted here -->
        </div>
    </div>

    <script>
        document.getElementById('generateBtn').addEventListener('click', generateRecipe);
        document.getElementById('recipeInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') generateRecipe();
        });

        function showLoading() {
            document.getElementById('generateBtn').disabled = true;
            document.getElementById('generateBtn').textContent = 'Generating...';
            document.getElementById('loading').style.display = 'block';
            document.getElementById('recipeResult').style.display = 'none';
            simulateProgress();
        }

        function hideLoading() {
            document.getElementById('generateBtn').disabled = false;
            document.getElementById('generateBtn').textContent = '🚀 Generate Recipe with AI Agents';
            document.getElementById('loading').style.display = 'none';
        }

        function simulateProgress() {
            const steps = [
                '🤖 Recipe Generator: Creating base recipe...',
                '🔍 Web Researcher: Finding cooking inspiration...',
                '📝 Recipe Enhancer: Adding creative improvements...',
                '🥗 Nutrition Analyst: Calculating health metrics...',
                '⭐ Quality Evaluator: Scoring recipe quality...'
            ];
            
            let currentStep = 0;
            const progressLog = document.getElementById('progressLog');
            progressLog.innerHTML = '';
            
            const interval = setInterval(() => {
                if (currentStep < steps.length) {
                    const progressItem = document.createElement('div');
                    progressItem.className = 'progress-item in-progress';
                    progressItem.textContent = steps[currentStep];
                    progressLog.appendChild(progressItem);
                    
                    if (currentStep > 0) {
                        const prevItem = progressLog.children[currentStep - 1];
                        prevItem.className = 'progress-item completed';
                        prevItem.textContent += ' ✓';
                    }
                    
                    currentStep++;
                    progressLog.scrollTop = progressLog.scrollHeight;
                } else {
                    clearInterval(interval);
                    if (progressLog.children.length > 0) {
                        const lastItem = progressLog.children[progressLog.children.length - 1];
                        lastItem.className = 'progress-item completed';
                        lastItem.textContent += ' ✓';
                    }
                }
            }, 2500);
        }

        async function generateRecipe() {
            const request = document.getElementById('recipeInput').value.trim();
            if (!request) {
                showError('Please enter a recipe request');
                return;
            }
            
            showLoading();
            hideError();
            
            try {
                const response = await fetch('/api/generate-recipe', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ recipe_request: request })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    displayRecipe(data);
                } else {
                    showError(data.error || 'Recipe generation failed');
                }
            } catch (error) {
                console.error('Error:', error);
                showError('Network error. Please try again.');
            } finally {
                hideLoading();
            }
        }

        function displayRecipe(data) {
            const recipe = data.recipe;
            const nutrition = data.nutrition;
            const quality = data.quality;
            
            const nutritionHtml = nutrition && nutrition.nutrition_per_serving ? `
                <h2 class="section-title">📊 Nutrition (per serving)</h2>
                <div class="nutrition-grid">
                    <div class="nutrition-card">
                        <div class="nutrition-value">${nutrition.nutrition_per_serving.calories || 'N/A'}</div>
                        <div class="nutrition-label">Calories</div>
                    </div>
                    <div class="nutrition-card">
                        <div class="nutrition-value">${nutrition.nutrition_per_serving.protein || 'N/A'}g</div>
                        <div class="nutrition-label">Protein</div>
                    </div>
                    <div class="nutrition-card">
                        <div class="nutrition-value">${nutrition.nutrition_per_serving.carbs || 'N/A'}g</div>
                        <div class="nutrition-label">Carbs</div>
                    </div>
                    <div class="nutrition-card">
                        <div class="nutrition-value">${nutrition.nutrition_per_serving.fat || 'N/A'}g</div>
                        <div class="nutrition-label">Fat</div>
                    </div>
                </div>
            ` : '';

            const enhancementsHtml = recipe.enhancements_made && recipe.enhancements_made.length > 0 ? `
                <h2 class="section-title">✨ AI Enhancements</h2>
                <div class="enhancement-list">
                    <ul>
                        ${recipe.enhancements_made.map(enhancement => `<li>${enhancement}</li>`).join('')}
                    </ul>
                </div>
            ` : '';
            
            const html = `
                <h1 class="recipe-title">${recipe.title}</h1>
                <p style="text-align: center; font-size: 1.1rem; color: #666; margin-bottom: 20px;">${recipe.description || ''}</p>
                
                <div class="recipe-meta">
                    <span class="meta-item">⏱️ Prep: ${recipe.prep_time}</span>
                    <span class="meta-item">🔥 Cook: ${recipe.cook_time}</span>
                    <span class="meta-item">👥 Serves: ${recipe.servings}</span>
                    <span class="meta-item">📊 ${recipe.difficulty}</span>
                    <span class="quality-score">⭐ ${quality?.score || 'N/A'}/10</span>
                </div>
                
                <h2 class="section-title">🥘 Ingredients</h2>
                <div class="ingredients-list">
                    <ul>
                        ${recipe.ingredients.map(ingredient => `<li>${ingredient}</li>`).join('')}
                    </ul>
                </div>
                
                <h2 class="section-title">👨‍🍳 Instructions</h2>
                <div class="instructions-list">
                    ${recipe.instructions.map(instruction => `<div class="instruction-item">${instruction}</div>`).join('')}
                </div>
                
                ${nutritionHtml}
                ${enhancementsHtml}
                
                <div class="tags">
                    ${recipe.tags ? recipe.tags.map(tag => `<span class="tag">${tag}</span>`).join('') : ''}
                    ${nutrition?.dietary_tags ? nutrition.dietary_tags.map(tag => `<span class="tag">${tag}</span>`).join('') : ''}
                </div>
                
                <div class="generation-stats">
                    <p><strong>Generated in ${data.generation_time} seconds with ${data.iterations} iteration${data.iterations > 1 ? 's' : ''}</strong></p>
                    <p style="margin-top: 10px;">Quality Level: ${quality?.quality_level || 'Good'} | Confidence: ${quality?.confidence || 'medium'}</p>
                </div>
            `;
            
            document.getElementById('recipeResult').innerHTML = html;
            document.getElementById('recipeResult').style.display = 'block';
            document.getElementById('recipeResult').scrollIntoView({ behavior: 'smooth' });
        }

        function showError(message) {
            const errorDiv = document.getElementById('errorMessage');
            errorDiv.textContent = message;
            errorDiv.style.display = 'block';
        }

        function hideError() {
            document.getElementById('errorMessage').style.display = 'none';
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    """Serve the main recipe generator page"""
    return render_template_string(HTML_TEMPLATE)

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
            recipe_data = None
            if supabase:
                try:
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
                        'quality_score': result['quality'].get('score') if result.get('quality') else 7.0,
                        'quality_level': result['quality'].get('quality_level') if result.get('quality') else 'Good',
                        'iterations_count': result.get('iterations', 1),
                        'nutrition_data': result.get('nutrition'),
                        'nutrition_score': result.get('nutrition', {}).get('nutrition_score') if result.get('nutrition') else None,
                        'dietary_tags': result.get('nutrition', {}).get('dietary_tags', []) if result.get('nutrition') else [],
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
                except Exception as db_error:
                    print(f"⚠️ Database save failed: {db_error}")
            
            # Return success response
            return jsonify({
                'success': True,
                'recipe_id': recipe_data.get('id') if recipe_data else None,
                'recipe': result['recipe'],
                'nutrition': result.get('nutrition'),
                'quality': result.get('quality'),
                'iterations': result.get('iterations'),
                'generation_time': generation_time,
                'process_log': result.get('process_log', [])
            })
            
        else:
            # Handle generation failure
            if supabase:
                try:
                    error_log = {
                        'original_request': user_request,
                        'agent_logs': result.get('process_log', []),
                        'error_message': result.get('error', 'Unknown error'),
                        'success': False,
                        'generation_time_seconds': generation_time
                    }
                    supabase.table('generation_logs').insert(error_log).execute()
                except Exception as db_error:
                    print(f"⚠️ Error log save failed: {db_error}")
            
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
    
    if not supabase:
        return jsonify({'success': False, 'error': 'Database not configured'}), 500
    
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

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'recipe-agent-team',
        'timestamp': datetime.now().isoformat(),
        'agents_available': True,
        'database_connected': supabase is not None
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# For Vercel deployment
if __name__ == '__main__':
    # Check required environment variables
    required_vars = ['ANTHROPIC_API_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Please add them to your Vercel environment variables")
        exit(1)
    
    print("🚀 Starting Recipe Agent Team Web App...")
    print("📡 API endpoints available")
    print("🌐 Full multi-agent system enabled")
    
    app.run(debug=True, port=5001)# web_app.py - Lightweight version for Vercel deployment
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import json
from datetime import datetime
import time
import traceback
import httpx
import requests

# Import agents - make sure they're in the same directory
try:
    from main import RecipeAgentTeam
except ImportError:
    # Lightweight fallback agents
    from recipe_generator import RecipeGenerator
    print("⚠️ Using lightweight agent setup for Vercel")

load_dotenv()

# For Vercel, we need to handle the template and static folders differently
app = Flask(__name__)
CORS(app)

# Simple HTTP client for Supabase instead of full SDK
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_ANON_KEY')

def supabase_insert(table, data):
    """Lightweight Supabase insert using direct HTTP calls"""
    if not supabase_url or not supabase_key:
        return None
    
    try:
        headers = {
            'apikey': supabase_key,
            'Authorization': f'Bearer {supabase_key}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(
            f"{supabase_url}/rest/v1/{table}",
            headers=headers,
            json=data,
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            return response.json()
        else:
            print(f"Supabase error: {response.status_code}")
            return None
    except Exception as e:
        print(f"Supabase insert failed: {e}")
        return None

# Initialize Recipe Agent Team
try:
    recipe_team = RecipeAgentTeam()
except:
    # Lightweight fallback - just use the recipe generator
    class MinimalRecipeTeam:
        def __init__(self):
            self.generator = RecipeGenerator()
        
        def generate_recipe(self, user_request):
            try:
                print(f"🤖 Generating recipe for: {user_request}")
                
                # Simple generation without heavy agents
                base_recipe = self.generator.create_recipe(user_request)
                if not base_recipe.get('success'):
                    return {'success': False, 'error': base_recipe.get('error')}
                
                # Add basic quality score
                base_recipe['quality_score'] = 7.5
                base_recipe['quality_level'] = 'Good'
                
                return {
                    'success': True,
                    'recipe': base_recipe,
                    'nutrition': {'nutrition_per_serving': {'calories': 'Estimated', 'protein': 'N/A'}},
                    'quality': {'score': 7.5, 'quality_level': 'Good', 'confidence': 'medium'},
                    'iterations': 1,
                    'process_log': ['Recipe generated successfully (lightweight mode)']
                }
                
            except Exception as e:
                return {
                    'success': False,
                    'error': f"Recipe generation failed: {str(e)}",
                    'process_log': [f"Error: {str(e)}"]
                }
    
    recipe_team = MinimalRecipeTeam()

@app.route('/')
def index():
    """Serve the main recipe generator page"""
    # For Vercel, we'll serve a simple HTML page directly
    return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Recipe Generator - Multi-Agent Cooking Assistant</title>
    <style>
        /* Add your CSS here or load from CDN */
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { text-align: center; color: white; margin-bottom: 40px; }
        .header h1 { font-size: 3rem; font-weight: 700; margin-bottom: 10px; }
        .recipe-generator { 
            background: white; border-radius: 20px; 
            box-shadow: 0 20px 40px rgba(0,0,0,0.1); padding: 40px; 
        }
        .recipe-input { 
            width: 100%; padding: 15px 20px; border: 2px solid #e1e5e9; 
            border-radius: 12px; font-size: 1rem; margin-bottom: 20px;
        }
        .generate-btn { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; border: none; padding: 15px 30px; border-radius: 12px;
            font-size: 1.1rem; font-weight: 600; cursor: pointer; width: 100%;
        }
        .loading { display: none; text-align: center; padding: 40px; }
        .result { display: none; margin-top: 30px; padding: 30px; background: #f8f9fa; border-radius: 15px; }
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <h1>🤖 AI Recipe Generator</h1>
            <p>Multi-agent cooking assistant that creates, enhances, and analyzes recipes using advanced AI</p>
        </header>
        
        <div class="recipe-generator">
            <div>
                <label for="recipeInput">What would you like to cook?</label>
                <input type="text" id="recipeInput" class="recipe-input" 
                       placeholder="e.g., 'spicy chicken tacos', 'healthy pasta dish', 'chocolate dessert for date night'" 
                       maxlength="200">
            </div>
            
            <button id="generateBtn" class="generate-btn">
                🚀 Generate Recipe with AI Agents
            </button>
            
            <div id="loading" class="loading">
                <h3>AI agents are working on your recipe...</h3>
                <p>This may take 30-60 seconds</p>
            </div>
            
            <div id="result" class="result"></div>
        </div>
    </div>

    <script>
        document.getElementById('generateBtn').addEventListener('click', async () => {
            const request = document.getElementById('recipeInput').value.trim();
            if (!request) {
                alert('Please enter a recipe request');
                return;
            }
            
            document.getElementById('loading').style.display = 'block';
            document.getElementById('result').style.display = 'none';
            
            try {
                const response = await fetch('/api/generate-recipe', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ recipe_request: request })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    const recipe = data.recipe;
                    document.getElementById('result').innerHTML = `
                        <h2>${recipe.title}</h2>
                        <p><strong>Description:</strong> ${recipe.description}</p>
                        <p><strong>Prep Time:</strong> ${recipe.prep_time} | <strong>Cook Time:</strong> ${recipe.cook_time} | <strong>Serves:</strong> ${recipe.servings}</p>
                        <h3>Ingredients:</h3>
                        <ul>${recipe.ingredients.map(ing => `<li>${ing}</li>`).join('')}</ul>
                        <h3>Instructions:</h3>
                        <ol>${recipe.instructions.map(inst => `<li>${inst}</li>`).join('')}</ol>
                        ${data.quality ? `<p><strong>Quality Score:</strong> ${data.quality.score}/10</p>` : ''}
                    `;
                    document.getElementById('result').style.display = 'block';
                } else {
                    alert('Error: ' + data.error);
                }
            } catch (error) {
                alert('Network error. Please try again.');
            } finally {
                document.getElementById('loading').style.display = 'none';
            }
        });
        
        document.getElementById('recipeInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') document.getElementById('generateBtn').click();
        });
    </script>
</body>
</html>
    '''

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
            # Save recipe to Supabase if available
            recipe_data = None
            if supabase_url and supabase_key:
                try:
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
                        'quality_score': result['quality'].get('score') if result.get('quality') else 7.0,
                        'quality_level': result['quality'].get('quality_level') if result.get('quality') else 'Good',
                        'iterations_count': result.get('iterations', 1),
                        'nutrition_data': result.get('nutrition'),
                        'nutrition_score': result.get('nutrition', {}).get('nutrition_score') if result.get('nutrition') else None,
                        'dietary_tags': result.get('nutrition', {}).get('dietary_tags', []) if result.get('nutrition') else [],
                        'generation_time_seconds': generation_time
                    }
                    
                    # Insert into Supabase using lightweight HTTP call
                    recipe_response = supabase_insert('recipes', recipe_data)
                    
                    if recipe_response:
                        recipe_id = recipe_response[0]['id'] if isinstance(recipe_response, list) else recipe_response.get('id')
                        
                        # Log the generation
                        log_data = {
                            'recipe_id': recipe_id,
                            'original_request': user_request,
                            'agent_logs': result.get('process_log', []),
                            'success': True,
                            'generation_time_seconds': generation_time
                        }
                        supabase_insert('generation_logs', log_data)
                except Exception as db_error:
                    print(f"⚠️ Database save failed: {db_error}")
            
            # Return success response
            return jsonify({
                'success': True,
                'recipe_id': recipe_data.get('id') if recipe_data else None,
                'recipe': result['recipe'],
                'nutrition': result.get('nutrition'),
                'quality': result.get('quality'),
                'iterations': result.get('iterations'),
                'generation_time': generation_time,
                'process_log': result.get('process_log', [])
            })
            
        else:
            # Handle generation failure
            if supabase_url and supabase_key:
                try:
                    error_log = {
                        'original_request': user_request,
                        'agent_logs': result.get('process_log', []),
                        'error_message': result.get('error', 'Unknown error'),
                        'success': False,
                        'generation_time_seconds': generation_time
                    }
                    supabase_insert('generation_logs', error_log)
                except Exception as db_error:
                    print(f"⚠️ Error log save failed: {db_error}")
            
            return jsonify({
                'success': False,
                'error': result.get('error', 'Recipe generation failed'),
                'process_log': result.get('process_log', [])
            }), 500
    
    except Exception as e:
        print(f"❌ API Error: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'recipe-agent-team',
        'timestamp': datetime.now().isoformat(),
        'agents_available': True,
        'database_connected': bool(supabase_url and supabase_key)
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# For Vercel
app = app
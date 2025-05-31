# web_app.py - Recipe Agent Team Flask Application
import os
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv
from supabase import create_client, Client
import json
from datetime import datetime
import time
from main import RecipeAgentTeam
import traceback

load_dotenv()

app = Flask(__name__, static_folder='web/static', template_folder='web/templates')
CORS(app)

# Initialize Supabase
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_ANON_KEY')
supabase: Client = create_client(supabase_url, supabase_key) if supabase_url and supabase_key else None

# Initialize Recipe Agent Team
recipe_team = RecipeAgentTeam()

# Embed the HTML template directly
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Recipe Generator - Multi-Agent Cooking Assistant</title>
    <link rel="stylesheet" href="/static/styles.css">
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

    <script src="/static/script.js"></script>
</body>
</html>
'''
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

@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files (CSS, JS, etc.)"""
    return app.send_static_file(filename)

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

if __name__ == '__main__':
    # Railway deployment configuration
    port = int(os.environ.get('PORT', 8000))
    
    print("🚀 Starting Recipe Agent Team Web App...")
    print(f"📡 Server starting on port {port}")
    print(f"🤖 Agent system: {'Full multi-agent' if FULL_AGENTS_AVAILABLE else 'Claude-only fallback'}")
    print(f"🗄️ Database: {'Connected' if supabase else 'Not configured'}")
    
    app.run(host='0.0.0.0', port=port, debug=False)# web_app.py - Lightweight version for Vercel deployment
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

# web_app.py - Recipe Agent Team Flask Application
import os
import sys
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from dotenv import load_dotenv
from supabase import create_client, Client
import json
from datetime import datetime
import time
import traceback

# Add agents folder to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'agents'))

load_dotenv()

app = Flask(__name__)
CORS(app)

# Initialize Supabase
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_ANON_KEY')
supabase: Client = create_client(supabase_url, supabase_key) if supabase_url and supabase_key else None

# Import agents with error handling
try:
    from main import RecipeAgentTeam
    FULL_AGENTS_AVAILABLE = True
    print("✅ Full agent system loaded from main.py")
except ImportError as e:
    print(f"⚠️ Could not import main RecipeAgentTeam: {e}")
    print("⚠️ Trying to import individual agents from agents/ folder...")
    
    try:
        from recipe_generator import RecipeGenerator
        from recipe_enhancer import RecipeEnhancer
        from web_researcher import WebResearcher
        from nutrition_analyst import NutritionAnalyst
        from quality_evaluator import QualityEvaluator
        
        print("✅ Individual agents imported successfully")
        FULL_AGENTS_AVAILABLE = True
        
        # Create a simple orchestrator
        class SimpleRecipeTeam:
            def __init__(self):
                self.generator = RecipeGenerator()
                self.enhancer = RecipeEnhancer()
                self.researcher = WebResearcher()
                self.nutrition = NutritionAnalyst()
                self.evaluator = QualityEvaluator()
                print("🤖 Simple agent team initialized")
            
            def generate_recipe(self, user_request):
                try:
                    print(f"🎯 Generating recipe for: {user_request}")
                    process_log = []
                    
                    # Step 1: Generate base recipe
                    process_log.append("🤖 Recipe Generator: Creating base recipe...")
                    base_recipe = self.generator.create_recipe(user_request)
                    
                    if not base_recipe.get('success'):
                        return {
                            'success': False, 
                            'error': base_recipe.get('error'),
                            'process_log': process_log
                        }
                    
                    process_log.append(f"✅ Generated: {base_recipe.get('title')}")
                    
                    # Step 2: Research inspiration (optional)
                    inspiration_data = None
                    try:
                        process_log.append("🔍 Web Researcher: Finding cooking inspiration...")
                        inspiration_data = self.researcher.find_inspiration(
                            base_recipe.get('title', ''), 
                            base_recipe.get('meal_type')
                        )
                        process_log.append("✅ Research completed")
                    except Exception as e:
                        print(f"⚠️ Research failed: {e}")
                        process_log.append("⚠️ Research failed - using base recipe")
                    
                    # Step 3: Enhance recipe
                    enhanced_recipe = base_recipe
                    try:
                        process_log.append("📝 Recipe Enhancer: Adding improvements...")
                        enhanced_recipe = self.enhancer.enhance_recipe(base_recipe, inspiration_data)
                        
                        enhancements = enhanced_recipe.get('enhancements_made', [])
                        if enhancements:
                            process_log.append(f"✅ Applied {len(enhancements)} enhancements")
                        else:
                            process_log.append("✅ Recipe enhanced")
                    except Exception as e:
                        print(f"⚠️ Enhancement failed: {e}")
                        process_log.append("⚠️ Enhancement failed - using base recipe")
                        enhanced_recipe = base_recipe
                    
                    # Step 4: Analyze nutrition
                    nutrition_data = None
                    try:
                        process_log.append("🥗 Nutrition Analyst: Calculating health metrics...")
                        nutrition_data = self.nutrition.analyze_nutrition(enhanced_recipe)
                        
                        if nutrition_data and nutrition_data.get('nutrition_per_serving'):
                            calories = nutrition_data['nutrition_per_serving'].get('calories', 'N/A')
                            process_log.append(f"✅ Nutrition: ~{calories} calories/serving")
                        else:
                            process_log.append("✅ Basic nutrition estimates provided")
                    except Exception as e:
                        print(f"⚠️ Nutrition analysis failed: {e}")
                        process_log.append("⚠️ Nutrition analysis failed")
                        nutrition_data = self._create_fallback_nutrition(enhanced_recipe)
                    
                    # Step 5: Evaluate quality
                    quality_data = None
                    try:
                        process_log.append("⭐ Quality Evaluator: Scoring recipe quality...")
                        quality_data = self.evaluator.evaluate_recipe(
                            enhanced_recipe, nutrition_data, inspiration_data
                        )
                        
                        score = quality_data.get('score', 0)
                        quality_level = quality_data.get('quality_level', 'Unknown')
                        process_log.append(f"✅ Quality Score: {score}/10 ({quality_level})")
                    except Exception as e:
                        print(f"⚠️ Quality evaluation failed: {e}")
                        process_log.append("⚠️ Quality evaluation failed")
                        quality_data = self._create_fallback_quality()
                    
                    process_log.append("🎉 Recipe generation complete!")
                    
                    return {
                        'success': True,
                        'recipe': enhanced_recipe,
                        'nutrition': nutrition_data,
                        'quality': quality_data,
                        'iterations': 1,
                        'process_log': process_log
                    }
                    
                except Exception as e:
                    error_msg = f"Recipe generation failed: {str(e)}"
                    print(f"❌ {error_msg}")
                    return {
                        'success': False,
                        'error': error_msg,
                        'process_log': process_log + [f"❌ {error_msg}"]
                    }
            
            def _create_fallback_nutrition(self, recipe):
                """Create basic nutrition estimates"""
                meal_type = recipe.get('meal_type', 'dinner').lower()
                base_estimates = {
                    'breakfast': {'calories': 350, 'protein': 15, 'carbs': 45, 'fat': 12},
                    'lunch': {'calories': 450, 'protein': 20, 'carbs': 50, 'fat': 15},
                    'dinner': {'calories': 550, 'protein': 25, 'carbs': 55, 'fat': 18},
                    'snack': {'calories': 200, 'protein': 8, 'carbs': 25, 'fat': 8},
                    'dessert': {'calories': 300, 'protein': 5, 'carbs': 45, 'fat': 12}
                }
                
                estimate = base_estimates.get(meal_type, base_estimates['dinner']).copy()
                estimate.update({'fiber': 4, 'sugar': 8, 'sodium': 400})
                
                return {
                    'nutrition_per_serving': estimate,
                    'health_insights': ["Nutrition estimates provided"],
                    'analysis_method': 'fallback_estimate',
                    'confidence': 'low'
                }
            
            def _create_fallback_quality(self):
                """Create basic quality score"""
                return {
                    'score': 7.0,
                    'quality_verdict': 'good',
                    'quality_level': 'Good',
                    'confidence': 'medium',
                    'recommendations': ['Quality evaluation used default scoring'],
                    'meets_threshold': True
                }
        
    except ImportError as e2:
        print(f"❌ Could not import individual agents: {e2}")
        FULL_AGENTS_AVAILABLE = False

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
if FULL_AGENTS_AVAILABLE:
    try:
        if 'RecipeAgentTeam' in globals():
            # Use the main orchestrator if available
            recipe_team = RecipeAgentTeam()
            print("🤖 Full Recipe Agent Team initialized")
        else:
            # Use the simple orchestrator with individual agents
            recipe_team = SimpleRecipeTeam()
            print("🤖 Simple Recipe Team initialized")
    except Exception as e:
        print(f"⚠️ Failed to initialize agent team: {e}")
        FULL_AGENTS_AVAILABLE = False

if not FULL_AGENTS_AVAILABLE:
    # Ultimate fallback - Claude-only recipe generation
    print("🔄 Initializing Claude-only fallback system...")
    
    class FallbackRecipeTeam:
        def __init__(self):
            print("🔄 Initializing fallback recipe system...")
            
        def generate_recipe(self, user_request):
            """Fallback recipe generation using only Claude API"""
            try:
                from anthropic import Anthropic
                
                client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
                
                prompt = f"""Create a detailed recipe for: {user_request}

Return a complete recipe with this exact structure:

Title: [Recipe Name]
Description: [Brief description]
Prep Time: [X minutes]
Cook Time: [X minutes]
Servings: [X]
Difficulty: [Easy/Medium/Hard]

Ingredients:
- [ingredient 1 with measurements]
- [ingredient 2 with measurements]
- [etc...]

Instructions:
1. [Step 1]
2. [Step 2]
3. [etc...]

Tags: [tag1, tag2, tag3]
Cuisine: [cuisine type]
Meal Type: [breakfast/lunch/dinner/snack/dessert]"""

                response = client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=2000,
                    messages=[{"role": "user", "content": prompt}]
                )
                
                recipe_text = response.content[0].text.strip()
                
                # Parse the response into structured data
                recipe_data = self._parse_recipe_text(recipe_text, user_request)
                
                return {
                    'success': True,
                    'recipe': recipe_data,
                    'nutrition': {
                        'nutrition_per_serving': {
                            'calories': 'Estimated',
                            'protein': 'N/A',
                            'carbs': 'N/A',
                            'fat': 'N/A'
                        },
                        'health_insights': ['Basic recipe generated - nutrition analysis unavailable']
                    },
                    'quality': {
                        'score': 7.0,
                        'quality_level': 'Good',
                        'confidence': 'medium'
                    },
                    'iterations': 1,
                    'process_log': ['Recipe generated using fallback system']
                }
                
            except Exception as e:
                return {
                    'success': False,
                    'error': f"Fallback recipe generation failed: {str(e)}",
                    'process_log': [f"Error: {str(e)}"]
                }
        
        def _parse_recipe_text(self, text, original_request):
            """Parse the Claude response into structured recipe data"""
            import re
            
            # Extract sections using regex
            title_match = re.search(r'Title:\s*(.+)', text)
            desc_match = re.search(r'Description:\s*(.+)', text)
            prep_match = re.search(r'Prep Time:\s*(.+)', text)
            cook_match = re.search(r'Cook Time:\s*(.+)', text)
            servings_match = re.search(r'Servings:\s*(.+)', text)
            difficulty_match = re.search(r'Difficulty:\s*(.+)', text)
            
            # Extract ingredients (lines starting with -)
            ingredients = re.findall(r'^\s*-\s*(.+)', text, re.MULTILINE)
            
            # Extract instructions (numbered lines)
            instructions = re.findall(r'^\s*\d+\.\s*(.+)', text, re.MULTILINE)
            
            # Extract tags
            tags_match = re.search(r'Tags:\s*(.+)', text)
            tags = []
            if tags_match:
                tags = [tag.strip() for tag in tags_match.group(1).split(',')]
            
            cuisine_match = re.search(r'Cuisine:\s*(.+)', text)
            meal_match = re.search(r'Meal Type:\s*(.+)', text)
            
            return {
                'title': title_match.group(1).strip() if title_match else f"Recipe for {original_request}",
                'description': desc_match.group(1).strip() if desc_match else "A delicious recipe",
                'prep_time': prep_match.group(1).strip() if prep_match else "Unknown",
                'cook_time': cook_match.group(1).strip() if cook_match else "Unknown",
                'total_time': "Unknown",
                'servings': servings_match.group(1).strip() if servings_match else "4",
                'difficulty': difficulty_match.group(1).strip() if difficulty_match else "Medium",
                'ingredients': ingredients if ingredients else ["Ingredients not parsed"],
                'instructions': instructions if instructions else ["Instructions not parsed"],
                'tags': tags if tags else ["recipe"],
                'cuisine_type': cuisine_match.group(1).strip() if cuisine_match else "Unknown",
                'meal_type': meal_match.group(1).strip() if meal_match else "Unknown",
                'enhanced': False,
                'enhancements_made': [],
                'chef_notes': [],
                'success': True,
                'agent': "fallback_generator",
                'original_request': original_request
            }
    
    recipe_team = FallbackRecipeTeam()
    print("🔄 Fallback recipe system ready")

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

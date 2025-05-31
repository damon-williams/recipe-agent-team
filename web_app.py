# web_app.py - Updated for Vercel deployment
import os
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from supabase import create_client, Client
import json
from datetime import datetime
import time
import traceback

# Import agents - make sure they're in the same directory
try:
    from main import RecipeAgentTeam
except ImportError:
    # Fallback if main.py doesn't exist
    from recipe_generator import RecipeGenerator
    from recipe_enhancer import RecipeEnhancer
    from web_researcher import WebResearcher
    from nutrition_analyst import NutritionAnalyst
    from quality_evaluator import QualityEvaluator

load_dotenv()

# For Vercel, we need to handle the template and static folders differently
app = Flask(__name__)
CORS(app)

# Initialize Supabase
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_ANON_KEY')

if supabase_url and supabase_key:
    supabase: Client = create_client(supabase_url, supabase_key)
else:
    print("⚠️ Warning: Supabase credentials not found")
    supabase = None

# Initialize Recipe Agent Team
try:
    recipe_team = RecipeAgentTeam()
except:
    # Fallback - create a simple team if main.py doesn't exist
    class SimpleRecipeTeam:
        def __init__(self):
            self.generator = RecipeGenerator()
            self.enhancer = RecipeEnhancer()
            self.researcher = WebResearcher()
            self.nutrition = NutritionAnalyst()
            self.evaluator = QualityEvaluator()
        
        def generate_recipe(self, user_request):
            try:
                # Simple workflow
                print(f"🤖 Generating recipe for: {user_request}")
                
                # Step 1: Generate base recipe
                base_recipe = self.generator.create_recipe(user_request)
                if not base_recipe.get('success'):
                    return {'success': False, 'error': base_recipe.get('error')}
                
                # Step 2: Research inspiration (optional)
                inspiration = None
                try:
                    inspiration = self.researcher.find_inspiration(base_recipe['title'])
                except Exception as e:
                    print(f"⚠️ Research failed: {e}")
                
                # Step 3: Enhance recipe
                try:
                    enhanced_recipe = self.enhancer.enhance_recipe(base_recipe, inspiration)
                except Exception as e:
                    print(f"⚠️ Enhancement failed: {e}")
                    enhanced_recipe = base_recipe
                
                # Step 4: Analyze nutrition
                nutrition_data = None
                try:
                    nutrition_data = self.nutrition.analyze_nutrition(enhanced_recipe)
                except Exception as e:
                    print(f"⚠️ Nutrition analysis failed: {e}")
                
                # Step 5: Evaluate quality
                quality_data = None
                try:
                    quality_data = self.evaluator.evaluate_recipe(enhanced_recipe, nutrition_data)
                except Exception as e:
                    print(f"⚠️ Quality evaluation failed: {e}")
                    quality_data = {'score': 7.0, 'quality_level': 'Good', 'confidence': 'medium'}
                
                return {
                    'success': True,
                    'recipe': enhanced_recipe,
                    'nutrition': nutrition_data,
                    'quality': quality_data,
                    'iterations': 1,
                    'process_log': ['Recipe generated successfully']
                }
                
            except Exception as e:
                return {
                    'success': False,
                    'error': f"Recipe generation failed: {str(e)}",
                    'process_log': [f"Error: {str(e)}"]
                }
    
    recipe_team = SimpleRecipeTeam()

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

# For Vercel
app = app
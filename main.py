# main.py - Orchestrator (Future Backend API)
import os
from dotenv import load_dotenv
from agents.recipe_generator import RecipeGenerator
from agents.recipe_enhancer import RecipeEnhancer
from agents.web_researcher import WebResearcher
from agents.nutrition_analyst import NutritionAnalyst
from agents.quality_evaluator import QualityEvaluator
import json
from datetime import datetime

load_dotenv()

class RecipeAgentTeam:
    def __init__(self):
        # Initialize all agents
        self.recipe_generator = RecipeGenerator()
        self.recipe_enhancer = RecipeEnhancer()
        self.web_researcher = WebResearcher()
        self.nutrition_analyst = NutritionAnalyst()
        self.quality_evaluator = QualityEvaluator()
        
        self.max_iterations = 3
        self.quality_threshold = 7.0
    
    def generate_recipe(self, user_request: str) -> dict:
        """
        Main orchestration method - returns structured data for web API
        """
        
        # Track the process for web display
        process_log = []
        
        try:
            # Step 1: Generate basic recipe
            process_log.append({"step": "generating", "status": "in_progress"})
            basic_recipe = self.recipe_generator.create_recipe(user_request)
            process_log.append({"step": "generating", "status": "completed"})
            
            # Step 2: Research for inspiration
            process_log.append({"step": "researching", "status": "in_progress"})
            inspiration = self.web_researcher.find_inspiration(basic_recipe["title"])
            process_log.append({"step": "researching", "status": "completed"})
            
            # Step 3: Enhancement loop
            current_recipe = basic_recipe
            iteration = 0
            
            while iteration < self.max_iterations:
                iteration += 1
                process_log.append({"step": f"enhancing_iteration_{iteration}", "status": "in_progress"})
                
                # Enhance recipe
                enhanced_recipe = self.recipe_enhancer.enhance_recipe(
                    current_recipe, inspiration
                )
                
                # Analyze nutrition
                nutrition_info = self.nutrition_analyst.analyze_nutrition(enhanced_recipe)
                
                # Evaluate quality
                quality_result = self.quality_evaluator.evaluate_recipe(
                    enhanced_recipe, nutrition_info
                )
                
                process_log.append({
                    "step": f"enhancing_iteration_{iteration}", 
                    "status": "completed",
                    "quality_score": quality_result["score"]
                })
                
                current_recipe = enhanced_recipe
                
                # Check if we're satisfied
                if quality_result["score"] >= self.quality_threshold:
                    break
            
            # Final result - structured for web API
            result = {
                "success": True,
                "recipe": current_recipe,
                "nutrition": nutrition_info,
                "quality": quality_result,
                "inspiration_sources": inspiration,
                "process_log": process_log,
                "iterations": iteration,
                "timestamp": datetime.now().isoformat(),
                "original_request": user_request
            }
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "process_log": process_log,
                "timestamp": datetime.now().isoformat()
            }
    
    def get_recipe_status(self, recipe_id: str) -> dict:
        """For future async processing"""
        # Placeholder for tracking long-running recipe generation
        pass

# CLI Interface (current)
def main():
    print("🍳 Recipe Agent Team - CLI Interface")
    print("="*50)
    
    team = RecipeAgentTeam()
    
    while True:
        user_input = input("\nWhat recipe would you like to create? (or 'quit'): ")
        if user_input.lower() == 'quit':
            break
            
        print(f"\n🤖 Generating recipe for: {user_input}")
        print("This may take a moment...")
        
        result = team.generate_recipe(user_input)
        
        if result["success"]:
            print("\n" + "="*50)
            print("✅ RECIPE GENERATED SUCCESSFULLY!")
            print("="*50)
            
            recipe = result["recipe"]
            print(f"\n📝 {recipe['title']}")
            print(f"⏱️  Prep: {recipe.get('prep_time', 'N/A')} | Cook: {recipe.get('cook_time', 'N/A')}")
            print(f"👥 Serves: {recipe.get('servings', 'N/A')}")
            
            print(f"\n🥘 Ingredients:")
            for ingredient in recipe.get('ingredients', []):
                print(f"  • {ingredient}")
            
            print(f"\n👨‍🍳 Instructions:")
            for i, instruction in enumerate(recipe.get('instructions', []), 1):
                print(f"  {i}. {instruction}")
            
            if result.get("nutrition"):
                nutrition_data = result["nutrition"]
                nutrition_per_serving = nutrition_data.get("nutrition_per_serving", {})
                print(f"\n📊 Nutrition (per serving):")
                print(f"  Calories: {nutrition_per_serving.get('calories', 'N/A')}")
                print(f"  Protein: {nutrition_per_serving.get('protein', 'N/A')}g")
                print(f"  Carbs: {nutrition_per_serving.get('carbs', 'N/A')}g")
                print(f"  Fat: {nutrition_per_serving.get('fat', 'N/A')}g")
                
                # Add more nutrition details if available
                if nutrition_per_serving.get('fiber'):
                    print(f"  Fiber: {nutrition_per_serving.get('fiber', 'N/A')}g")
                if nutrition_per_serving.get('sodium'):
                    print(f"  Sodium: {nutrition_per_serving.get('sodium', 'N/A')}mg")
                
                # Show nutrition score and insights
                if nutrition_data.get('nutrition_score'):
                    print(f"  Nutrition Score: {nutrition_data.get('nutrition_score', 'N/A')}/10")
                
                # Show top health insights
                health_insights = nutrition_data.get('health_insights', [])
                if health_insights:
                    print(f"\n💡 Health Insights:")
                    for insight in health_insights[:2]:  # Show top 2 insights
                        print(f"  • {insight}")
            
            print(f"\n⭐ Quality Score: {result['quality']['score']}/10")
            print(f"🔄 Iterations: {result['iterations']}")
            
        else:
            print(f"\n❌ Error: {result['error']}")

# Future Web API (commented out for now)
"""
# web_app.py - Future Flask/FastAPI implementation

from flask import Flask, request, jsonify
from main import RecipeAgentTeam

app = Flask(__name__)
team = RecipeAgentTeam()

@app.route('/api/generate-recipe', methods=['POST'])
def api_generate_recipe():
    data = request.get_json()
    user_request = data.get('recipe_request', '')
    
    result = team.generate_recipe(user_request)
    return jsonify(result)

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "recipe-agent-team"})

if __name__ == '__main__':
    app.run(debug=True)
"""

if __name__ == "__main__":
    main()
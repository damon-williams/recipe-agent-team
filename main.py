# main.py - Recipe Agent Team Orchestrator
import os
import time
from typing import Dict, List
import traceback

# Import all agents
from recipe_generator import RecipeGenerator
from recipe_enhancer import RecipeEnhancer
from web_researcher import WebResearcher
from nutrition_analyst import NutritionAnalyst
from quality_evaluator import QualityEvaluator

class RecipeAgentTeam:
    def __init__(self):
        """Initialize all AI agents for recipe generation pipeline"""
        
        print("🚀 Initializing Recipe Agent Team...")
        
        # Initialize all agents
        self.generator = RecipeGenerator()
        self.enhancer = RecipeEnhancer()
        self.researcher = WebResearcher()
        self.nutrition_analyst = NutritionAnalyst()
        self.quality_evaluator = QualityEvaluator()
        
        # Pipeline configuration
        self.max_iterations = 2
        self.quality_threshold = 6.0
        self.timeout_seconds = 45
        
        print("✅ All agents initialized successfully!")
    
    def generate_recipe(self, user_request: str) -> Dict:
        """
        Main recipe generation pipeline using all AI agents
        """
        
        start_time = time.time()
        process_log = []
        
        try:
            print(f"\n🎯 Starting recipe generation for: '{user_request}'")
            process_log.append(f"🎯 Request: {user_request}")
            
            # Step 1: Generate base recipe
            process_log.append("🤖 Recipe Generator: Creating base recipe...")
            print("🤖 Step 1: Generating base recipe...")
            
            base_recipe = self.generator.create_recipe(user_request)
            
            if not base_recipe.get('success'):
                return {
                    'success': False,
                    'error': base_recipe.get('error', 'Recipe generation failed'),
                    'process_log': process_log
                }
            
            process_log.append(f"✅ Generated: {base_recipe.get('title', 'Unknown Recipe')}")
            
            # Step 2: Research cooking inspiration
            inspiration_data = None
            if time.time() - start_time < self.timeout_seconds - 30:  # Time check
                try:
                    process_log.append("🔍 Web Researcher: Finding cooking inspiration...")
                    print("🔍 Step 2: Researching cooking inspiration...")
                    
                    inspiration_data = self.researcher.find_inspiration(
                        base_recipe.get('title', ''), 
                        base_recipe.get('meal_type')
                    )
                    
                    sources_found = inspiration_data.get('sources_analyzed', 0)
                    process_log.append(f"✅ Found inspiration from {sources_found} sources")
                    
                except Exception as e:
                    print(f"⚠️ Research failed: {str(e)}")
                    process_log.append(f"⚠️ Research failed - using fallback inspiration")
                    inspiration_data = None
            else:
                process_log.append("⏰ Skipping research due to time constraints")
            
            # Step 3: Enhance the recipe
            enhanced_recipe = base_recipe
            if time.time() - start_time < self.timeout_seconds - 20:  # Time check
                try:
                    process_log.append("📝 Recipe Enhancer: Adding creative improvements...")
                    print("📝 Step 3: Enhancing recipe...")
                    
                    enhanced_recipe = self.enhancer.enhance_recipe(base_recipe, inspiration_data)
                    
                    enhancements = enhanced_recipe.get('enhancements_made', [])
                    if enhancements:
                        process_log.append(f"✅ Applied {len(enhancements)} enhancements")
                    else:
                        process_log.append("✅ Recipe enhanced successfully")
                    
                except Exception as e:
                    print(f"⚠️ Enhancement failed: {str(e)}")
                    process_log.append(f"⚠️ Enhancement failed - using base recipe")
                    enhanced_recipe = base_recipe
            else:
                process_log.append("⏰ Skipping enhancement due to time constraints")
            
            # Step 4: Analyze nutrition
            nutrition_data = None
            if time.time() - start_time < self.timeout_seconds - 15:  # Time check
                try:
                    process_log.append("🥗 Nutrition Analyst: Calculating health metrics...")
                    print("🥗 Step 4: Analyzing nutrition...")
                    
                    nutrition_data = self.nutrition_analyst.analyze_nutrition(enhanced_recipe)
                    
                    if nutrition_data and nutrition_data.get('nutrition_per_serving'):
                        calories = nutrition_data['nutrition_per_serving'].get('calories', 'N/A')
                        process_log.append(f"✅ Nutrition analyzed: ~{calories} calories/serving")
                    else:
                        process_log.append("✅ Basic nutrition estimates provided")
                    
                except Exception as e:
                    print(f"⚠️ Nutrition analysis failed: {str(e)}")
                    process_log.append(f"⚠️ Nutrition analysis failed - using estimates")
                    nutrition_data = self._create_fallback_nutrition(enhanced_recipe)
            else:
                process_log.append("⏰ Skipping nutrition analysis due to time constraints")
                nutrition_data = self._create_fallback_nutrition(enhanced_recipe)
            
            # Step 5: Evaluate quality
            quality_data = None
            if time.time() - start_time < self.timeout_seconds - 5:  # Time check
                try:
                    process_log.append("⭐ Quality Evaluator: Scoring recipe quality...")
                    print("⭐ Step 5: Evaluating quality...")
                    
                    quality_data = self.quality_evaluator.evaluate_recipe(
                        enhanced_recipe, 
                        nutrition_data, 
                        inspiration_data
                    )
                    
                    score = quality_data.get('score', 0)
                    quality_level = quality_data.get('quality_level', 'Unknown')
                    process_log.append(f"✅ Quality Score: {score}/10 ({quality_level})")
                    
                except Exception as e:
                    print(f"⚠️ Quality evaluation failed: {str(e)}")
                    process_log.append(f"⚠️ Quality evaluation failed - using default score")
                    quality_data = self._create_fallback_quality()
            else:
                process_log.append("⏰ Using default quality score due to time constraints")
                quality_data = self._create_fallback_quality()
            
            # Final result
            total_time = int(time.time() - start_time)
            process_log.append(f"🎉 Recipe generation complete in {total_time}s!")
            
            print(f"🎉 Recipe generation complete!")
            print(f"   Title: {enhanced_recipe.get('title', 'Unknown')}")
            print(f"   Quality: {quality_data.get('score', 'N/A')}/10")
            print(f"   Time: {total_time}s")
            
            return {
                'success': True,
                'recipe': enhanced_recipe,
                'nutrition': nutrition_data,
                'quality': quality_data,
                'iterations': 1,
                'process_log': process_log,
                'generation_time': total_time,
                'inspiration_used': inspiration_data is not None
            }
            
        except Exception as e:
            error_msg = f"Pipeline failed: {str(e)}"
            print(f"❌ {error_msg}")
            traceback.print_exc()
            
            process_log.append(f"❌ {error_msg}")
            
            return {
                'success': False,
                'error': error_msg,
                'process_log': process_log,
                'generation_time': int(time.time() - start_time)
            }
    
    def _create_fallback_nutrition(self, recipe: Dict) -> Dict:
        """Create basic nutrition estimates when analysis fails"""
        
        meal_type = recipe.get('meal_type', 'dinner').lower()
        
        base_estimates = {
            'breakfast': {'calories': 350, 'protein': 15, 'carbs': 45, 'fat': 12},
            'lunch': {'calories': 450, 'protein': 20, 'carbs': 50, 'fat': 15},
            'dinner': {'calories': 550, 'protein': 25, 'carbs': 55, 'fat': 18},
            'snack': {'calories': 200, 'protein': 8, 'carbs': 25, 'fat': 8},
            'dessert': {'calories': 300, 'protein': 5, 'carbs': 45, 'fat': 12}
        }
        
        estimate = base_estimates.get(meal_type, base_estimates['dinner']).copy()
        estimate.update({
            'fiber': 4,
            'sugar': 8,
            'sodium': 400
        })
        
        return {
            'nutrition_per_serving': estimate,
            'health_insights': ["Nutrition estimates provided"],
            'analysis_method': 'fallback_estimate',
            'confidence': 'low',
            'servings_analyzed': self._parse_servings(recipe.get('servings', '4')),
            'dietary_tags': ['estimated'],
            'nutrition_score': 5.0,
            'recommendations': ["Use nutrition tracking apps for accurate analysis"]
        }
    
    def _create_fallback_quality(self) -> Dict:
        """Create basic quality score when evaluation fails"""
        
        return {
            'score': 7.0,
            'quality_verdict': 'good',
            'quality_level': 'Good',
            'confidence': 'medium',
            'detailed_scores': {
                'creativity': {'score': 7.0, 'confidence': 'medium'},
                'practicality': {'score': 7.5, 'confidence': 'medium'},
                'nutrition': {'score': 6.5, 'confidence': 'low'},
                'completeness': {'score': 7.5, 'confidence': 'high'}
            },
            'recommendations': ['Quality evaluation used default scoring'],
            'meets_threshold': True,
            'evaluation_timestamp': self._get_timestamp()
        }
    
    def _parse_servings(self, servings_str: str) -> int:
        """Parse servings string to get number"""
        import re
        try:
            numbers = re.findall(r'\d+', str(servings_str))
            return int(numbers[0]) if numbers else 4
        except:
            return 4
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()

# Test the full system
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    # Test the full pipeline
    team = RecipeAgentTeam()
    
    test_request = "healthy chicken stir fry"
    print(f"\n🧪 Testing full pipeline with: '{test_request}'")
    
    result = team.generate_recipe(test_request)
    
    print(f"\n📊 Pipeline Results:")
    print(f"Success: {result.get('success')}")
    print(f"Recipe: {result.get('recipe', {}).get('title', 'N/A')}")
    print(f"Quality: {result.get('quality', {}).get('score', 'N/A')}/10")
    print(f"Time: {result.get('generation_time', 'N/A')}s")
    print(f"Inspiration Used: {result.get('inspiration_used', False)}")
    
    if result.get('process_log'):
        print(f"\n📋 Process Log:")
        for log_entry in result['process_log']:
            print(f"  {log_entry}")
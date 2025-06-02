# agents/nutrition_analyst.py - Complete Edamam API Integration
import os
import requests
from anthropic import Anthropic
from typing import Dict, List, Optional
import json
import re
from dataclasses import dataclass
import math

@dataclass
class NutritionData:
    calories: float
    protein: float  # grams
    carbs: float   # grams
    fat: float     # grams
    fiber: float   # grams
    sugar: float   # grams
    sodium: float  # mg
    confidence: str = "medium"  # low, medium, high

class NutritionAnalyst:
    def __init__(self):
        self.client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        self.model = "claude-sonnet-4-20250514"
        
        # Edamam Nutrition API setup
        self.edamam_app_id = os.getenv('EDAMAM_APP_ID')
        self.edamam_app_key = os.getenv('EDAMAM_APP_KEY')
        
        # Try both endpoints - Recipe Analysis is more forgiving
        self.edamam_nutrition_url = "https://api.edamam.com/api/nutrition-details"
        self.edamam_recipe_url = "https://api.edamam.com/api/recipes/v2/analyze"
        
        # Check if Edamam API is available
        self.has_edamam_api = bool(self.edamam_app_id and self.edamam_app_key)
        # if self.has_edamam_api:
        #     print("✅ Edamam Nutrition API initialized")
        # else:
        #     print("⚠️  No Edamam API credentials - using AI-powered analysis")
        
        # Load basic nutrition database for fallback
        self.ingredient_nutrition_db = self._load_basic_nutrition_db()
    
    def analyze_nutrition(self, recipe: Dict) -> Dict:
        """
        Analyze nutritional content of a recipe using AI-powered estimation as primary method
        """
        
        print(f"🥗 Analyzing nutrition for: {recipe.get('title', 'Unknown Recipe')}")
        
        try:
            ingredients = recipe.get('ingredients', [])
            servings = self._parse_servings(recipe.get('servings', '4'))
            
            nutrition_data = None
            
            # Approach 1: Use AI-powered nutrition estimation (PRIMARY METHOD)
            print("🤖 Using AI-powered nutrition estimation...")
            nutrition_data = self._analyze_with_ai_enhanced(recipe)
            
            # Approach 2: Try Edamam Nutrition API (disabled for now)
            # if not nutrition_data and self.has_edamam_api:
            #     nutrition_data = self._analyze_with_edamam(ingredients, servings)
            
            # Approach 3: Use built-in ingredient database (fallback)
            if not nutrition_data:
                nutrition_data = self._analyze_with_database(ingredients, servings)
            
            # Approach 4: Basic estimation (final fallback)
            if not nutrition_data:
                nutrition_data = self._create_basic_nutrition_estimate(recipe)
            
            # Calculate additional metrics
            enhanced_nutrition = self._calculate_nutrition_metrics(nutrition_data, recipe)
            
            # Generate health insights
            health_insights = self._generate_health_insights_enhanced(enhanced_nutrition, recipe)
            
            return {
                'nutrition_per_serving': enhanced_nutrition,
                'health_insights': health_insights,
                'analysis_method': nutrition_data.get('method', 'ai_estimation'),
                'confidence': nutrition_data.get('confidence', 'medium'),
                'servings_analyzed': servings,
                'dietary_tags': self._generate_dietary_tags(enhanced_nutrition),
                'nutrition_score': self._calculate_nutrition_score(enhanced_nutrition),
                'recommendations': self._generate_recommendations(enhanced_nutrition, recipe),
                'api_used': False  # Always false now since we're using AI
            }
            
        except Exception as e:
            print(f"⚠️  Nutrition analysis failed: {str(e)}")
            return self._create_fallback_nutrition(recipe)
    
    def _analyze_with_ai_enhanced(self, recipe: Dict) -> Dict:
        """Enhanced AI nutrition analysis with detailed consideration"""
        
        print("  🤖 Using enhanced AI nutrition estimation...")
        
        # Prepare comprehensive recipe data for AI analysis
        recipe_context = {
            'title': recipe.get('title', 'Unknown'),
            'servings': recipe.get('servings', '4'),
            'ingredients': recipe.get('ingredients', []),
            'cooking_methods': self._extract_cooking_methods(recipe.get('instructions', [])),
            'meal_type': recipe.get('meal_type', 'unknown'),
            'cuisine_type': recipe.get('cuisine_type', 'unknown')
        }
        
        nutrition_prompt = f"""
Analyze the nutritional content of this recipe and provide detailed estimates per serving:

RECIPE ANALYSIS:
Title: {recipe_context['title']}
Servings: {recipe_context['servings']}
Meal Type: {recipe_context['meal_type']}
Cooking Methods: {', '.join(recipe_context['cooking_methods']) if recipe_context['cooking_methods'] else 'Various'}

INGREDIENTS TO ANALYZE:
{self._format_ingredients_for_analysis(recipe_context['ingredients'])}

Please provide comprehensive nutritional estimates considering:
1. Raw ingredient nutritional values
2. Cooking method impacts (oil absorption, water loss, etc.)
3. Realistic portion sizes per serving
4. Added fats, oils, and seasonings during cooking
5. Bioavailability changes from cooking processes

Provide estimates in this JSON format:
{{
    "calories": number (realistic total per serving),
    "protein": number (grams per serving),
    "carbs": number (grams per serving), 
    "fat": number (grams per serving),
    "fiber": number (grams per serving),
    "sugar": number (grams per serving),
    "sodium": number (mg per serving),
    "confidence": "high/medium/low",
    "method": "ai_enhanced_estimation",
    "analysis_notes": [
        "Key factors considered in estimation",
        "Cooking method impacts",
        "Major calorie contributors"
    ]
}}

Be realistic and consider:
- Cooking oils and fats added during preparation
- Water content changes from cooking
- Actual edible portions (bones, peels removed)
- Reasonable serving sizes for the meal type

Provide your best professional estimation based on culinary and nutritional knowledge.
"""
        
        try:
            print(f"  🤖 Sending detailed nutrition analysis to Claude...")
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1200,
                messages=[{"role": "user", "content": nutrition_prompt}]
            )
            
            nutrition_text = response.content[0].text.strip()
            print(f"  🤖 Claude nutrition response length: {len(nutrition_text)} characters")
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', nutrition_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                
                # Validate and clean the results
                result = self._validate_ai_nutrition_result(result)
                
                print(f"  ✅ AI nutrition estimation complete")
                print(f"     Calories: {result.get('calories', 'N/A')} per serving")
                print(f"     Protein: {result.get('protein', 'N/A')}g per serving")
                print(f"     Confidence: {result.get('confidence', 'medium')}")
                
                return result
            else:
                print(f"  ❌ Could not extract JSON from AI response")
                return None
        
        except Exception as e:
            print(f"  ❌ AI nutrition estimation failed: {str(e)}")
            return None
    
    def _extract_cooking_methods(self, instructions: List[str]) -> List[str]:
        """Extract cooking methods from recipe instructions"""
        
        cooking_methods = set()
        
        method_keywords = {
            'sauté': ['sauté', 'sautee', 'pan fry'],
            'bake': ['bake', 'roast', 'oven'],
            'boil': ['boil', 'simmer', 'cook in water'],
            'grill': ['grill', 'bbq', 'barbecue'],
            'steam': ['steam'],
            'fry': ['fry', 'deep fry'],
            'braise': ['braise', 'slow cook'],
            'broil': ['broil'],
            'poach': ['poach'],
            'stir-fry': ['stir fry', 'stir-fry', 'wok']
        }
        
        instructions_text = ' '.join(instructions).lower()
        
        for method, keywords in method_keywords.items():
            if any(keyword in instructions_text for keyword in keywords):
                cooking_methods.add(method)
        
        return list(cooking_methods)
    
    def _format_ingredients_for_analysis(self, ingredients: List[str]) -> str:
        """Format ingredients list for AI analysis"""
        
        if not ingredients:
            return "No ingredients specified"
        
        formatted = []
        for i, ingredient in enumerate(ingredients[:20], 1):  # Limit to first 20 ingredients
            formatted.append(f"{i}. {ingredient}")
        
        if len(ingredients) > 20:
            formatted.append(f"... and {len(ingredients) - 20} more ingredients")
        
        return '\n'.join(formatted)
    
    def _validate_ai_nutrition_result(self, result: Dict) -> Dict:
        """Validate and clean AI nutrition estimation results"""
        
        # Ensure all required fields are present and reasonable
        validated = {
            'calories': max(0, min(result.get('calories', 400), 2000)),  # Cap at reasonable ranges
            'protein': max(0, min(result.get('protein', 15), 100)),
            'carbs': max(0, min(result.get('carbs', 30), 150)), 
            'fat': max(0, min(result.get('fat', 10), 80)),
            'fiber': max(0, min(result.get('fiber', 3), 20)),
            'sugar': max(0, min(result.get('sugar', 5), 50)),
            'sodium': max(0, min(result.get('sodium', 300), 3000)),
            'confidence': result.get('confidence', 'medium'),
            'method': result.get('method', 'ai_enhanced_estimation'),
            'analysis_notes': result.get('analysis_notes', [])
        }
        
        # Sanity check: calories should roughly match macronutrients
        calculated_calories = (validated['protein'] * 4) + (validated['carbs'] * 4) + (validated['fat'] * 9)
        if abs(validated['calories'] - calculated_calories) > validated['calories'] * 0.3:  # 30% tolerance
            print(f"  ⚠️ Calorie mismatch detected, adjusting...")
            # Adjust calories to match macronutrients more closely
            validated['calories'] = round((validated['calories'] + calculated_calories) / 2)
        
        return validated
    
    def _generate_health_insights_enhanced(self, nutrition: Dict, recipe: Dict) -> List[str]:
        """Generate enhanced health insights based on nutritional analysis"""
        
        insights = []
        
        calories = nutrition.get('calories', 0)
        protein = nutrition.get('protein', 0)
        fiber = nutrition.get('fiber', 0)
        sodium = nutrition.get('sodium', 0)
        fat = nutrition.get('fat', 0)
        carbs = nutrition.get('carbs', 0)
        
        # Meal-type specific calorie insights
        meal_type = recipe.get('meal_type', '').lower()
        if meal_type == 'breakfast' and calories < 300:
            insights.append("Light breakfast - great for weight management")
        elif meal_type == 'lunch' and 400 <= calories <= 600:
            insights.append("Well-balanced lunch portion")
        elif meal_type == 'dinner' and calories > 700:
            insights.append("Hearty dinner - consider portion control if needed")
        elif calories < 300:
            insights.append("Light meal - perfect for calorie-conscious eating")
        elif calories > 600:
            insights.append("Substantial meal - great for active individuals")
        
        # Protein insights
        if protein > 25:
            insights.append("High protein content - excellent for muscle maintenance")
        elif protein > 15:
            insights.append("Good protein source - supports daily protein needs")
        elif protein < 10:
            insights.append("Lower protein - consider adding protein-rich ingredients")
        
        # Fiber insights
        if fiber > 8:
            insights.append("High fiber content - supports digestive health")
        elif fiber > 5:
            insights.append("Good fiber source - aids in digestion")
        elif fiber < 3:
            insights.append("Low fiber - consider adding vegetables or whole grains")
        
        # Sodium insights
        if sodium > 1000:
            insights.append("Higher sodium content - balance with low-sodium foods")
        elif sodium > 600:
            insights.append("Moderate sodium levels - within reasonable range")
        elif sodium < 300:
            insights.append("Low sodium - heart-friendly option")
        
        # Analysis quality insights
        analysis_method = nutrition.get('method', '')
        confidence = nutrition.get('confidence', 'medium')
        
        if analysis_method == 'ai_enhanced_estimation' and confidence == 'high':
            insights.append("Nutrition calculated using advanced AI analysis")
        elif confidence == 'medium':
            insights.append("Nutrition estimates based on ingredient analysis")
        
        return insights[:4]  # Return top 4 most relevant insights
    
    def _analyze_with_edamam(self, ingredients: List[str], servings: int) -> Optional[Dict]:
        """Analyze nutrition using Edamam Nutrition API (KEPT FOR FUTURE USE)"""
        
        try:
            print("  🔬 Using Edamam Nutrition API...")
            
            # Prepare ingredient list for Edamam
            edamam_ingredients = []
            
            for ingredient in ingredients:
                # Clean and format ingredient for API
                cleaned = self._clean_ingredient_for_api(ingredient)
                if cleaned:
                    edamam_ingredients.append(cleaned)
            
            if not edamam_ingredients:
                print("  ⚠️  No valid ingredients for API")
                return None
            
            # Debug: show what we're sending
            print(f"  📋 Cleaned ingredients: {edamam_ingredients[:5]}...")
            
            # Try different approaches to get nutrition data
            
            # Approach 1: Try with all ingredients
            result = self._try_nutrition_details_api(edamam_ingredients, servings)
            if result:
                return result
            
            # Approach 2: Try with just main ingredients (remove seasonings/small items)
            main_ingredients = self._filter_main_ingredients(edamam_ingredients)
            if len(main_ingredients) != len(edamam_ingredients):
                print("  🔄 Trying with main ingredients only...")
                result = self._try_nutrition_details_api(main_ingredients, servings)
                if result:
                    return result
            
            # Approach 3: Try with simplified ingredient names
            simplified = self._simplify_ingredients(edamam_ingredients)
            if simplified != edamam_ingredients:
                print("  🔄 Trying with simplified ingredients...")
                result = self._try_nutrition_details_api(simplified, servings)
                if result:
                    return result
            
            print("  ❌ All Edamam approaches failed")
            return None
                
        except Exception as e:
            print(f"  ❌ Edamam API failed: {str(e)}")
            return None
    
    def _filter_main_ingredients(self, ingredients: List[str]) -> List[str]:
        """Keep only main ingredients, remove seasonings and small quantities"""
        
        main_ingredients = []
        skip_keywords = [
            'salt', 'pepper', 'garlic powder', 'onion powder', 
            'paprika', 'oregano', 'thyme', 'basil', 'parsley',
            'pinch', 'dash', 'sprinkle'
        ]
        
        for ingredient in ingredients:
            # Skip if it contains seasoning keywords
            if any(keyword in ingredient.lower() for keyword in skip_keywords):
                continue
            
            # Skip very small quantities (less than 1 tsp/tbsp without main ingredient)
            if ('tsp' in ingredient.lower() or 'teaspoon' in ingredient.lower()) and len(ingredient) < 20:
                continue
                
            main_ingredients.append(ingredient)
        
        return main_ingredients
    
    def _simplify_ingredients(self, ingredients: List[str]) -> List[str]:
        """Simplify ingredient names to improve API recognition"""
        
        simplified = []
        
        # Common substitutions that Edamam recognizes better
        substitutions = {
            'artisan sourdough': 'sourdough bread',
            'ciabatta bread': 'bread',
            'thick-cut deli ham': 'ham',
            'gruyère cheese': 'gruyere cheese',
            'yellow onion': 'onion',
            'arugula leaves': 'arugula',
            'extra virgin olive oil': 'olive oil',
            'kosher salt': 'salt',
            'sea salt': 'salt',
            'black pepper': 'pepper',
            'unsalted butter': 'butter'
        }
        
        for ingredient in ingredients:
            simplified_ingredient = ingredient.lower()
            
            # Apply substitutions
            for original, replacement in substitutions.items():
                if original in simplified_ingredient:
                    simplified_ingredient = simplified_ingredient.replace(original, replacement)
            
            # Clean up and capitalize properly
            simplified_ingredient = ' '.join(simplified_ingredient.split())
            simplified.append(simplified_ingredient)
        
        return simplified
    
    def _try_nutrition_details_api(self, ingredients: List[str], servings: int) -> Optional[Dict]:
        """Try the Nutrition Details API with better error handling"""
        
        try:
            recipe_data = {
                "title": "Recipe Analysis",
                "ingr": ingredients
            }
            
            params = {
                'app_id': self.edamam_app_id,
                'app_key': self.edamam_app_key
            }
            
            print(f"  📤 Nutrition API: {len(ingredients)} ingredients...")
            
            response = requests.post(
                self.edamam_nutrition_url,
                params=params,
                json=recipe_data,
                timeout=15
            )
            
            print(f"  📡 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Debug the response structure
                print(f"  📋 Response keys: {list(data.keys())}")
                
                # Check for nutrition data
                nutrition = data.get('totalNutrients', {})
                
                if nutrition:
                    calories = self._extract_nutrient_value(nutrition, 'ENERC_KCAL')
                    print(f"  📊 Total calories found: {calories}")
                    
                    if calories > 0:
                        result = self._parse_nutrition_data(nutrition, servings, 'edamam_nutrition_api')
                        print(f"  ✅ Nutrition API success - {result['calories']} cal/serving")
                        return result
                    else:
                        print(f"  ⚠️  Zero calories returned - ingredients not recognized")
                else:
                    print(f"  ⚠️  No totalNutrients in response")
                    
                    # Check if ingredients were parsed at all
                    if 'ingredients' in data:
                        parsed_ingredients = data['ingredients']
                        print(f"  📋 Parsed {len(parsed_ingredients)} ingredients")
                        for i, parsed in enumerate(parsed_ingredients[:3]):
                            print(f"    {i+1}. {parsed.get('text', 'Unknown')}")
                
                return None
            
            elif response.status_code == 422:
                print(f"  ⚠️  API couldn't parse ingredients (422)")
                try:
                    error_data = response.json()
                    if 'message' in error_data:
                        print(f"  📋 Error: {error_data['message']}")
                except:
                    pass
                return None
            else:
                print(f"  ❌ API error {response.status_code}")
                return None
                
        except Exception as e:
            print(f"  ❌ API exception: {str(e)}")
            return None
    
    def _parse_nutrition_data(self, nutrition: Dict, servings: int, method: str) -> Dict:
        """Parse nutrition data from Edamam response"""
        
        return {
            'calories': round(self._extract_nutrient_value(nutrition, 'ENERC_KCAL') / servings, 1),
            'protein': round(self._extract_nutrient_value(nutrition, 'PROCNT') / servings, 1),
            'carbs': round(self._extract_nutrient_value(nutrition, 'CHOCDF') / servings, 1),
            'fat': round(self._extract_nutrient_value(nutrition, 'FAT') / servings, 1),
            'fiber': round(self._extract_nutrient_value(nutrition, 'FIBTG') / servings, 1),
            'sugar': round(self._extract_nutrient_value(nutrition, 'SUGAR') / servings, 1),
            'sodium': round(self._extract_nutrient_value(nutrition, 'NA') / servings, 1),
            'method': method,
            'confidence': 'high'
        }
    
    def _clean_ingredient_for_api(self, ingredient: str) -> Optional[str]:
        """Clean ingredient text for Edamam API - keep measurements but remove cooking instructions"""
        
        # Start with the original ingredient
        cleaned = ingredient.strip()
        
        # Remove parenthetical notes 
        cleaned = re.sub(r'\([^)]*\)', '', cleaned)
        
        # Remove cooking method words but keep the core ingredient + measurement
        remove_words = [
            'finely chopped', 'roughly chopped', 'finely diced', 'roughly diced',
            'minced', 'sliced thin', 'sliced thick', 'thinly sliced', 'thickly sliced',
            'fresh', 'dried', 'ground', 'crushed', 'grated', 'shredded',
            'to taste', 'optional', 'for serving', 'for garnish', 'for decoration',
            'at room temperature', 'cold', 'warm', 'hot', 'chilled', 'frozen',
            'large', 'medium', 'small', 'extra large', 'jumbo'
        ]
        
        # Remove these words but preserve the structure
        for word in remove_words:
            cleaned = re.sub(r'\b' + re.escape(word) + r'\b', '', cleaned, flags=re.IGNORECASE)
        
        # Clean up punctuation and extra spaces
        cleaned = re.sub(r'[,;]', ' ', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned)
        cleaned = cleaned.strip()
        
        # Skip empty or very short results
        if len(cleaned) < 3:
            return None
        
        # Skip seasoning-only ingredients without measurements
        seasoning_only = ['salt', 'pepper', 'black pepper', 'white pepper', 'to taste']
        if any(cleaned.lower().strip() == seasoning for seasoning in seasoning_only):
            return None
        
        # Edamam works better with more natural language, so don't over-clean
        return cleaned[:100].strip()
    
    
    def _extract_nutrient_value(self, nutrients: Dict, nutrient_code: str) -> float:
        """Extract nutrient value from Edamam response"""
        
        nutrient = nutrients.get(nutrient_code, {})
        return nutrient.get('quantity', 0.0)
    
    def _analyze_with_database(self, ingredients: List[str], servings: int) -> Optional[Dict]:
        """Analyze nutrition using built-in ingredient database"""
        
        print("  📚 Using ingredient database...")
        
        total_nutrition = {
            'calories': 0,
            'protein': 0,
            'carbs': 0,
            'fat': 0,
            'fiber': 0,
            'sugar': 0,
            'sodium': 0
        }
        
        matched_ingredients = 0
        
        for ingredient in ingredients:
            # Parse ingredient to extract quantity and food item
            parsed = self._parse_ingredient(ingredient)
            
            # Look for matches in our database
            for db_food, nutrition in self.ingredient_nutrition_db.items():
                if db_food in parsed['food'].lower():
                    quantity_multiplier = parsed['quantity'] * 0.01  # Convert to reasonable portion
                    
                    for nutrient in total_nutrition:
                        total_nutrition[nutrient] += nutrition[nutrient] * quantity_multiplier
                    
                    matched_ingredients += 1
                    break
        
        if matched_ingredients > 0:
            # Calculate per serving
            for nutrient in total_nutrition:
                total_nutrition[nutrient] = round(total_nutrition[nutrient] / servings, 1)
            
            total_nutrition['method'] = 'ingredient_database'
            total_nutrition['confidence'] = 'medium' if matched_ingredients >= len(ingredients) * 0.6 else 'low'
            
            print(f"  ✅ Database matched {matched_ingredients}/{len(ingredients)} ingredients")
            return total_nutrition
        
        return None
    
    def _parse_ingredient(self, ingredient: str) -> Dict:
        """Parse ingredient string to extract quantity and food item"""
        
        ingredient_lower = ingredient.lower().strip()
        
        # Common quantity patterns
        quantity_patterns = [
            r'(\d+(?:\.\d+)?)\s*(?:lbs?|pounds?)',
            r'(\d+(?:\.\d+)?)\s*(?:cups?)',
            r'(\d+(?:\.\d+)?)\s*(?:tbsp|tablespoons?)',
            r'(\d+(?:\.\d+)?)\s*(?:tsp|teaspoons?)',
            r'(\d+(?:\.\d+)?)\s*(?:oz|ounces?)',
        ]
        
        quantity = 1.0  # default
        for pattern in quantity_patterns:
            match = re.search(pattern, ingredient_lower)
            if match:
                quantity = float(match.group(1))
                break
        
        # Extract the main food item (simplified)
        food_words = re.sub(r'\d+(?:\.\d+)?', '', ingredient_lower)
        food_words = re.sub(r'\b(?:cups?|tbsp|tsp|lbs?|pounds?|oz|ounces?|tablespoons?|teaspoons?)\b', '', food_words)
        food_words = re.sub(r'\b(?:diced|chopped|sliced|minced|fresh|dried|ground)\b', '', food_words)
        food_item = food_words.strip().strip(',')
        
        return {
            'quantity': quantity,
            'food': food_item,
            'original': ingredient
        }
    
    def _parse_servings(self, servings_str: str) -> int:
        """Parse servings string to get number"""
        try:
            numbers = re.findall(r'\d+', str(servings_str))
            return int(numbers[0]) if numbers else 4
        except:
            return 4
    
    def _analyze_with_ai(self, recipe: Dict) -> Dict:
        """Use AI to estimate nutrition when other methods fail (LEGACY METHOD)"""
        
        print("  🤖 Using AI estimation...")
        
        nutrition_prompt = f"""
Analyze the nutritional content of this recipe and provide estimates per serving:

RECIPE:
Title: {recipe.get('title', 'Unknown')}
Servings: {recipe.get('servings', '4')}
Ingredients: {json.dumps(recipe.get('ingredients', []), indent=2)}

Provide nutritional estimates in this JSON format:
{{
    "calories": number,
    "protein": number,
    "carbs": number,
    "fat": number,
    "fiber": number,
    "sugar": number,
    "sodium": number,
    "confidence": "medium",
    "method": "ai_estimation"
}}

Base estimates on typical nutritional values for similar dishes.
"""
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=800,
                messages=[{"role": "user", "content": nutrition_prompt}]
            )
            
            nutrition_text = response.content[0].text.strip()
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', nutrition_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                print(f"  ✅ AI nutrition estimation complete")
                return result
        
        except Exception as e:
            print(f"  ❌ AI nutrition estimation failed: {str(e)}")
        
        # Ultimate fallback
        return self._create_basic_nutrition_estimate(recipe)
    
    def _calculate_nutrition_metrics(self, base_nutrition: Dict, recipe: Dict) -> Dict:
        """Calculate additional nutrition metrics and ratios"""
        
        nutrition = base_nutrition.copy()
        
        # Calculate calories from macronutrients (for validation)
        calculated_calories = (
            nutrition.get('protein', 0) * 4 +  # 4 cal/g protein
            nutrition.get('carbs', 0) * 4 +    # 4 cal/g carbs  
            nutrition.get('fat', 0) * 9        # 9 cal/g fat
        )
        
        # Add calculated metrics
        nutrition['calories_from_macros'] = round(calculated_calories, 1)
        nutrition['protein_percentage'] = round((nutrition.get('protein', 0) * 4 / max(nutrition.get('calories', 1), 1)) * 100, 1)
        nutrition['carb_percentage'] = round((nutrition.get('carbs', 0) * 4 / max(nutrition.get('calories', 1), 1)) * 100, 1)
        nutrition['fat_percentage'] = round((nutrition.get('fat', 0) * 9 / max(nutrition.get('calories', 1), 1)) * 100, 1)
        
        return nutrition
    
    def _generate_health_insights(self, nutrition: Dict, recipe: Dict) -> List[str]:
        """Generate health insights based on nutritional analysis (LEGACY METHOD)"""
        
        insights = []
        
        calories = nutrition.get('calories', 0)
        protein = nutrition.get('protein', 0)
        fiber = nutrition.get('fiber', 0)
        sodium = nutrition.get('sodium', 0)
        
        # Calorie insights
        if calories < 300:
            insights.append("Light meal - great for weight management")
        elif calories > 600:
            insights.append("Hearty meal - consider portion control")
        
        # Protein insights
        if protein > 25:
            insights.append("High protein content - excellent for muscle maintenance")
        elif protein < 10:
            insights.append("Low protein - consider adding protein-rich ingredients")
        
        # Fiber insights
        if fiber > 8:
            insights.append("High fiber content - supports digestive health")
        elif fiber < 3:
            insights.append("Low fiber - consider adding vegetables or whole grains")
        
        # Sodium insights
        if sodium > 800:
            insights.append("High sodium content - monitor salt intake")
        elif sodium < 200:
            insights.append("Low sodium - heart-healthy option")
        
        return insights
    
    def _generate_dietary_tags(self, nutrition: Dict) -> List[str]:
        """Generate dietary tags based on nutrition profile"""
        
        tags = []
        
        calories = nutrition.get('calories', 0)
        protein = nutrition.get('protein', 0)
        carbs = nutrition.get('carbs', 0)
        
        # Calorie-based tags
        if calories < 300:
            tags.append('low-calorie')
        elif calories > 500:
            tags.append('high-calorie')
        
        # Macronutrient tags
        if protein > 20:
            tags.append('high-protein')
        if carbs < 20:
            tags.append('low-carb')
        
        return tags
    
    def _calculate_nutrition_score(self, nutrition: Dict) -> float:
        """Calculate overall nutrition score (0-10)"""
        
        score = 5.0  # Base score
        
        # Positive factors
        if nutrition.get('protein', 0) > 15:
            score += 1
        if nutrition.get('fiber', 0) > 5:
            score += 1
        if nutrition.get('sodium', 0) < 600:
            score += 1
        
        # Negative factors
        if nutrition.get('sodium', 0) > 1000:
            score -= 1
        if nutrition.get('calories', 0) > 700:
            score -= 0.5
        
        return max(0, min(10, round(score, 1)))
    
    def _generate_recommendations(self, nutrition: Dict, recipe: Dict) -> List[str]:
        """Generate recommendations for improving nutrition"""
        
        recommendations = []
        
        if nutrition.get('fiber', 0) < 5:
            recommendations.append("Add more vegetables or use whole grain alternatives")
        
        if nutrition.get('protein', 0) < 15:
            recommendations.append("Consider adding lean protein like chicken, fish, or legumes")
        
        if nutrition.get('sodium', 0) > 800:
            recommendations.append("Reduce salt and use herbs/spices for flavor instead")
        
        return recommendations
    
    def _load_basic_nutrition_db(self) -> Dict:
        """Load basic nutrition database for common ingredients"""
        
        # Simplified nutrition database (per 100g)
        return {
            'chicken breast': {'calories': 165, 'protein': 31, 'carbs': 0, 'fat': 3.6, 'fiber': 0, 'sugar': 0, 'sodium': 74},
            'ground beef': {'calories': 250, 'protein': 26, 'carbs': 0, 'fat': 15, 'fiber': 0, 'sugar': 0, 'sodium': 75},
            'pasta': {'calories': 131, 'protein': 5, 'carbs': 25, 'fat': 1.1, 'fiber': 1.8, 'sugar': 0.8, 'sodium': 1},
            'rice': {'calories': 130, 'protein': 2.7, 'carbs': 28, 'fat': 0.3, 'fiber': 0.4, 'sugar': 0.1, 'sodium': 1},
            'olive oil': {'calories': 884, 'protein': 0, 'carbs': 0, 'fat': 100, 'fiber': 0, 'sugar': 0, 'sodium': 2},
            'onion': {'calories': 40, 'protein': 1.1, 'carbs': 9.3, 'fat': 0.1, 'fiber': 1.7, 'sugar': 4.2, 'sodium': 4},
            'tomato': {'calories': 18, 'protein': 0.9, 'carbs': 3.9, 'fat': 0.2, 'fiber': 1.2, 'sugar': 2.6, 'sodium': 5}
        }
    
    def _create_basic_nutrition_estimate(self, recipe: Dict) -> Dict:
        """Create basic nutrition estimate when all else fails"""
        
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
            'sodium': 400,
            'method': 'basic_estimate',
            'confidence': 'low'
        })
        
        return estimate
    
    def _create_fallback_nutrition(self, recipe: Dict) -> Dict:
        """Create fallback nutrition data when analysis fails"""
        
        return {
            'nutrition_per_serving': self._create_basic_nutrition_estimate(recipe),
            'health_insights': ["Nutrition analysis unavailable - estimates provided"],
            'analysis_method': 'fallback',
            'confidence': 'low',
            'servings_analyzed': self._parse_servings(recipe.get('servings', '4')),
            'dietary_tags': ['estimated'],
            'nutrition_score': 5.0,
            'recommendations': ["Use nutrition tracking apps for accurate analysis"],
            'api_used': False,
            'error': "Nutrition analysis failed"
        }

# Test the nutrition analyst
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    # Test recipe
    test_recipe = {
        'title': 'Grilled Chicken with Rice',
        'servings': '4',
        'ingredients': [
            '1 lb chicken breast',
            '2 cups jasmine rice',
            '2 tbsp olive oil',
            '1 large onion, diced',
            '2 cloves garlic, minced',
            'Salt and pepper to taste'
        ],
        'meal_type': 'dinner'
    }
    
    analyst = NutritionAnalyst()
    
    print("Testing nutrition analysis...")
    nutrition_result = analyst.analyze_nutrition(test_recipe)
    
    if nutrition_result.get('nutrition_per_serving'):
        print("\n✅ Nutrition Analysis Complete!")
        nutrition = nutrition_result['nutrition_per_serving']
        print(f"Calories: {nutrition.get('calories', 'N/A')}")
        print(f"Protein: {nutrition.get('protein', 'N/A')}g")
        print(f"Method: {nutrition_result.get('analysis_method', 'unknown')}")
        print(f"Confidence: {nutrition_result.get('confidence', 'unknown')}")
        print(f"API Used: {nutrition_result.get('api_used', False)}")
        
        print(f"\n📊 Health Insights:")
        for insight in nutrition_result.get('health_insights', [])[:3]:
            print(f"  • {insight}")
    else:
        print("❌ Nutrition analysis failed")
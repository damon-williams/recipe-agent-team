# agents/recipe_generator.py
import os
from anthropic import Anthropic
from typing import Dict, List
import json
import re

class RecipeGenerator:
    def __init__(self):
        self.client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        self.model = "claude-sonnet-4-20250514"
        print("initiating RecipeGenerator with key: ", self.client.api_key)
    
    def create_recipe(self, user_request: str, complexity: str = "Medium") -> Dict:
        """
        Generate a recipe based on user request and complexity level
        Returns structured recipe data for web API compatibility
        """
        
        print(f"🤖 RecipeGenerator: Creating {complexity} complexity recipe for '{user_request}'")
        
        # Define complexity-specific guidance
        complexity_guidance = self._get_complexity_guidance(complexity)
        
        prompt = f"""
Create a recipe based on this request: "{user_request}"

COMPLEXITY LEVEL: {complexity}
{complexity_guidance}

Please provide a well-structured, practical recipe that matches the {complexity} complexity level.

Return your response in this EXACT JSON format:
{{
    "title": "Recipe Name",
    "description": "Brief description of the dish",
    "prep_time": "X minutes",
    "cook_time": "X minutes", 
    "total_time": "X minutes",
    "servings": "X",
    "difficulty": "{complexity}",
    "ingredients": [
        "ingredient 1 with measurements",
        "ingredient 2 with measurements"
    ],
    "instructions": [
        "Step 1 instruction",
        "Step 2 instruction"
    ],
    "tags": ["tag1", "tag2", "tag3"],
    "cuisine_type": "cuisine name",
    "meal_type": "breakfast/lunch/dinner/snack/dessert"
}}

Make sure the JSON is valid and complete. Include realistic measurements and clear instructions that match the {complexity} complexity level.
"""
        
        try:
            print(f"🤖 Sending prompt to Claude for {complexity} recipe...")
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            recipe_text = response.content[0].text.strip()
            print(f"🤖 Claude response length: {len(recipe_text)} characters")
            
            # Extract JSON from the response
            recipe_data = self._extract_json_from_response(recipe_text)
            
            # Validate and clean the recipe data
            validated_recipe = self._validate_recipe_data(recipe_data, user_request, complexity)
            
            print(f"✅ RecipeGenerator: Successfully created '{validated_recipe.get('title')}' at {complexity} complexity")
            
            return validated_recipe
            
        except Exception as e:
            print(f"❌ RecipeGenerator Error: {str(e)}")
            # Return error in structured format
            return {
                "error": f"Recipe generation failed: {str(e)}",
                "title": f"Failed Recipe for: {user_request}",
                "success": False
            }
    
    def _get_complexity_guidance(self, complexity: str) -> str:
        """Return specific guidance for each complexity level"""
        
        guidance = {
            "Easy": """
EASY COMPLEXITY GUIDELINES:
- Use common, easily available ingredients (found in most grocery stores)
- Limit to 8-10 ingredients maximum
- Use basic cooking techniques: sautéing, boiling, baking, grilling
- Keep prep time under 15 minutes, total time under 45 minutes
- Instructions should be clear and straightforward
- Avoid specialized equipment beyond basic pots, pans, and oven
- Focus on one-pot or sheet-pan meals when possible
- Include ingredient substitutions for accessibility""",
            
            "Medium": """
MEDIUM COMPLEXITY GUIDELINES:
- Mix of common and some specialty ingredients (1-2 unique items)
- 10-15 ingredients total
- Moderate techniques: braising, roasting, basic sauce-making
- Prep time 15-30 minutes, total time 45-90 minutes
- Some multi-step processes but well-organized
- May require basic kitchen tools (whisk, thermometer, etc.)
- Can include homemade components (simple sauces, seasonings)
- Balance of flavors and textures""",
            
            "High": """
HIGH COMPLEXITY GUIDELINES:
- Include premium, specialty, or hard-to-find ingredients
- 12-20+ ingredients for complex flavor profiles
- Advanced techniques: sous vide, confit, emulsification, reduction sauces
- Prep time 30+ minutes, total time 90+ minutes or multi-day preparation
- Multiple cooking methods and precise timing
- May require specialized equipment (stand mixer, food processor, etc.)
- Artisanal components (house-made stocks, cured elements, etc.)
- Restaurant-quality presentation and plating instructions
- Professional techniques and terminology"""
        }
        
        return guidance.get(complexity, guidance["Medium"])
    
    def _extract_json_from_response(self, response_text: str) -> Dict:
        """Extract JSON from Claude's response, handling various formats"""
        
        # Try to find JSON block
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            try:
                extracted = json.loads(json_str)
                print(f"🤖 Successfully extracted JSON with {len(extracted)} fields")
                return extracted
            except json.JSONDecodeError as e:
                print(f"⚠️ JSON decode error: {str(e)}")
                # If JSON is malformed, try to fix common issues
                return self._fix_malformed_json(json_str)
        
        # If no JSON found, try to parse the entire response
        try:
            return json.loads(response_text)
        except:
            print(f"❌ Could not extract valid JSON from response")
            raise Exception("Could not extract valid JSON from recipe response")
    
    def _fix_malformed_json(self, json_str: str) -> Dict:
        """Try to fix common JSON formatting issues"""
        
        print(f"🔧 Attempting to fix malformed JSON...")
        
        # Remove any trailing commas
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
        
        # Try parsing again
        try:
            fixed = json.loads(json_str)
            print(f"✅ Successfully fixed JSON")
            return fixed
        except:
            print(f"❌ Could not fix JSON formatting")
            raise Exception("Could not fix malformed JSON")
    
    def _validate_recipe_data(self, recipe_data: Dict, original_request: str, complexity: str) -> Dict:
        """Ensure recipe data has all required fields and is web-ready"""
        
        print(f"🔍 Validating recipe data for {complexity} complexity...")
        
        # Map backend complexity to frontend complexity for consistency
        frontend_complexity_mapping = {
            'Easy': 'Simple',
            'Medium': 'Medium', 
            'High': 'Gourmet'
        }
        frontend_complexity = frontend_complexity_mapping.get(complexity, complexity)
        
        # Required fields with defaults
        validated = {
            "title": recipe_data.get("title", f"Recipe for {original_request}"),
            "description": recipe_data.get("description", "A delicious recipe"),
            "prep_time": recipe_data.get("prep_time", "Unknown"),
            "cook_time": recipe_data.get("cook_time", "Unknown"),
            "total_time": recipe_data.get("total_time", "Unknown"),
            "servings": str(recipe_data.get("servings", "4")),
            "difficulty": frontend_complexity,  # Use frontend complexity for consistency
            "ingredients": recipe_data.get("ingredients", []),
            "instructions": recipe_data.get("instructions", []),
            "tags": recipe_data.get("tags", []),
            "cuisine_type": recipe_data.get("cuisine_type", "Unknown"),
            "meal_type": recipe_data.get("meal_type", "Unknown"),
            "success": True,
            "agent": "recipe_generator",
            "original_request": original_request,
            "requested_complexity": complexity,
            "frontend_complexity": frontend_complexity
        }
        
        # Clean and validate ingredients
        if not validated["ingredients"]:
            validated["ingredients"] = ["Ingredients need to be specified"]
            print(f"⚠️ No ingredients found, using placeholder")
        else:
            print(f"✅ Found {len(validated['ingredients'])} ingredients")
        
        # Clean and validate instructions
        if not validated["instructions"]:
            validated["instructions"] = ["Instructions need to be specified"]
            print(f"⚠️ No instructions found, using placeholder")
        else:
            print(f"✅ Found {len(validated['instructions'])} instruction steps")
        
        # Ensure we have at least some tags
        if not validated["tags"]:
            frontend_complexity_tag = frontend_complexity.lower()
            validated["tags"] = ["homemade", "recipe", frontend_complexity_tag]
            print(f"⚠️ No tags found, using defaults including '{frontend_complexity_tag}'")
        else:
            # Add complexity tag if not present
            frontend_complexity_tag = frontend_complexity.lower()
            if frontend_complexity_tag not in [tag.lower() for tag in validated["tags"]]:
                validated["tags"].append(frontend_complexity_tag)
            print(f"✅ Tags validated: {validated['tags']}")
        
        print(f"✅ Recipe validation complete for '{validated['title']}'")
        
        return validated
    
    def regenerate_recipe(self, original_recipe: Dict, feedback: str, complexity: str = None) -> Dict:
        """
        Regenerate a recipe based on feedback - useful for the enhancement loop
        """
        
        # Use original complexity if not specified
        if not complexity:
            complexity = original_recipe.get('requested_complexity', 'Medium')
        
        print(f"🔄 Regenerating recipe with {complexity} complexity based on feedback")
        
        complexity_guidance = self._get_complexity_guidance(complexity)
        
        prompt = f"""
Here's a recipe that needs improvement:

CURRENT RECIPE:
{json.dumps(original_recipe, indent=2)}

FEEDBACK FOR IMPROVEMENT:
{feedback}

COMPLEXITY LEVEL: {complexity}
{complexity_guidance}

Please create an improved version of this recipe addressing the feedback while maintaining the {complexity} complexity level.
Keep the same JSON structure but make the requested improvements.

Return the improved recipe in the same JSON format as before.
"""
        
        try:
            print(f"🔄 Sending regeneration request to Claude...")
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            recipe_text = response.content[0].text.strip()
            recipe_data = self._extract_json_from_response(recipe_text)
            validated_recipe = self._validate_recipe_data(
                recipe_data, 
                original_recipe.get("original_request", "improved recipe"),
                complexity
            )
            
            print(f"✅ Recipe regenerated successfully with {complexity} complexity")
            
            return validated_recipe
            
        except Exception as e:
            print(f"❌ Recipe regeneration failed: {str(e)}")
            # Return the original recipe with error note if regeneration fails
            original_recipe["regeneration_error"] = str(e)
            return original_recipe

# Test the agent directly (optional)
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    generator = RecipeGenerator()
    
    # Test with different complexity levels
    test_requests = [
        ("chicken tacos", "Simple"),
        ("pasta carbonara", "Medium"),
        ("beef wellington", "Gourmet")
    ]
    
    for request, complexity in test_requests:
        print(f"\n{'='*50}")
        print(f"Testing {complexity} complexity: {request}")
        print(f"{'='*50}")
        
        result = generator.create_recipe(request, complexity)
        
        if result.get("success"):
            print(f"\n✅ {complexity} Recipe Generated Successfully!")
            print(f"Title: {result['title']}")
            print(f"Difficulty: {result['difficulty']}")
            print(f"Prep Time: {result['prep_time']}")
            print(f"Ingredients: {len(result['ingredients'])} items")
            print(f"Instructions: {len(result['instructions'])} steps")
            print(f"Tags: {result['tags']}")
        else:
            print(f"❌ Error: {result.get('error')}")
    
    print(f"\n📊 Testing Complete!")
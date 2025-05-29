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
    
    def create_recipe(self, user_request: str) -> Dict:
        """
        Generate a basic recipe based on user request
        Returns structured recipe data for web API compatibility
        """
        
        prompt = f"""
Create a recipe based on this request: "{user_request}"

Please provide a well-structured, practical recipe. Make it good but not overly complex - we'll enhance it later.

Return your response in this EXACT JSON format:
{{
    "title": "Recipe Name",
    "description": "Brief description of the dish",
    "prep_time": "X minutes",
    "cook_time": "X minutes", 
    "total_time": "X minutes",
    "servings": "X",
    "difficulty": "Easy/Medium/Hard",
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

Make sure the JSON is valid and complete. Include realistic measurements and clear instructions.
"""
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            recipe_text = response.content[0].text.strip()
            
            # Extract JSON from the response
            recipe_data = self._extract_json_from_response(recipe_text)
            
            # Validate and clean the recipe data
            validated_recipe = self._validate_recipe_data(recipe_data, user_request)
            
            return validated_recipe
            
        except Exception as e:
            # Return error in structured format
            return {
                "error": f"Recipe generation failed: {str(e)}",
                "title": f"Failed Recipe for: {user_request}",
                "success": False
            }
    
    def _extract_json_from_response(self, response_text: str) -> Dict:
        """Extract JSON from Claude's response, handling various formats"""
        
        # Try to find JSON block
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                # If JSON is malformed, try to fix common issues
                return self._fix_malformed_json(json_str)
        
        # If no JSON found, try to parse the entire response
        try:
            return json.loads(response_text)
        except:
            raise Exception("Could not extract valid JSON from recipe response")
    
    def _fix_malformed_json(self, json_str: str) -> Dict:
        """Try to fix common JSON formatting issues"""
        
        # Remove any trailing commas
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
        
        # Try parsing again
        try:
            return json.loads(json_str)
        except:
            raise Exception("Could not fix malformed JSON")
    
    def _validate_recipe_data(self, recipe_data: Dict, original_request: str) -> Dict:
        """Ensure recipe data has all required fields and is web-ready"""
        
        # Required fields with defaults
        validated = {
            "title": recipe_data.get("title", f"Recipe for {original_request}"),
            "description": recipe_data.get("description", "A delicious recipe"),
            "prep_time": recipe_data.get("prep_time", "Unknown"),
            "cook_time": recipe_data.get("cook_time", "Unknown"),
            "total_time": recipe_data.get("total_time", "Unknown"),
            "servings": str(recipe_data.get("servings", "4")),
            "difficulty": recipe_data.get("difficulty", "Medium"),
            "ingredients": recipe_data.get("ingredients", []),
            "instructions": recipe_data.get("instructions", []),
            "tags": recipe_data.get("tags", []),
            "cuisine_type": recipe_data.get("cuisine_type", "Unknown"),
            "meal_type": recipe_data.get("meal_type", "Unknown"),
            "success": True,
            "agent": "recipe_generator",
            "original_request": original_request
        }
        
        # Clean and validate ingredients
        if not validated["ingredients"]:
            validated["ingredients"] = ["Ingredients need to be specified"]
        
        # Clean and validate instructions
        if not validated["instructions"]:
            validated["instructions"] = ["Instructions need to be specified"]
        
        # Ensure we have at least some tags
        if not validated["tags"]:
            validated["tags"] = ["homemade", "recipe"]
        
        return validated
    
    def regenerate_recipe(self, original_recipe: Dict, feedback: str) -> Dict:
        """
        Regenerate a recipe based on feedback - useful for the enhancement loop
        """
        
        prompt = f"""
Here's a recipe that needs improvement:

CURRENT RECIPE:
{json.dumps(original_recipe, indent=2)}

FEEDBACK FOR IMPROVEMENT:
{feedback}

Please create an improved version of this recipe addressing the feedback. 
Keep the same JSON structure but make the requested improvements.

Return the improved recipe in the same JSON format as before.
"""
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            recipe_text = response.content[0].text.strip()
            recipe_data = self._extract_json_from_response(recipe_text)
            validated_recipe = self._validate_recipe_data(
                recipe_data, 
                original_recipe.get("original_request", "improved recipe")
            )
            
            return validated_recipe
            
        except Exception as e:
            # Return the original recipe with error note if regeneration fails
            original_recipe["regeneration_error"] = str(e)
            return original_recipe

# Test the agent directly (optional)
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    generator = RecipeGenerator()
    
    # Test basic generation
    test_request = "spicy chicken tacos"
    print(f"Testing recipe generation for: {test_request}")
    
    result = generator.create_recipe(test_request)
    
    if result.get("success"):
        print("\n✅ Recipe Generated Successfully!")
        print(f"Title: {result['title']}")
        print(f"Prep Time: {result['prep_time']}")
        print(f"Ingredients: {len(result['ingredients'])} items")
        print(f"Instructions: {len(result['instructions'])} steps")
    else:
        print(f"❌ Error: {result.get('error')}")
    
    print(f"\n📊 Full Recipe Data:")
    print(json.dumps(result, indent=2))
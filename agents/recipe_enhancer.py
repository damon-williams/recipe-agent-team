# agents/recipe_enhancer.py
import os
from anthropic import Anthropic
from typing import Dict, List
import json
import random

class RecipeEnhancer:
    def __init__(self):
        self.client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        self.model = "claude-sonnet-4-20250514"
        
        # Enhancement strategies to make recipes more interesting
        self.enhancement_strategies = [
            "flavor_boosting",
            "texture_variation", 
            "presentation_upgrade",
            "technique_sophistication",
            "ingredient_substitution",
            "fusion_elements",
            "seasonal_adaptation"
        ]
    
    def enhance_recipe(self, basic_recipe: Dict, inspiration_data: Dict = None) -> Dict:
        """
        Take a basic recipe and make it more interesting/sophisticated
        Uses inspiration from web research if available
        """
        
        # Choose enhancement strategies based on recipe type and inspiration
        strategies = self._select_enhancement_strategies(basic_recipe, inspiration_data)
        
        prompt = self._build_enhancement_prompt(basic_recipe, inspiration_data, strategies)
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            enhanced_text = response.content[0].text.strip()
            enhanced_data = self._extract_json_from_response(enhanced_text)
            validated_recipe = self._validate_enhanced_recipe(enhanced_data, basic_recipe)
            
            return validated_recipe
            
        except Exception as e:
            # Return original recipe with enhancement error if failed
            error_recipe = basic_recipe.copy()
            error_recipe["enhancement_error"] = str(e)
            error_recipe["enhancement_attempted"] = True
            return error_recipe
    
    def _select_enhancement_strategies(self, recipe: Dict, inspiration: Dict = None) -> List[str]:
        """Select 2-3 enhancement strategies based on recipe characteristics"""
        
        strategies = []
        
        # Base strategy selection on recipe type and difficulty
        difficulty = recipe.get("difficulty", "Medium").lower()
        meal_type = recipe.get("meal_type", "").lower()
        cuisine = recipe.get("cuisine_type", "").lower()
        
        # Always try flavor boosting
        strategies.append("flavor_boosting")
        
        # Add texture variation for most recipes
        if len(recipe.get("ingredients", [])) > 3:
            strategies.append("texture_variation")
        
        # Add presentation for dinner/special meals
        if meal_type in ["dinner", "dessert"] or difficulty == "easy":
            strategies.append("presentation_upgrade")
        
        # Add technique sophistication for easy recipes
        if difficulty == "easy":
            strategies.append("technique_sophistication")
        
        # Add fusion elements if we have inspiration from different cuisines
        if inspiration and len(inspiration.get("sources", [])) > 1:
            strategies.append("fusion_elements")
        
        # Limit to 2-3 strategies to avoid overwhelming changes
        return strategies[:3]
    
    def _build_enhancement_prompt(self, basic_recipe: Dict, inspiration: Dict, strategies: List[str]) -> str:
        """Build the prompt for recipe enhancement"""
        
        strategies_desc = {
            "flavor_boosting": "Add complementary spices, herbs, aromatics, or flavor compounds",
            "texture_variation": "Introduce contrasting textures (crunchy, creamy, chewy elements)",
            "presentation_upgrade": "Improve plating, garnishing, and visual appeal",
            "technique_sophistication": "Upgrade cooking techniques (braising, reduction, emulsification)",
            "ingredient_substitution": "Substitute with higher-quality or more interesting ingredients",
            "fusion_elements": "Incorporate elements from other cuisines tastefully",
            "seasonal_adaptation": "Adapt for seasonal ingredients and flavors"
        }
        
        inspiration_text = ""
        if inspiration and inspiration.get("sources"):
            inspiration_text = f"""
INSPIRATION FROM WEB RESEARCH:
{json.dumps(inspiration, indent=2)}

Use this inspiration to inform your enhancements, but don't copy directly.
"""
        
        selected_strategies_text = "\n".join([
            f"- {strategy}: {strategies_desc[strategy]}" 
            for strategy in strategies
        ])
        
        prompt = f"""
TASK: Enhance this basic recipe to make it more interesting and sophisticated.

CURRENT RECIPE:
{json.dumps(basic_recipe, indent=2)}

{inspiration_text}

ENHANCEMENT STRATEGIES TO APPLY:
{selected_strategies_text}

REQUIREMENTS:
1. Keep the core recipe concept and structure
2. Make meaningful improvements that add value
3. Ensure changes are practical for home cooks
4. Don't make it overly complex - enhance, don't overcomplicate
5. Add new ingredients/steps only if they significantly improve the dish
6. Update cooking times if new techniques require it

Return the enhanced recipe in this EXACT JSON format:
{{
    "title": "Enhanced Recipe Name (can be more appealing)",
    "description": "Updated description highlighting improvements",
    "prep_time": "X minutes",
    "cook_time": "X minutes",
    "total_time": "X minutes", 
    "servings": "X",
    "difficulty": "Easy/Medium/Hard",
    "ingredients": [
        "enhanced ingredient list with measurements"
    ],
    "instructions": [
        "enhanced step-by-step instructions"
    ],
    "tags": ["updated", "tags", "including", "new", "characteristics"],
    "cuisine_type": "cuisine name (can be fusion if appropriate)",
    "meal_type": "breakfast/lunch/dinner/snack/dessert",
    "enhancements_made": [
        "specific enhancement 1",
        "specific enhancement 2"
    ],
    "chef_notes": [
        "tips for best results",
        "substitution suggestions"
    ],
    "enhancement_level": "moderate/significant"
}}

Focus on making real improvements that will make the dish more delicious and interesting!
"""
        
        return prompt
    
    def _extract_json_from_response(self, response_text: str) -> Dict:
        """Extract JSON from Claude's response"""
        import re
        
        # Try to find JSON block
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                # Try to fix common JSON issues
                json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
                return json.loads(json_str)
        
        raise Exception("Could not extract valid JSON from enhancement response")
    
    def _validate_enhanced_recipe(self, enhanced_data: Dict, original_recipe: Dict) -> Dict:
        """Validate enhanced recipe and ensure it has all required fields"""
        
        # Start with original recipe as base
        validated = original_recipe.copy()
        
        # Update with enhancements
        for key, value in enhanced_data.items():
            if value:  # Only update if the new value is not empty
                validated[key] = value
        
        # Ensure new required fields exist
        validated.setdefault("enhancements_made", ["General improvements"])
        validated.setdefault("chef_notes", [])
        validated.setdefault("enhancement_level", "moderate")
        
        # Mark as enhanced
        validated["enhanced"] = True
        validated["enhancement_agent"] = "recipe_enhancer"
        validated["original_title"] = original_recipe.get("title", "Unknown")
        
        # Validate that we actually made improvements
        if len(enhanced_data.get("ingredients", [])) < len(original_recipe.get("ingredients", [])):
            # If ingredients got shorter, it might not be an improvement
            validated["enhancement_warning"] = "Enhancement may have simplified the recipe"
        
        return validated
    
    def suggest_variations(self, recipe: Dict) -> List[Dict]:
        """Generate recipe variations for web app features"""
        
        prompt = f"""
Based on this recipe, suggest 3 interesting variations:

RECIPE:
{json.dumps(recipe, indent=2)}

For each variation, provide:
1. A descriptive name
2. What changes to make
3. Why this variation is appealing

Return as JSON array:
[
    {{
        "name": "Variation Name",
        "changes": ["change 1", "change 2"],
        "appeal": "why this is interesting",
        "difficulty_change": "easier/same/harder"
    }}
]
"""
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            variations_text = response.content[0].text.strip()
            # Extract JSON array from response
            import re
            json_match = re.search(r'\[.*\]', variations_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            
        except Exception as e:
            pass
        
        # Return default variations if generation fails
        return [
            {
                "name": f"Spiced {recipe.get('title', 'Recipe')}",
                "changes": ["Add warming spices", "Increase seasoning"],
                "appeal": "More flavorful and aromatic",
                "difficulty_change": "same"
            }
        ]

# Test the enhancer directly
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    # Test data - basic recipe
    test_recipe = {
        "title": "Basic Chicken Pasta",
        "description": "Simple chicken and pasta dish",
        "prep_time": "15 minutes",
        "cook_time": "20 minutes",
        "total_time": "35 minutes",
        "servings": "4",
        "difficulty": "Easy",
        "ingredients": [
            "1 lb chicken breast, sliced",
            "12 oz pasta",
            "2 tbsp olive oil",
            "Salt and pepper to taste"
        ],
        "instructions": [
            "Cook pasta according to package directions",
            "Heat oil in pan and cook chicken",
            "Combine pasta and chicken",
            "Season with salt and pepper"
        ],
        "tags": ["easy", "chicken", "pasta"],
        "cuisine_type": "Italian",
        "meal_type": "dinner"
    }
    
    enhancer = RecipeEnhancer()
    
    print("Testing recipe enhancement...")
    enhanced = enhancer.enhance_recipe(test_recipe)
    
    if enhanced.get("enhanced"):
        print("\n✅ Recipe Enhanced Successfully!")
        print(f"Original: {test_recipe['title']}")
        print(f"Enhanced: {enhanced['title']}")
        print(f"Enhancements: {enhanced.get('enhancements_made', [])}")
        print(f"Enhancement Level: {enhanced.get('enhancement_level', 'unknown')}")
    else:
        print("❌ Enhancement failed")
    
    print(f"\n📊 Enhanced Recipe Preview:")
    print(f"Ingredients: {len(enhanced.get('ingredients', []))} items")
    print(f"Instructions: {len(enhanced.get('instructions', []))} steps")
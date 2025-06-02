# agents/recipe_enhancer.py
import os
from anthropic import Anthropic
from typing import Dict, List
import json
import random
import re

class RecipeEnhancer:
    def __init__(self):
        self.client = Anthropic(
            api_key=os.getenv('ANTHROPIC_API_KEY'),
            timeout=60.0  # 60 second timeout for API calls
        )
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
    
    def enhance_recipe(self, basic_recipe: Dict, inspiration_data: Dict = None, complexity: str = None) -> Dict:
        """
        Take a basic recipe and make it more interesting/sophisticated
        Uses inspiration from web research if available
        Now accepts complexity parameter for complexity-aware enhancements
        """
        
        try:
            print(f"🔧 Enhancing recipe: {basic_recipe.get('title', 'Unknown')}")
            
            # Use complexity from parameter or fall back to recipe difficulty
            target_complexity = complexity or basic_recipe.get('difficulty', 'Medium')
            print(f"🔧 Target complexity: {target_complexity}")
            
            # Choose enhancement strategies based on recipe type, inspiration, and complexity
            strategies = self._select_enhancement_strategies(basic_recipe, inspiration_data, target_complexity)
            
            prompt = self._build_enhancement_prompt(basic_recipe, inspiration_data, strategies, target_complexity)
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                timeout=60,  # Explicit timeout per request
                messages=[{"role": "user", "content": prompt}]
            )
            
            enhanced_text = response.content[0].text.strip()
            print(f"📝 Claude response length: {len(enhanced_text)} characters")
            
            # Enhanced JSON extraction with better error handling
            enhanced_data = self._extract_json_from_response(enhanced_text)
            
            if not enhanced_data:
                print("⚠️ No valid JSON found, using original recipe")
                return self._mark_enhancement_failed(basic_recipe, "No valid JSON response")
            
            validated_recipe = self._validate_enhanced_recipe(enhanced_data, basic_recipe, target_complexity)
            
            print(f"✅ Recipe enhanced successfully: {validated_recipe.get('title', 'Unknown')}")
            return validated_recipe
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing failed: {str(e)}")
            return self._mark_enhancement_failed(basic_recipe, f"JSON parsing error: {str(e)}")
            
        except Exception as e:
            print(f"❌ Enhancement failed: {str(e)}")
            return self._mark_enhancement_failed(basic_recipe, str(e))
    
    def _extract_json_from_response(self, response_text: str) -> Dict:
        """Extract JSON from Claude's response with robust error handling"""
        
        print(f"🔍 Extracting JSON from response...")
        
        # Method 1: Try to find complete JSON block
        json_patterns = [
            r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',  # Simple nested JSON
            r'\{.*?\}(?=\s*$)',  # JSON at end of text
            r'\{.*?\}',  # Any JSON-like structure
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, response_text, re.DOTALL)
            for match in matches:
                try:
                    # Clean the JSON string
                    cleaned_json = self._clean_json_string(match)
                    parsed = json.loads(cleaned_json)
                    
                    # Validate that it looks like a recipe
                    if self._is_valid_recipe_json(parsed):
                        print(f"✅ Valid JSON found using pattern")
                        return parsed
                        
                except json.JSONDecodeError:
                    continue
        
        # Method 2: Try to extract individual fields if complete JSON fails
        print("⚠️ Complete JSON extraction failed, trying field extraction...")
        return self._extract_recipe_fields(response_text)
    
    def _clean_json_string(self, json_str: str) -> str:
        """Clean common JSON formatting issues"""
        
        # Remove leading/trailing whitespace
        json_str = json_str.strip()
        
        # Remove trailing commas before closing braces/brackets
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
        
        # Fix missing quotes around keys (common Claude issue)
        json_str = re.sub(r'(\w+)(\s*):', r'"\1"\2:', json_str)
        
        # Fix already quoted keys that got double-quoted
        json_str = re.sub(r'""(\w+)""', r'"\1"', json_str)
        
        return json_str
    
    def _is_valid_recipe_json(self, parsed_json: Dict) -> bool:
        """Check if the parsed JSON looks like a valid recipe"""
        
        required_fields = ['title', 'ingredients', 'instructions']
        return all(field in parsed_json for field in required_fields)
    
    def _extract_recipe_fields(self, text: str) -> Dict:
        """Extract recipe fields individually if JSON parsing fails"""
        
        print("🔧 Attempting field-by-field extraction...")
        
        extracted = {}
        
        # Extract title
        title_match = re.search(r'"title":\s*"([^"]*)"', text)
        if title_match:
            extracted['title'] = title_match.group(1)
        
        # Extract description
        desc_match = re.search(r'"description":\s*"([^"]*)"', text)
        if desc_match:
            extracted['description'] = desc_match.group(1)
        
        # Extract simple fields
        simple_fields = ['prep_time', 'cook_time', 'total_time', 'servings', 'difficulty', 'cuisine_type', 'meal_type', 'enhancement_level']
        for field in simple_fields:
            match = re.search(rf'"{field}":\s*"([^"]*)"', text)
            if match:
                extracted[field] = match.group(1)
        
        # Extract arrays (ingredients, instructions, tags, etc.)
        array_fields = ['ingredients', 'instructions', 'tags', 'enhancements_made', 'chef_notes']
        for field in array_fields:
            extracted[field] = self._extract_array_field(text, field)
        
        # Only return if we got essential fields
        if extracted.get('title') and (extracted.get('ingredients') or extracted.get('instructions')):
            print(f"✅ Field extraction successful: {extracted.get('title')}")
            return extracted
        
        print("❌ Field extraction failed")
        return {}
    
    def _extract_array_field(self, text: str, field_name: str) -> List[str]:
        """Extract array fields from text"""
        
        # Look for array pattern
        pattern = rf'"{field_name}":\s*\[(.*?)\]'
        match = re.search(pattern, text, re.DOTALL)
        
        if not match:
            return []
        
        array_content = match.group(1)
        
        # Extract quoted strings from array
        items = re.findall(r'"([^"]*)"', array_content)
        
        # Clean and filter items
        cleaned_items = [item.strip() for item in items if item.strip()]
        
        return cleaned_items
    
    def _mark_enhancement_failed(self, basic_recipe: Dict, error_message: str) -> Dict:
        """Mark recipe as enhancement failed but return usable recipe"""
        
        error_recipe = basic_recipe.copy()
        error_recipe["enhancement_error"] = error_message
        error_recipe["enhancement_attempted"] = True
        error_recipe["enhanced"] = False
        
        print(f"⚠️ Returning original recipe due to error: {error_message}")
        return error_recipe
    
    def _select_enhancement_strategies(self, recipe: Dict, inspiration: Dict = None, complexity: str = "Medium") -> List[str]:
        """Select 2-3 enhancement strategies based on recipe characteristics and complexity"""
        
        strategies = []
        
        # Base strategy selection on recipe type, difficulty, and target complexity
        difficulty = recipe.get("difficulty", "Medium").lower()
        meal_type = recipe.get("meal_type", "").lower()
        cuisine = recipe.get("cuisine_type", "").lower()
        
        # Map complexity levels for strategy selection
        complexity_map = {
            "Easy": "easy",
            "Simple": "easy", 
            "Medium": "medium",
            "High": "high",
            "Gourmet": "high"
        }
        target_level = complexity_map.get(complexity, "medium")
        
        print(f"🔧 Selecting strategies for {target_level} complexity level")
        
        # Always try flavor boosting for all levels
        strategies.append("flavor_boosting")
        
        # Add complexity-appropriate strategies
        if target_level == "easy":
            # For easy recipes, focus on simple improvements
            strategies.append("presentation_upgrade")
            if len(recipe.get("ingredients", [])) > 5:
                strategies.append("texture_variation")
        
        elif target_level == "medium":
            # For medium complexity, balanced enhancements
            strategies.append("texture_variation")
            if meal_type in ["dinner", "lunch"]:
                strategies.append("technique_sophistication")
            else:
                strategies.append("presentation_upgrade")
        
        elif target_level == "high":
            # For high complexity, advanced techniques
            strategies.append("technique_sophistication")
            strategies.append("ingredient_substitution")
            if inspiration and len(inspiration.get("sources", [])) > 1:
                strategies.append("fusion_elements")
        
        # Add fusion elements if we have diverse inspiration
        if inspiration and len(inspiration.get("sources", [])) > 1 and "fusion_elements" not in strategies:
            strategies.append("fusion_elements")
        
        # Limit to 3 strategies to avoid overwhelming changes
        selected_strategies = strategies[:3]
        print(f"🔧 Selected strategies: {selected_strategies}")
        
        return selected_strategies
    
    def _build_enhancement_prompt(self, basic_recipe: Dict, inspiration: Dict, strategies: List[str], complexity: str) -> str:
        """Build the prompt for recipe enhancement with complexity awareness"""
        
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
        
        # Get complexity-specific guidance
        complexity_guidance = self._get_complexity_guidance(complexity)
        
        prompt = f"""
TASK: Enhance this basic recipe to make it more interesting and sophisticated while maintaining {complexity} complexity level.

CURRENT RECIPE:
{json.dumps(basic_recipe, indent=2)}

TARGET COMPLEXITY: {complexity}
{complexity_guidance}

{inspiration_text}

ENHANCEMENT STRATEGIES TO APPLY:
{selected_strategies_text}

REQUIREMENTS:
1. Keep the core recipe concept and structure
2. Make meaningful improvements that add value while staying at {complexity} complexity
3. Ensure changes are appropriate for {complexity} level cooks
4. Don't make it overly complex - enhance within the {complexity} complexity bounds
5. Add new ingredients/steps only if they fit the {complexity} level
6. Update cooking times if new techniques require it
7. Maintain the {complexity} complexity level throughout

Return the enhanced recipe in this EXACT JSON format (ensure valid JSON syntax):
{{
    "title": "Enhanced Recipe Name (can be more appealing)",
    "description": "Updated description highlighting improvements",
    "prep_time": "X minutes",
    "cook_time": "X minutes",
    "total_time": "X minutes", 
    "servings": "X",
    "difficulty": "{complexity}",
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

IMPORTANT: Return ONLY the JSON object, no additional text or explanations. Ensure the recipe maintains {complexity} complexity level.
"""
        
        return prompt
    
    def _get_complexity_guidance(self, complexity: str) -> str:
        """Get complexity-specific guidance for enhancements"""
        
        guidance = {
            "Easy": """
EASY COMPLEXITY ENHANCEMENT GUIDELINES:
- Keep enhancements simple and accessible
- Use common ingredients and basic techniques
- Focus on flavor improvements that don't add complexity
- Enhance presentation with simple garnishes
- Avoid specialized equipment or advanced techniques
- Keep total ingredients under 10-12 items
- Maintain simple, clear instructions""",
            
            "Medium": """
MEDIUM COMPLEXITY ENHANCEMENT GUIDELINES:
- Balance sophistication with accessibility
- Can introduce 1-2 specialty ingredients
- Use moderate techniques like sauce reductions or herb oils
- Enhance with thoughtful flavor layering
- Acceptable to add 2-3 extra steps if they add significant value
- Can require basic kitchen tools beyond pots and pans
- Maintain organized, clear instruction flow""",
            
            "High": """
HIGH COMPLEXITY ENHANCEMENT GUIDELINES:
- Embrace sophisticated techniques and premium ingredients
- Can use advanced cooking methods and specialized equipment
- Focus on restaurant-quality improvements
- Acceptable to significantly increase ingredient count for complex flavors
- Can add multiple preparation components and sub-recipes
- Enhance with professional presentation techniques
- Maintain clear organization despite increased complexity"""
        }
        
        # Handle alternative complexity names
        complexity_map = {
            "Simple": "Easy",
            "Gourmet": "High"
        }
        
        mapped_complexity = complexity_map.get(complexity, complexity)
        return guidance.get(mapped_complexity, guidance["Medium"])
    
    def _validate_enhanced_recipe(self, enhanced_data: Dict, original_recipe: Dict, complexity: str = None) -> Dict:
        """Validate enhanced recipe and ensure it has all required fields"""
        
        # Start with original recipe as base
        validated = original_recipe.copy()
        
        # Update with enhancements
        for key, value in enhanced_data.items():
            if value:  # Only update if the new value is not empty
                validated[key] = value
        
        # Ensure target complexity is maintained
        if complexity:
            validated["difficulty"] = complexity
            validated["target_complexity"] = complexity
        
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
        
        # Add complexity tracking
        validated["complexity_maintained"] = complexity or original_recipe.get("difficulty", "Medium")
        
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
            json_match = re.search(r'\[.*\]', variations_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            
        except Exception as e:
            print(f"⚠️ Variations generation failed: {str(e)}")
        
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
    
    print("Testing recipe enhancement with complexity...")
    
    # Test with different complexity levels
    for complexity in ["Easy", "Medium", "High"]:
        print(f"\n{'='*50}")
        print(f"Testing {complexity} complexity enhancement")
        print(f"{'='*50}")
        
        enhanced = enhancer.enhance_recipe(test_recipe, None, complexity)
        
        if enhanced.get("enhanced"):
            print(f"\n✅ Recipe Enhanced Successfully for {complexity}!")
            print(f"Original: {test_recipe['title']}")
            print(f"Enhanced: {enhanced['title']}")
            print(f"Target Complexity: {complexity}")
            print(f"Final Difficulty: {enhanced.get('difficulty', 'Unknown')}")
            print(f"Enhancements: {enhanced.get('enhancements_made', [])}")
            print(f"Enhancement Level: {enhanced.get('enhancement_level', 'unknown')}")
        else:
            print(f"❌ Enhancement failed for {complexity}")
            if enhanced.get("enhancement_error"):
                print(f"Error: {enhanced['enhancement_error']}")
    
    print(f"\n📊 Testing Complete!")
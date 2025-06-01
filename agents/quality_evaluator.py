# agents/quality_evaluator.py
import os
from anthropic import Anthropic
from typing import Dict, List, Tuple
import json
import statistics
from dataclasses import dataclass

@dataclass
class QualityMetrics:
    creativity_score: float
    practicality_score: float
    nutrition_score: float
    completeness_score: float
    complexity_alignment_score: float
    overall_score: float
    confidence: str

class QualityEvaluator:
    def __init__(self):
        self.client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        self.model = "claude-sonnet-4-20250514"
        
        # Quality thresholds for different aspects
        self.quality_thresholds = {
            'minimum_acceptable': 6.0,
            'good_quality': 7.5,
            'excellent_quality': 9.0
        }
        
        # Weights for different quality aspects (updated with complexity alignment)
        self.evaluation_weights = {
            'creativity': 0.20,
            'practicality': 0.25,
            'nutrition': 0.20,
            'completeness': 0.15,
            'complexity_alignment': 0.20  # New metric for complexity matching
        }
        
        print("⭐ QualityEvaluator initialized with complexity-aware scoring")
    
    def evaluate_recipe(self, recipe: Dict, nutrition_data: Dict = None, inspiration_data: Dict = None, complexity: str = "Medium") -> Dict:
        """
        Comprehensive recipe quality evaluation with complexity consideration
        Returns scoring and recommendations for improvement
        """
        
        print(f"⭐ Evaluating quality of: {recipe.get('title', 'Unknown Recipe')} (Expected: {complexity} complexity)")
        
        try:
            # Evaluate different quality dimensions
            creativity_result = self._evaluate_creativity(recipe, inspiration_data, complexity)
            practicality_result = self._evaluate_practicality(recipe, complexity)
            nutrition_result = self._evaluate_nutrition_quality(nutrition_data) if nutrition_data else None
            completeness_result = self._evaluate_completeness(recipe)
            complexity_alignment_result = self._evaluate_complexity_alignment(recipe, complexity)
            
            # Debug output for each evaluation
            print(f"⭐ Creativity Score: {creativity_result.get('score', 'N/A')}/10")
            print(f"⭐ Practicality Score: {practicality_result.get('score', 'N/A')}/10")
            print(f"⭐ Nutrition Score: {nutrition_result.get('score', 'N/A') if nutrition_result else 'N/A'}/10")
            print(f"⭐ Completeness Score: {completeness_result.get('score', 'N/A')}/10")
            print(f"⭐ Complexity Alignment Score: {complexity_alignment_result.get('score', 'N/A')}/10")
            
            # Calculate weighted overall score
            overall_score = self._calculate_overall_score(
                creativity_result, practicality_result, nutrition_result, 
                completeness_result, complexity_alignment_result
            )
            
            print(f"⭐ Overall Weighted Score: {overall_score}/10")
            
            # Generate improvement recommendations
            recommendations = self._generate_improvement_recommendations(
                recipe, creativity_result, practicality_result, nutrition_result, 
                completeness_result, complexity_alignment_result, complexity
            )
            
            # Determine if recipe meets quality threshold
            quality_verdict = self._determine_quality_verdict(overall_score)
            
            print(f"⭐ Quality Verdict: {quality_verdict} ({self._get_quality_level(overall_score)})")
            
            return {
                'score': overall_score,
                'quality_verdict': quality_verdict,
                'detailed_scores': {
                    'creativity': creativity_result,
                    'practicality': practicality_result,
                    'nutrition': nutrition_result,
                    'completeness': completeness_result,
                    'complexity_alignment': complexity_alignment_result
                },
                'recommendations': recommendations,
                'meets_threshold': overall_score >= self.quality_thresholds['minimum_acceptable'],
                'quality_level': self._get_quality_level(overall_score),
                'confidence': self._calculate_confidence(creativity_result, practicality_result, nutrition_result, completeness_result, complexity_alignment_result),
                'evaluation_timestamp': self._get_timestamp(),
                'complexity_evaluated': complexity
            }
            
        except Exception as e:
            print(f"⚠️  Quality evaluation failed: {str(e)}")
            return self._create_fallback_evaluation(recipe, complexity)
    
    def _evaluate_complexity_alignment(self, recipe: Dict, expected_complexity: str) -> Dict:
        """Evaluate how well the recipe matches the expected complexity level"""
        
        print(f"⭐ Evaluating complexity alignment for {expected_complexity} level...")
        
        # Prepare recipe data for complexity evaluation
        recipe_data = {
            'title': recipe.get('title'),
            'ingredients': recipe.get('ingredients', []),
            'instructions': recipe.get('instructions', []),
            'prep_time': recipe.get('prep_time'),
            'cook_time': recipe.get('cook_time'),
            'difficulty': recipe.get('difficulty')
        }
        
        complexity_criteria = self._get_complexity_criteria(expected_complexity)
        
        complexity_prompt = f"""
Evaluate how well this recipe matches the {expected_complexity} complexity level on a scale of 1-10:

RECIPE TO EVALUATE:
{json.dumps(recipe_data, indent=2)}

EXPECTED COMPLEXITY: {expected_complexity}
{complexity_criteria}

Evaluate complexity alignment based on:
1. Ingredient accessibility and specialization
2. Cooking techniques required
3. Time commitment (prep + cook)
4. Equipment needs
5. Skill level required
6. Number of steps and sub-processes

Return JSON:
{{
    "score": number (1-10),
    "alignment_analysis": "detailed explanation of how well it matches {expected_complexity}",
    "complexity_gaps": ["what makes it more/less complex than expected"],
    "strengths": ["aspects that match {expected_complexity} well"],
    "improvements": ["how to better align with {expected_complexity}"],
    "confidence": "low/medium/high"
}}

Score 10 = perfect alignment, 5 = somewhat matches, 1 = completely wrong complexity
"""
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=800,
                messages=[{"role": "user", "content": complexity_prompt}]
            )
            
            result = self._extract_evaluation_json(response.content[0].text)
            score = result.get('score', 5.0)
            
            print(f"⭐ Complexity alignment: {score}/10 for {expected_complexity}")
            if result.get('alignment_analysis'):
                print(f"⭐ Analysis: {result['alignment_analysis'][:100]}...")
            
            return result
            
        except Exception as e:
            print(f"⚠️ Complexity alignment evaluation failed: {str(e)}")
            return self._fallback_complexity_score(recipe, expected_complexity)
    
    def _get_complexity_criteria(self, complexity: str) -> str:
        """Get detailed criteria for each complexity level"""
        
        criteria = {
            "Simple": """
SIMPLE COMPLEXITY CRITERIA:
- Common ingredients available in most grocery stores
- Basic cooking techniques (sauté, boil, bake, grill)
- 8-10 ingredients maximum
- Under 45 minutes total time
- Basic kitchen equipment only
- Clear, straightforward instructions
- Minimal prep work required""",
            
            "Medium": """
MEDIUM COMPLEXITY CRITERIA:
- Mix of common and some specialty ingredients
- Moderate techniques (braising, sauce-making, roasting)
- 10-15 ingredients
- 45-90 minutes total time
- Some specialized tools acceptable
- Multi-step processes but organized
- Some advanced techniques but accessible""",
            
            "Gourmet": """
GOURMET COMPLEXITY CRITERIA:
- Premium, specialty, or hard-to-find ingredients
- Advanced techniques (confit, emulsification, sous vide)
- 15+ ingredients for complex flavors
- 90+ minutes or multi-day preparation
- Specialized equipment may be required
- Professional-level techniques
- Restaurant-quality presentation focus"""
        }
        
        return criteria.get(complexity, criteria["Medium"])
    
    def _evaluate_creativity(self, recipe: Dict, inspiration_data: Dict = None, complexity: str = "Medium") -> Dict:
        """Evaluate the creativity and innovation of the recipe with complexity context"""
        
        print(f"⭐ Evaluating creativity for {complexity} complexity level...")
        
        # Prepare recipe data for evaluation
        recipe_data = {
            'title': recipe.get('title'),
            'description': recipe.get('description'),
            'ingredients': recipe.get('ingredients', [])[:10],
            'techniques': recipe.get('instructions', [])[:5],
            'enhancements_made': recipe.get('enhancements_made', [])
        }
        
        inspiration_text = ""
        if inspiration_data:
            inspiration_text = "INSPIRATION USED:" + json.dumps(inspiration_data, indent=2)
        
        creativity_prompt = f"""
Evaluate the CREATIVITY and INNOVATION of this {complexity} complexity recipe on a scale of 1-10:

RECIPE TO EVALUATE:
{json.dumps(recipe_data, indent=2)}

COMPLEXITY LEVEL: {complexity}
{inspiration_text}

Evaluate creativity based on:
1. Ingredient combinations (unique, interesting pairings for {complexity} level)
2. Cooking techniques (innovation appropriate for {complexity})
3. Flavor profiles (complexity and balance suitable for {complexity})
4. Presentation elements (visual appeal matching {complexity})
5. Creative enhancements over basic versions

COMPLEXITY CONTEXT:
- Simple: Creativity through accessible flavor combinations and simple techniques
- Medium: Balanced innovation with moderate complexity
- Gourmet: High creativity expected with advanced techniques and premium ingredients

Return JSON:
{{
    "score": number (1-10),
    "strengths": ["strength 1", "strength 2"],
    "areas_for_improvement": ["improvement 1", "improvement 2"],
    "creativity_highlights": ["highlight 1", "highlight 2"],
    "confidence": "low/medium/high"
}}

Rate creativity relative to the {complexity} complexity level expectations.
"""
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=800,
                messages=[{"role": "user", "content": creativity_prompt}]
            )
            
            result = self._extract_evaluation_json(response.content[0].text)
            score = result.get('score', 5.0)
            print(f"⭐ Creativity: {score}/10 for {complexity} level")
            
            return result
            
        except Exception as e:
            print(f"⚠️ Creativity evaluation failed: {str(e)}")
            return self._fallback_creativity_score(recipe)
    
    def _evaluate_practicality(self, recipe: Dict, complexity: str = "Medium") -> Dict:
        """Evaluate how practical and achievable the recipe is with complexity expectations"""
        
        print(f"⭐ Evaluating practicality for {complexity} complexity level...")
        
        # Prepare recipe data for practicality evaluation
        practicality_data = {
            'title': recipe.get('title'),
            'prep_time': recipe.get('prep_time'),
            'cook_time': recipe.get('cook_time'),
            'difficulty': recipe.get('difficulty'),
            'ingredients': recipe.get('ingredients', []),
            'instructions': recipe.get('instructions', []),
            'servings': recipe.get('servings')
        }
        
        practicality_prompt = f"""
Evaluate the PRACTICALITY of this {complexity} complexity recipe for home cooks on a scale of 1-10:

RECIPE TO EVALUATE:
{json.dumps(practicality_data, indent=2)}

COMPLEXITY LEVEL: {complexity}

Evaluate practicality based on complexity-appropriate expectations:

FOR {complexity.upper()} RECIPES:
{self._get_complexity_criteria(complexity)}

Rate practicality considering:
1. Ingredient accessibility (appropriate for {complexity} level)
2. Equipment requirements (reasonable for {complexity})
3. Time commitment (suitable for {complexity} expectations)
4. Skill level required (matches {complexity} level)
5. Clear, actionable instructions
6. Realistic serving sizes and portions

Return JSON:
{{
    "score": number (1-10),
    "strengths": ["practical strength 1", "practical strength 2"],
    "areas_for_improvement": ["improvement 1", "improvement 2"],
    "accessibility_issues": ["issue 1", "issue 2"],
    "time_assessment": "reasonable/lengthy/quick",
    "confidence": "low/medium/high"
}}

Rate against {complexity} complexity expectations, not absolute simplicity.
"""
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=800,
                messages=[{"role": "user", "content": practicality_prompt}]
            )
            
            result = self._extract_evaluation_json(response.content[0].text)
            score = result.get('score', 5.0)
            print(f"⭐ Practicality: {score}/10 for {complexity} level")
            
            return result
            
        except Exception as e:
            print(f"⚠️ Practicality evaluation failed: {str(e)}")
            return self._fallback_practicality_score(recipe)
    
    def _evaluate_nutrition_quality(self, nutrition_data: Dict) -> Dict:
        """Evaluate the nutritional quality of the recipe"""
        
        print(f"⭐ Evaluating nutrition quality...")
        
        if not nutrition_data or not nutrition_data.get('nutrition_per_serving'):
            print(f"⚠️ No nutrition data available")
            return {
                'score': 5.0,
                'strengths': [],
                'areas_for_improvement': ['Nutrition data unavailable'],
                'confidence': 'low',
                'nutrition_highlights': []
            }
        
        nutrition = nutrition_data['nutrition_per_serving']
        existing_score = nutrition_data.get('nutrition_score', 5.0)
        
        # Use AI to provide more detailed nutrition evaluation
        nutrition_prompt = f"""
Evaluate the NUTRITIONAL QUALITY of this recipe on a scale of 1-10:

NUTRITION DATA:
{json.dumps(nutrition, indent=2)}

EXISTING ANALYSIS:
Health Insights: {nutrition_data.get('health_insights', [])}
Dietary Tags: {nutrition_data.get('dietary_tags', [])}
Recommendations: {nutrition_data.get('recommendations', [])}

Evaluate based on:
1. Macronutrient balance (protein, carbs, fats)
2. Micronutrient density (vitamins, minerals via ingredients)
3. Calorie appropriateness for meal type
4. Fiber content and digestive health
5. Sodium levels and heart health
6. Overall nutritional density

Return JSON:
{{
    "score": number (1-10),
    "strengths": ["nutritional strength 1", "strength 2"],
    "areas_for_improvement": ["improvement 1", "improvement 2"],
    "nutrition_highlights": ["highlight 1", "highlight 2"],
    "confidence": "low/medium/high"
}}
"""
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=600,
                messages=[{"role": "user", "content": nutrition_prompt}]
            )
            
            evaluation = self._extract_evaluation_json(response.content[0].text)
            
            # Blend AI evaluation with existing nutrition score
            if evaluation.get('score') and existing_score:
                evaluation['score'] = (evaluation['score'] + existing_score) / 2
            
            score = evaluation.get('score', 5.0)
            print(f"⭐ Nutrition: {score}/10")
            
            return evaluation
            
        except Exception as e:
            print(f"⚠️ Nutrition evaluation failed: {str(e)}")
            return {
                'score': existing_score,
                'strengths': nutrition_data.get('health_insights', [])[:2],
                'areas_for_improvement': nutrition_data.get('recommendations', [])[:2],
                'confidence': 'medium',
                'nutrition_highlights': nutrition_data.get('dietary_tags', [])
            }
    
    def _evaluate_completeness(self, recipe: Dict) -> Dict:
        """Evaluate how complete and well-structured the recipe is"""
        
        print(f"⭐ Evaluating recipe completeness...")
        
        # Check for required fields and quality
        completeness_metrics = {
            'has_title': bool(recipe.get('title')),
            'has_description': bool(recipe.get('description')),
            'has_ingredients': len(recipe.get('ingredients', [])) > 0,
            'has_instructions': len(recipe.get('instructions', [])) > 0,
            'has_timing': bool(recipe.get('prep_time')) and bool(recipe.get('cook_time')),
            'has_servings': bool(recipe.get('servings')),
            'ingredient_detail': self._check_ingredient_detail(recipe.get('ingredients', [])),
            'instruction_clarity': self._check_instruction_clarity(recipe.get('instructions', [])),
            'has_tags': len(recipe.get('tags', [])) > 0
        }
        
        # Calculate completeness score
        total_checks = len(completeness_metrics)
        passed_checks = sum(1 for passed in completeness_metrics.values() if passed)
        completeness_score = (passed_checks / total_checks) * 10
        
        print(f"⭐ Completeness: {completeness_score}/10 ({passed_checks}/{total_checks} checks passed)")
        
        # Generate feedback
        strengths = []
        improvements = []
        
        if completeness_metrics['ingredient_detail']:
            strengths.append("Detailed ingredient measurements")
        else:
            improvements.append("Add specific measurements to ingredients")
        
        if completeness_metrics['instruction_clarity']:
            strengths.append("Clear step-by-step instructions")
        else:
            improvements.append("Make instructions more detailed and clear")
        
        if completeness_metrics['has_timing']:
            strengths.append("Complete timing information")
        else:
            improvements.append("Add prep and cook time estimates")
        
        return {
            'score': round(completeness_score, 1),
            'strengths': strengths,
            'areas_for_improvement': improvements,
            'completeness_metrics': completeness_metrics,
            'confidence': 'high'
        }
    
    def _check_ingredient_detail(self, ingredients: List[str]) -> bool:
        """Check if ingredients have proper measurements and details"""
        if not ingredients:
            return False
        
        # Look for measurement patterns
        detailed_count = 0
        for ingredient in ingredients:
            if any(measure in ingredient.lower() for measure in 
                   ['cup', 'tbsp', 'tsp', 'lb', 'oz', 'gram', 'kg', 'liter', 'ml']):
                detailed_count += 1
        
        return detailed_count >= len(ingredients) * 0.7  # 70% should have measurements
    
    def _check_instruction_clarity(self, instructions: List[str]) -> bool:
        """Check if instructions are clear and actionable"""
        if not instructions:
            return False
        
        # Look for action words and detail
        clear_count = 0
        for instruction in instructions:
            if len(instruction.split()) >= 5:  # At least 5 words
                clear_count += 1
        
        return clear_count >= len(instructions) * 0.8  # 80% should be detailed
    
    def _calculate_overall_score(self, creativity: Dict, practicality: Dict, 
                               nutrition: Dict, completeness: Dict, complexity_alignment: Dict) -> float:
        """Calculate weighted overall quality score including complexity alignment"""
        
        scores = []
        weights = []
        
        if creativity and creativity.get('score'):
            scores.append(creativity['score'])
            weights.append(self.evaluation_weights['creativity'])
        
        if practicality and practicality.get('score'):
            scores.append(practicality['score'])
            weights.append(self.evaluation_weights['practicality'])
        
        if nutrition and nutrition.get('score'):
            scores.append(nutrition['score'])
            weights.append(self.evaluation_weights['nutrition'])
        
        if completeness and completeness.get('score'):
            scores.append(completeness['score'])
            weights.append(self.evaluation_weights['completeness'])
        
        if complexity_alignment and complexity_alignment.get('score'):
            scores.append(complexity_alignment['score'])
            weights.append(self.evaluation_weights['complexity_alignment'])
        
        if not scores:
            return 5.0  # Neutral score if no evaluations
        
        # Calculate weighted average
        weighted_sum = sum(score * weight for score, weight in zip(scores, weights))
        total_weight = sum(weights)
        
        overall = round(weighted_sum / total_weight, 1)
        print(f"⭐ Weighted calculation: {overall} from {len(scores)} metrics")
        
        return overall
    
    def _generate_improvement_recommendations(self, recipe: Dict, creativity: Dict, 
                                           practicality: Dict, nutrition: Dict, 
                                           completeness: Dict, complexity_alignment: Dict, complexity: str) -> List[str]:
        """Generate specific recommendations for recipe improvement"""
        
        print(f"⭐ Generating improvement recommendations for {complexity} complexity...")
        
        recommendations = []
        
        # Collect improvement areas from each evaluation
        for evaluation in [creativity, practicality, nutrition, completeness, complexity_alignment]:
            if evaluation and evaluation.get('areas_for_improvement'):
                recommendations.extend(evaluation['areas_for_improvement'][:2])  # Top 2 from each
        
        # Remove duplicates and limit
        unique_recommendations = list(dict.fromkeys(recommendations))
        
        # Prioritize based on scores (lower scores = higher priority)
        if complexity_alignment and complexity_alignment.get('score', 10) < 6:
            unique_recommendations.insert(0, f"Better align recipe with {complexity} complexity expectations")
        
        if creativity and creativity.get('score', 10) < 6:
            unique_recommendations.insert(0, f"Add more creative elements appropriate for {complexity} level")
        
        if practicality and practicality.get('score', 10) < 6:
            unique_recommendations.insert(0, f"Improve practicality for {complexity} complexity level")
        
        final_recommendations = unique_recommendations[:5]  # Top 5 recommendations
        print(f"⭐ Generated {len(final_recommendations)} recommendations")
        
        return final_recommendations
    
    def _determine_quality_verdict(self, overall_score: float) -> str:
        """Determine quality verdict based on score"""
        
        if overall_score >= self.quality_thresholds['excellent_quality']:
            return "excellent"
        elif overall_score >= self.quality_thresholds['good_quality']:
            return "good"
        elif overall_score >= self.quality_thresholds['minimum_acceptable']:
            return "acceptable"
        else:
            return "needs_improvement"
    
    def _get_quality_level(self, score: float) -> str:
        """Get descriptive quality level"""
        
        if score >= 9.0:
            return "Exceptional"
        elif score >= 7.5:
            return "Very Good"
        elif score >= 6.0:
            return "Good"
        elif score >= 4.0:
            return "Average"
        else:
            return "Needs Work"
    
    def _calculate_confidence(self, *evaluations) -> str:
        """Calculate overall confidence in the evaluation"""
        
        confidences = []
        for eval_result in evaluations:
            if eval_result and eval_result.get('confidence'):
                confidence_val = {'low': 1, 'medium': 2, 'high': 3}.get(eval_result['confidence'], 2)
                confidences.append(confidence_val)
        
        if not confidences:
            return 'medium'
        
        avg_confidence = statistics.mean(confidences)
        
        if avg_confidence >= 2.7:
            return 'high'
        elif avg_confidence >= 1.7:
            return 'medium'
        else:
            return 'low'
    
    def _extract_evaluation_json(self, response_text: str) -> Dict:
        """Extract JSON from evaluation response"""
        
        try:
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            print(f"Failed to extract evaluation JSON: {str(e)}")
        
        return {'score': 5.0, 'confidence': 'low', 'strengths': [], 'areas_for_improvement': []}
    
    def _fallback_complexity_score(self, recipe: Dict, complexity: str) -> Dict:
        """Fallback complexity alignment evaluation"""
        
        score = 5.0
        
        # Simple heuristics based on complexity
        ingredient_count = len(recipe.get('ingredients', []))
        instruction_count = len(recipe.get('instructions', []))
        
        if complexity == "Simple":
            if ingredient_count <= 10 and instruction_count <= 8:
                score += 1
        elif complexity == "Gourmet":
            if ingredient_count >= 12 and instruction_count >= 10:
                score += 1
        
        return {
            'score': score,
            'alignment_analysis': f'Basic heuristic evaluation for {complexity} complexity',
            'strengths': [f'Recipe structure suits {complexity} level'],
            'areas_for_improvement': [f'Verify alignment with {complexity} complexity standards'],
            'confidence': 'low'
        }
    
    def _fallback_creativity_score(self, recipe: Dict) -> Dict:
        """Fallback creativity evaluation"""
        
        score = 5.0
        
        # Simple heuristics
        if recipe.get('enhancements_made'):
            score += 1
        if len(recipe.get('ingredients', [])) > 8:
            score += 0.5
        
        return {
            'score': score,
            'strengths': ['Recipe has been enhanced'],
            'areas_for_improvement': ['Could add more creative elements'],
            'confidence': 'low'
        }
    
    def _fallback_practicality_score(self, recipe: Dict) -> Dict:
        """Fallback practicality evaluation"""
        
        score = 6.0
        
        # Simple checks
        if recipe.get('difficulty', '').lower() == 'simple':
            score += 1
        if len(recipe.get('ingredients', [])) <= 10:
            score += 0.5
        
        return {
            'score': score,
            'strengths': ['Reasonable ingredient count'],
            'areas_for_improvement': ['Verify ingredient accessibility'],
            'confidence': 'low'
        }
    
    def _create_fallback_evaluation(self, recipe: Dict, complexity: str) -> Dict:
        """Create fallback evaluation when main evaluation fails"""
        
        print(f"⚠️ Using fallback evaluation for {complexity} complexity")
        
        return {
            'score': 5.0,
            'quality_verdict': 'needs_improvement',
            'detailed_scores': {
                'creativity': {'score': 5.0, 'confidence': 'low'},
                'practicality': {'score': 5.0, 'confidence': 'low'},
                'nutrition': {'score': 5.0, 'confidence': 'low'},
                'completeness': {'score': 5.0, 'confidence': 'low'},
                'complexity_alignment': {'score': 5.0, 'confidence': 'low'}
            },
            'recommendations': [f'Evaluation failed - manual review needed for {complexity} complexity'],
            'meets_threshold': False,
            'quality_level': 'Unknown',
            'confidence': 'low',
            'evaluation_error': True,
            'evaluation_timestamp': self._get_timestamp(),
            'complexity_evaluated': complexity
        }
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()

# Test the quality evaluator
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    # Test recipes with different complexities
    test_recipes = [
        {
            'title': 'Simple Grilled Cheese',
            'ingredients': ['2 slices bread', '1 slice cheese', '1 tbsp butter'],
            'instructions': ['Butter bread', 'Add cheese', 'Grill until golden'],
            'complexity': 'Simple'
        },
        {
            'title': 'Beef Wellington',
            'ingredients': ['2 lb beef tenderloin', 'puff pastry', 'mushroom duxelles', 'prosciutto'],
            'instructions': ['Sear beef', 'Prepare duxelles', 'Wrap in pastry', 'Bake'],
            'complexity': 'Gourmet'
        }
    ]
    
    evaluator = QualityEvaluator()
    
    for recipe in test_recipes:
        complexity = recipe.pop('complexity')
        print(f"\n{'='*50}")
        print(f"Testing {complexity} Recipe: {recipe['title']}")
        print(f"{'='*50}")
        
        evaluation = evaluator.evaluate_recipe(recipe, None, None, complexity)
        
        print(f"\n✅ Quality Evaluation Complete!")
        print(f"Overall Score: {evaluation['score']}/10")
        print(f"Quality Level: {evaluation['quality_level']}")
        print(f"Complexity Evaluated: {evaluation['complexity_evaluated']}")
        print(f"Verdict: {evaluation['quality_verdict']}")
        print(f"Meets Threshold: {evaluation['meets_threshold']}")
        print(f"Confidence: {evaluation['confidence']}")
        
        if evaluation.get('recommendations'):
            print(f"\n📋 Top Recommendations:")
            for rec in evaluation['recommendations'][:3]:
                print(f"  • {rec}")
        
        print(f"\n📊 Detailed Scores:")
        for category, details in evaluation['detailed_scores'].items():
            if details:
                print(f"  {category.title()}: {details.get('score', 'N/A')}/10")
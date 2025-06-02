# main.py - Simple queue-based optimization without async complexity
import os
import time
import threading
import uuid
import traceback
from typing import Dict, List
from queue import Queue, Empty
from dataclasses import dataclass
from enum import Enum

class TaskStatus(Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class RecipeTask:
    task_id: str
    user_request: str
    complexity: str
    status: TaskStatus
    created_at: float
    progress: Dict
    result: Dict = None
    error: str = None

class SimpleRecipeQueue:
    def __init__(self, max_concurrent=2):
        self.tasks = {}
        self.queue = Queue(maxsize=50)
        self.processing_count = 0
        self.max_concurrent = max_concurrent
        self.lock = threading.Lock()
        self.worker_thread = None
        self.running = True
        
        # Start worker thread
        self._start_worker()
        
    def add_task(self, user_request: str, complexity: str) -> str:
        task_id = str(uuid.uuid4())
        task = RecipeTask(
            task_id=task_id,
            user_request=user_request,
            complexity=complexity,
            status=TaskStatus.QUEUED,
            created_at=time.time(),
            progress={"step": "queued", "message": "Request queued for processing"}
        )
        
        with self.lock:
            self.tasks[task_id] = task
            
        try:
            self.queue.put(task, timeout=1)
            return task_id
        except:
            # Queue full
            task.status = TaskStatus.FAILED
            task.error = "Queue is full, please try again later"
            return task_id
    
    def get_task_status(self, task_id: str) -> Dict:
        with self.lock:
            task = self.tasks.get(task_id)
            
        if not task:
            return {"error": "Task not found"}
        
        queue_position = None
        if task.status == TaskStatus.QUEUED:
            queue_position = self._get_queue_position(task_id)
        
        return {
            "task_id": task.task_id,
            "status": task.status.value,
            "progress": task.progress,
            "result": task.result,
            "error": task.error,
            "queue_position": queue_position
        }
    
    def _get_queue_position(self, task_id: str) -> int:
        position = 1
        with self.lock:
            target_task = self.tasks.get(task_id)
            if not target_task:
                return 0
                
            for task in self.tasks.values():
                if (task.status == TaskStatus.QUEUED and 
                    task.created_at < target_task.created_at):
                    position += 1
        return position
    
    def _start_worker(self):
        def worker():
            print("🔄 Queue worker thread started")
            while self.running:
                try:
                    # Check if we can process more tasks
                    with self.lock:
                        current_processing = self.processing_count
                    
                    if current_processing >= self.max_concurrent:
                        time.sleep(1)
                        continue
                    
                    # Get next task
                    try:
                        task = self.queue.get(timeout=1)
                        print(f"🎯 Worker got task: {task.task_id}")
                    except Empty:
                        continue
                    
                    # Process in separate thread to maintain concurrency
                    process_thread = threading.Thread(
                        target=self._process_task, 
                        args=(task,),
                        daemon=True
                    )
                    process_thread.start()
                    
                except Exception as e:
                    print(f"❌ Worker error: {str(e)}")
                    traceback.print_exc()
                    time.sleep(1)
            
            print("🔄 Queue worker thread stopped")
        
        self.worker_thread = threading.Thread(target=worker, daemon=True)
        self.worker_thread.start()
        print("✅ Queue worker started")
    
    def _process_task(self, task: RecipeTask):
        """Process individual recipe generation task"""
        try:
            with self.lock:
                self.processing_count += 1
                task.status = TaskStatus.PROCESSING
                task.progress = {"step": "processing", "message": "Starting recipe generation..."}
            
            print(f"🎯 Processing task: {task.task_id} for '{task.user_request}'")
            
            # Import here to avoid circular imports
            try:
                from recipe_generator import RecipeGenerator
                from recipe_enhancer import RecipeEnhancer
                from web_researcher import WebResearcher
                from nutrition_analyst import NutritionAnalyst
                from quality_evaluator import QualityEvaluator
                print(f"✅ Imported all agents for task {task.task_id}")
            except ImportError as e:
                print(f"❌ Failed to import agents: {str(e)}")
                raise e
            
            # Initialize agents (could be cached globally)
            generator = RecipeGenerator()
            enhancer = RecipeEnhancer()
            researcher = WebResearcher()
            nutrition_analyst = NutritionAnalyst()
            quality_evaluator = QualityEvaluator()
            print(f"✅ Initialized all agents for task {task.task_id}")
            
            # Run pipeline
            result = self._run_pipeline(
                task, generator, enhancer, researcher, 
                nutrition_analyst, quality_evaluator
            )
            
            with self.lock:
                task.status = TaskStatus.COMPLETED
                task.result = result
                task.progress = {"step": "completed", "message": "Recipe generation complete!"}
            
            print(f"✅ Task completed: {task.task_id} - {result['recipe']['title']}")
            
        except Exception as e:
            print(f"❌ Task failed: {task.task_id} - {str(e)}")
            traceback.print_exc()
            
            with self.lock:
                task.status = TaskStatus.FAILED
                task.error = str(e)
                task.progress = {"step": "failed", "message": f"Generation failed: {str(e)}"}
            
        finally:
            with self.lock:
                self.processing_count -= 1
            print(f"🔄 Processing count after task {task.task_id}: {self.processing_count}")
    
    def _run_pipeline(self, task, generator, enhancer, researcher, nutrition_analyst, quality_evaluator):
        """Run the recipe generation pipeline"""
        
        start_time = time.time()
        
        # Step 1: Generate base recipe
        task.progress = {"step": "generating", "message": "🤖 Creating base recipe..."}
        
        base_recipe = generator.create_recipe(task.user_request, task.complexity)
        
        if not base_recipe.get('success'):
            raise Exception(base_recipe.get('error', 'Recipe generation failed'))
        
        base_recipe['requested_complexity'] = task.complexity
        
        # Step 2: Research inspiration (with timeout)
        task.progress = {"step": "researching", "message": "🔍 Finding cooking inspiration..."}
        
        inspiration_data = None
        try:
            inspiration_data = researcher.find_inspiration(
                base_recipe.get('title', ''), 
                base_recipe.get('meal_type')
            )
        except Exception as e:
            print(f"⚠️ Research failed: {str(e)}")
            inspiration_data = None
        
        # Step 3: Enhance recipe
        task.progress = {"step": "enhancing", "message": "📝 Adding creative improvements..."}
        
        enhanced_recipe = base_recipe
        try:
            # Use the fixed method signature with complexity parameter
            enhanced_recipe = enhancer.enhance_recipe(base_recipe, inspiration_data, task.complexity)
        except Exception as e:
            print(f"⚠️ Enhancement failed: {str(e)}")
            enhanced_recipe = base_recipe
        
        # Step 4: Analyze nutrition
        task.progress = {"step": "analyzing", "message": "🥗 Calculating nutrition..."}
        
        nutrition_data = None
        try:
            nutrition_data = nutrition_analyst.analyze_nutrition(enhanced_recipe)
        except Exception as e:
            print(f"⚠️ Nutrition analysis failed: {str(e)}")
            nutrition_data = self._create_fallback_nutrition(enhanced_recipe)
        
        # Step 5: Evaluate quality
        task.progress = {"step": "evaluating", "message": "⭐ Scoring recipe quality..."}
        
        quality_data = None
        try:
            quality_data = quality_evaluator.evaluate_recipe(
                enhanced_recipe, 
                nutrition_data, 
                inspiration_data,
                task.complexity
            )
        except Exception as e:
            print(f"⚠️ Quality evaluation failed: {str(e)}")
            quality_data = self._create_fallback_quality()
        
        # Final result
        total_time = int(time.time() - start_time)
        
        return {
            'success': True,
            'recipe': enhanced_recipe,
            'nutrition': nutrition_data,
            'quality': quality_data,
            'iterations': 1,
            'complexity_requested': task.complexity,
            'generation_time': total_time,
            'inspiration_used': inspiration_data is not None
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
        estimate.update({'fiber': 4, 'sugar': 8, 'sodium': 400})
        
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
    
    def shutdown(self):
        """Shutdown the queue worker"""
        self.running = False

class RecipeAgentTeam:
    def __init__(self):
        """Initialize the recipe agent team with simple queue management"""
        
        print("🚀 Initializing Recipe Agent Team with queue management...")
        
        # Initialize queue
        self.queue = SimpleRecipeQueue(max_concurrent=2)  # Conservative limit
        
        print("✅ Recipe Agent Team initialized successfully!")
    
    def queue_recipe_generation(self, user_request: str, complexity: str = "Medium") -> str:
        """Queue a recipe generation request and return task ID"""
        task_id = self.queue.add_task(user_request, complexity)
        print(f"🎯 Recipe queued: {task_id} for '{user_request}' ({complexity})")
        return task_id
    
    def get_recipe_status(self, task_id: str) -> Dict:
        """Get status of queued/processing recipe"""
        return self.queue.get_task_status(task_id)
    
    def generate_recipe(self, user_request: str, complexity: str = "Medium") -> Dict:
        """
        Legacy synchronous method for backward compatibility
        """
        print(f"🎯 Synchronous recipe generation for: '{user_request}' (Complexity: {complexity})")
        
        # For immediate/synchronous requests, create a simple task and process directly
        task = RecipeTask(
            task_id="sync_" + str(uuid.uuid4()),
            user_request=user_request,
            complexity=complexity,
            status=TaskStatus.PROCESSING,
            created_at=time.time(),
            progress={"step": "processing", "message": "Processing recipe synchronously..."}
        )
        
        try:
            # Import agents
            from recipe_generator import RecipeGenerator
            from recipe_enhancer import RecipeEnhancer
            from web_researcher import WebResearcher
            from nutrition_analyst import NutritionAnalyst
            from quality_evaluator import QualityEvaluator
            
            generator = RecipeGenerator()
            enhancer = RecipeEnhancer()
            researcher = WebResearcher()
            nutrition_analyst = NutritionAnalyst()
            quality_evaluator = QualityEvaluator()
            
            # Process directly
            result = self.queue._run_pipeline(
                task, generator, enhancer, researcher, 
                nutrition_analyst, quality_evaluator
            )
            
            return result
            
        except Exception as e:
            print(f"❌ Synchronous generation failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'generation_time': int(time.time() - task.created_at)
            }

# Global instance - simple singleton pattern
_recipe_team_instance = None

def get_recipe_team():
    global _recipe_team_instance
    if _recipe_team_instance is None:
        _recipe_team_instance = RecipeAgentTeam()
    return _recipe_team_instance

# Test the system
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    # Test the queue system
    team = get_recipe_team()
    
    print(f"\n🧪 Testing queue system...")
    
    # Queue a recipe
    task_id = team.queue_recipe_generation("healthy chicken stir fry", "Medium")
    print(f"Task ID: {task_id}")
    
    # Poll status
    for i in range(30):  # Poll for up to 30 seconds
        status = team.get_recipe_status(task_id)
        print(f"Status: {status['status']} - {status['progress']['message']}")
        
        if status['status'] in ['completed', 'failed']:
            if status['status'] == 'completed':
                print(f"✅ Recipe completed: {status['result']['recipe']['title']}")
            else:
                print(f"❌ Recipe failed: {status['error']}")
            break
            
        time.sleep(2)
    
    print(f"\n📊 Test complete!")
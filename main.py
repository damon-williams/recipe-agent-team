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
            print("🔄 Queue worker thread starting...")
            
            # Add startup delay to ensure all imports are ready
            time.sleep(2)
            
            while self.running:
                try:
                    # Check if we can process more tasks
                    with self.lock:
                        current_processing = self.processing_count
                    
                    if current_processing >= self.max_concurrent:
                        time.sleep(1)
                        continue
                    
                    # Get next task with shorter timeout to avoid blocking
                    try:
                        task = self.queue.get(timeout=0.5)  # Shorter timeout
                        print(f"🎯 Worker got task: {task.task_id}")
                    except Empty:
                        continue
                    
                    # Process in separate thread to maintain concurrency
                    try:
                        process_thread = threading.Thread(
                            target=self._process_task_safe, 
                            args=(task,),
                            daemon=True,
                            name=f"RecipeProcessor-{task.task_id[:8]}"
                        )
                        process_thread.start()
                        print(f"🚀 Started processing thread for {task.task_id}")
                    except Exception as thread_error:
                        print(f"❌ Failed to start processing thread: {str(thread_error)}")
                        # Mark task as failed
                        with self.lock:
                            task.status = TaskStatus.FAILED
                            task.error = f"Failed to start processing: {str(thread_error)}"
                    
                except Exception as e:
                    print(f"❌ Worker loop error: {str(e)}")
                    print(traceback.format_exc())
                    # Don't crash the worker, just wait and continue
                    time.sleep(5)
            
            print("🔄 Queue worker thread stopped")
        
        try:
            self.worker_thread = threading.Thread(target=worker, daemon=True, name="QueueWorker")
            self.worker_thread.start()
            
            # Verify the thread started successfully
            time.sleep(0.1)
            if self.worker_thread.is_alive():
                print("✅ Queue worker started successfully")
            else:
                print("❌ Queue worker failed to start")
                
        except Exception as e:
            print(f"❌ Failed to create worker thread: {str(e)}")
            print(traceback.format_exc())

    def _process_task_safe(self, task: RecipeTask):
        """Ultra-safe task processing that never crashes the worker"""
        
        try:
            with self.lock:
                self.processing_count += 1
                task.status = TaskStatus.PROCESSING
                task.progress = {"step": "processing", "message": "Starting recipe generation..."}
            
            print(f"🎯 Processing task: {task.task_id} for '{task.user_request}'")
            
            # Try to run the full pipeline
            result = self._run_minimal_pipeline(task)
            
            with self.lock:
                task.status = TaskStatus.COMPLETED
                task.result = result
                task.progress = {"step": "completed", "message": "Recipe generation complete!"}
            
            print(f"✅ Task completed: {task.task_id}")
            
        except Exception as e:
            print(f"❌ Task processing failed: {task.task_id} - {str(e)}")
            print(traceback.format_exc())
            
            # Always mark as failed rather than crash
            with self.lock:
                task.status = TaskStatus.FAILED
                task.error = str(e)
                task.progress = {"step": "failed", "message": f"Processing failed: {str(e)}"}
        
        finally:
            # ALWAYS decrement the processing count
            with self.lock:
                self.processing_count -= 1
            print(f"🔄 Processing count after task {task.task_id}: {self.processing_count}")

    def _run_minimal_pipeline(self, task):
        """Minimal pipeline that works even if agents fail to import"""
        
        start_time = time.time()
        
        # Try to use agents, but fall back to basic generation if imports fail
        try:
            # Only import what we absolutely need
            print("🔄 Attempting to import recipe generator...")
            
            # Try importing in the safest way possible
            import sys
            import os
            
            # Ensure agents directory is in path
            agents_path = os.path.join(os.path.dirname(__file__), 'agents')
            if agents_path not in sys.path:
                sys.path.insert(0, agents_path)
            
            # Try to import and use RecipeGenerator
            from recipe_generator import RecipeGenerator
            generator = RecipeGenerator()
            
            print("✅ Generator imported successfully")
            
            # Generate base recipe
            task.progress = {"step": "generating", "message": "🤖 Creating recipe..."}
            base_recipe = generator.create_recipe(task.user_request, task.complexity)
            
            if not base_recipe.get('success'):
                raise Exception("Generator failed")
            
            print(f"✅ Generated: {base_recipe.get('title', 'Unknown')}")
            
            # Try enhancement if possible
            try:
                from recipe_enhancer import RecipeEnhancer
                enhancer = RecipeEnhancer()
                enhanced_recipe = enhancer.enhance_recipe(base_recipe, None, task.complexity)
                print("✅ Enhancement successful")
            except Exception as e:
                print(f"⚠️ Enhancement failed, using base recipe: {str(e)}")
                enhanced_recipe = base_recipe
            
            # Create basic result
            result = {
                'success': True,
                'recipe': enhanced_recipe,
                'nutrition': self._create_fallback_nutrition(enhanced_recipe),
                'quality': self._create_fallback_quality(),
                'iterations': 1,
                'complexity_requested': task.complexity,
                'generation_time': int(time.time() - start_time),
                'inspiration_used': False
            }
            
            return result
            
        except Exception as e:
            print(f"❌ Full pipeline failed: {str(e)}")
            print(traceback.format_exc())
            
            # Ultimate fallback - create a basic recipe without any agents
            return {
                'success': True,
                'recipe': {
                    'title': f"Basic {task.user_request.title()}",
                    'description': f"A simple {task.user_request} recipe",
                    'ingredients': [
                        f"Main ingredients for {task.user_request}",
                        "Seasonings to taste"
                    ],
                    'instructions': [
                        f"Prepare the {task.user_request} ingredients",
                        "Cook according to standard methods",
                        "Season and serve"
                    ],
                    'prep_time': "15 minutes",
                    'cook_time': "20 minutes",
                    'total_time': "35 minutes",
                    'servings': "4",
                    'difficulty': task.complexity,
                    'tags': [task.user_request.lower(), "basic"],
                    'cuisine_type': "Various",
                    'meal_type': "dinner",
                    'success': True
                },
                'nutrition': self._create_fallback_nutrition({}),
                'quality': self._create_fallback_quality(),
                'iterations': 1,
                'complexity_requested': task.complexity,
                'generation_time': int(time.time() - start_time),
                'inspiration_used': False,
                'fallback_used': True,
                'error_handled': str(e)
            }
    
    def _process_task(self, task: RecipeTask):
        """Process individual recipe generation task with robust error handling"""
        thread_name = threading.current_thread().name
        
        try:
            with self.lock:
                self.processing_count += 1
                task.status = TaskStatus.PROCESSING
                task.progress = {"step": "processing", "message": "Starting recipe generation..."}
            
            print(f"🎯 [{thread_name}] Processing task: {task.task_id} for '{task.user_request}'")
            
            # Pre-import all agents with individual error handling
            agents = {}
            agent_classes = {
                'generator': 'recipe_generator.RecipeGenerator',
                'enhancer': 'recipe_enhancer.RecipeEnhancer', 
                'researcher': 'web_researcher.WebResearcher',
                'nutrition_analyst': 'nutrition_analyst.NutritionAnalyst',
                'quality_evaluator': 'quality_evaluator.QualityEvaluator'
            }
            
            for agent_name, import_path in agent_classes.items():
                try:
                    module_name, class_name = import_path.split('.')
                    module = __import__(module_name, fromlist=[class_name])
                    agent_class = getattr(module, class_name)
                    agents[agent_name] = agent_class()
                    print(f"✅ [{thread_name}] Imported {agent_name}")
                except Exception as e:
                    print(f"❌ [{thread_name}] Failed to import {agent_name}: {str(e)}")
                    # Continue without this agent - use fallbacks
                    agents[agent_name] = None
            
            # Run pipeline with available agents
            result = self._run_robust_pipeline(task, agents)
            
            with self.lock:
                task.status = TaskStatus.COMPLETED
                task.result = result
                task.progress = {"step": "completed", "message": "Recipe generation complete!"}
            
            print(f"✅ [{thread_name}] Task completed: {task.task_id}")
            
        except Exception as e:
            print(f"❌ [{thread_name}] Task failed: {task.task_id} - {str(e)}")
            traceback.print_exc()
            
            with self.lock:
                task.status = TaskStatus.FAILED
                task.error = str(e)
                task.progress = {"step": "failed", "message": f"Generation failed: {str(e)}"}
            
        finally:
            with self.lock:
                self.processing_count -= 1
            print(f"🔄 [{thread_name}] Processing count after task {task.task_id}: {self.processing_count}")

    def _run_robust_pipeline(self, task, agents):
        """Run the recipe generation pipeline with graceful agent failures"""
        
        start_time = time.time()
        
        # Step 1: Generate base recipe (REQUIRED)
        task.progress = {"step": "generating", "message": "🤖 Creating base recipe..."}
        
        if agents['generator']:
            base_recipe = agents['generator'].create_recipe(task.user_request, task.complexity)
        else:
            # Fallback: create a basic recipe structure
            base_recipe = self._create_fallback_recipe(task.user_request, task.complexity)
        
        if not base_recipe.get('success'):
            raise Exception(base_recipe.get('error', 'Recipe generation failed'))
        
        base_recipe['requested_complexity'] = task.complexity
        
        # Step 2: Research inspiration (OPTIONAL)
        task.progress = {"step": "researching", "message": "🔍 Finding cooking inspiration..."}
        
        inspiration_data = None
        if agents['researcher']:
            try:
                inspiration_data = agents['researcher'].find_inspiration(
                    base_recipe.get('title', ''), 
                    base_recipe.get('meal_type')
                )
            except Exception as e:
                print(f"⚠️ Research failed: {str(e)}")
                inspiration_data = None
        
        # Step 3: Enhance recipe (OPTIONAL)
        task.progress = {"step": "enhancing", "message": "📝 Adding creative improvements..."}
        
        enhanced_recipe = base_recipe
        if agents['enhancer']:
            try:
                enhanced_recipe = agents['enhancer'].enhance_recipe(base_recipe, inspiration_data, task.complexity)
            except Exception as e:
                print(f"⚠️ Enhancement failed: {str(e)}")
                enhanced_recipe = base_recipe
        
        # Step 4: Analyze nutrition (OPTIONAL)
        task.progress = {"step": "analyzing", "message": "🥗 Calculating nutrition..."}
        
        nutrition_data = None
        if agents['nutrition_analyst']:
            try:
                nutrition_data = agents['nutrition_analyst'].analyze_nutrition(enhanced_recipe)
            except Exception as e:
                print(f"⚠️ Nutrition analysis failed: {str(e)}")
                nutrition_data = self._create_fallback_nutrition(enhanced_recipe)
        else:
            nutrition_data = self._create_fallback_nutrition(enhanced_recipe)
        
        # Step 5: Evaluate quality (OPTIONAL)
        task.progress = {"step": "evaluating", "message": "⭐ Scoring recipe quality..."}
        
        quality_data = None
        if agents['quality_evaluator']:
            try:
                quality_data = agents['quality_evaluator'].evaluate_recipe(
                    enhanced_recipe, 
                    nutrition_data, 
                    inspiration_data,
                    task.complexity
                )
            except Exception as e:
                print(f"⚠️ Quality evaluation failed: {str(e)}")
                quality_data = self._create_fallback_quality()
        else:
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
            'inspiration_used': inspiration_data is not None,
            'agents_used': [name for name, agent in agents.items() if agent is not None]
        }

    def _create_fallback_recipe(self, user_request: str, complexity: str) -> Dict:
        """Create a basic recipe when generator fails"""
        return {
            'success': True,
            'title': f"Basic {user_request.title()}",
            'description': f"A simple {user_request} recipe",
            'ingredients': ["Main ingredients for " + user_request],
            'instructions': ["Basic cooking instructions"],
            'prep_time': "15 minutes",
            'cook_time': "20 minutes", 
            'total_time': "35 minutes",
            'servings': "4",
            'difficulty': complexity,
            'tags': [user_request.lower(), "simple"],
            'cuisine_type': "Various",
            'meal_type': "dinner"
        }
    
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
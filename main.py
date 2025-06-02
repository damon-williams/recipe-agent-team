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
import logging
import signal
import atexit

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
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
        self.startup_complete = False
        
        # ADD: Task retention settings
        self.task_retention_time = 1800  # Keep completed tasks for 30 minutes
        self.last_cleanup = time.time()
        self.cleanup_interval = 600  # Run cleanup every 10 minutes
        
        logger.info(f"🚀 Initializing queue with max_concurrent={max_concurrent}")
        logger.info(f"🕐 Task retention: {self.task_retention_time}s, cleanup interval: {self.cleanup_interval}s")
        
        # Setup graceful shutdown handlers
        self._setup_graceful_shutdown()
        
        # DON'T start worker immediately - wait for first request to avoid startup race condition
        logger.info("⏰ Queue initialized, worker will start on first request")
        
    def _ensure_worker_started(self):
        """Ensure worker is started when needed (lazy startup to avoid race conditions)"""
        if not self.startup_complete:
            with self.lock:
                if not self.startup_complete:  # Double-check locking pattern
                    self._start_worker_delayed()
                    self.startup_complete = True
    
    def _start_worker_delayed(self):
        """Start worker with better timing after app is fully loaded"""
        
        def worker():
            logger.info("🔄 Queue worker thread starting (delayed startup)...")
            
            # Longer delay to ensure all imports and app initialization are complete
            time.sleep(5)
            
            while self.running:
                try:
                    # Check if we can process more tasks
                    with self.lock:
                        current_processing = self.processing_count
                    
                    if current_processing >= self.max_concurrent:
                        logger.debug(f"🔄 At max capacity ({current_processing}/{self.max_concurrent})")
                        time.sleep(1)
                        continue
                    
                    # Get next task
                    try:
                        task = self.queue.get(timeout=1)
                        logger.info(f"🎯 Worker got task: {task.task_id}")
                    except Empty:
                        continue
                    
                    # Process in separate thread to maintain concurrency
                    try:
                        process_thread = threading.Thread(
                            target=self._process_task_safe, 
                            args=(task,),
                            daemon=False,  # Non-daemon so gthread won't kill it
                            name=f"RecipeProcessor-{task.task_id[:8]}"
                        )
                        process_thread.start()
                        logger.info(f"🚀 Started processing thread for {task.task_id}")
                    except Exception as thread_error:
                        logger.error(f"❌ Failed to start processing thread: {str(thread_error)}")
                        # Mark task as failed if we can't start processing thread
                        with self.lock:
                            task.status = TaskStatus.FAILED
                            task.error = f"Failed to start processing: {str(thread_error)}"
                    
                except Exception as e:
                    logger.error(f"❌ Worker loop error: {str(e)}")
                    logger.error(traceback.format_exc())
                    # Don't crash the worker, just wait and continue
                    time.sleep(5)
            
            logger.info("🔄 Queue worker thread stopped")
        
        try:
            self.worker_thread = threading.Thread(
                target=worker, 
                daemon=False,  # Non-daemon thread so it survives gthread worker
                name="QueueWorker"
            )
            self.worker_thread.start()
            
            # Verify the thread started successfully
            time.sleep(0.1)
            if self.worker_thread.is_alive():
                logger.info("✅ Delayed queue worker started successfully")
            else:
                logger.error("❌ Delayed queue worker failed to start")
                
        except Exception as e:
            logger.error(f"❌ Failed to create delayed worker thread: {str(e)}")
            logger.error(traceback.format_exc())
    

    def _cleanup_old_tasks(self):
        """Clean up old completed/failed tasks to prevent memory leaks"""
        
        current_time = time.time()
        
        # Only run cleanup periodically
        if current_time - self.last_cleanup < self.cleanup_interval:
            return
        
        try:
            lock_acquired = self.lock.acquire(timeout=2.0)
            if not lock_acquired:
                logger.warning("⚠️ Could not acquire lock for task cleanup")
                return
            
            try:
                tasks_to_remove = []
                
                for task_id, task in self.tasks.items():
                    # CRITICAL: NEVER clean up processing or queued tasks
                    if task.status in [TaskStatus.PROCESSING, TaskStatus.QUEUED]:
                        continue  # Skip active tasks completely
                    
                    # Only clean up completed or failed tasks (keep processing/queued tasks)
                    if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                        # Calculate how long ago the task finished (not when it was created)
                        task_completion_time = getattr(task, 'completion_time', task.created_at)
                        task_age_since_completion = current_time - task_completion_time
                        
                        if task_age_since_completion > self.task_retention_time:
                            tasks_to_remove.append(task_id)
                            logger.debug(f"🧹 Marking task {task_id} for cleanup (age: {task_age_since_completion:.1f}s)")
                
                # Remove old tasks
                removed_count = 0
                for task_id in tasks_to_remove:
                    if task_id in self.tasks:
                        del self.tasks[task_id]
                        removed_count += 1
                        logger.debug(f"🧹 Cleaned up old task: {task_id}")
                
                if removed_count > 0:
                    logger.info(f"🧹 Cleaned up {removed_count} old tasks. Remaining: {len(self.tasks)}")
                
                self.last_cleanup = current_time
                
            finally:
                self.lock.release()
                
        except Exception as e:
            logger.error(f"❌ Task cleanup failed: {str(e)}")
            
    def add_task(self, user_request: str, complexity: str) -> str:
        """Add task to queue with timeout protection"""
        
        # Ensure worker is running before adding tasks (lazy startup)
        self._ensure_worker_started()
        
        task_id = str(uuid.uuid4())
        logger.info(f"🎯 Creating task {task_id} for '{user_request}' ({complexity})")
        
        task = RecipeTask(
            task_id=task_id,
            user_request=user_request,
            complexity=complexity,
            status=TaskStatus.QUEUED,
            created_at=time.time(),
            progress={"step": "queued", "message": "Request queued for processing"}
        )
        
        try:
            # SAFE: Use timeout on lock acquisition to prevent deadlock
            lock_acquired = self.lock.acquire(timeout=5.0)  # 5 second timeout
            if not lock_acquired:
                logger.error(f"❌ Lock timeout adding task {task_id}")
                task.status = TaskStatus.FAILED
                task.error = "System busy, please try again"
                # Store failed task without lock
                self.tasks[task_id] = task
                return task_id
            
            try:
                # Store task while holding lock
                self.tasks[task_id] = task
                task_count = len(self.tasks)
                logger.info(f"✅ Task {task_id} stored. Total tasks: {task_count}")
            finally:
                self.lock.release()
            
            # Add to processing queue (this is thread-safe on its own)
            try:
                self.queue.put(task, timeout=1)
                logger.info(f"✅ Task {task_id} queued. Queue size: {self.queue.qsize()}")
            except:
                logger.error(f"❌ Queue full for task {task_id}")
                # Mark as failed but keep in tasks dict
                with self.lock.acquire(timeout=2.0):
                    if self.lock.acquire(timeout=2.0):
                        task.status = TaskStatus.FAILED
                        task.error = "Queue full"
                        self.lock.release()
            
            return task_id
            
        except Exception as e:
            logger.error(f"❌ Exception adding task {task_id}: {str(e)}")
            return task_id

    def get_task_status(self, task_id: str) -> Dict:
        """Get status with cleanup management and extended retention"""
        
        # Run periodic cleanup before checking status
        self._cleanup_old_tasks()
        
        try:
            # SAFE: Use timeout on lock acquisition
            lock_acquired = self.lock.acquire(timeout=3.0)
            if not lock_acquired:
                logger.error(f"❌ Lock timeout getting status for {task_id}")
                return {"error": "System busy, please try again"}
            
            try:
                task = self.tasks.get(task_id)
                if not task:
                    logger.warning(f"⚠️ Task not found: {task_id}")
                    return {"error": "Task not found"}
                
                # Copy task data while holding lock
                task_data = {
                    "task_id": task.task_id,
                    "status": task.status.value,
                    "progress": task.progress.copy() if task.progress else {},
                    "result": task.result,
                    "error": task.error,
                    "queue_position": None
                }
                
                # Calculate queue position if needed
                if task.status == TaskStatus.QUEUED:
                    queue_position = 1
                    for other_task in self.tasks.values():
                        if (other_task.status == TaskStatus.QUEUED and 
                            other_task.created_at < task.created_at):
                            queue_position += 1
                    task_data["queue_position"] = queue_position
                
                # ADD: Debug info for completed tasks
                if task.status == TaskStatus.COMPLETED:
                    completion_time = getattr(task, 'completion_time', task.created_at)
                    age_since_completion = time.time() - completion_time
                    logger.debug(f"📊 Completed task {task_id} age: {age_since_completion:.1f}s (retention: {self.task_retention_time}s)")
                
                # DEBUG: Log task age for processing tasks
                if task.status == TaskStatus.PROCESSING:
                    task_age = time.time() - task.created_at
                    logger.debug(f"📊 Processing task {task_id} age: {task_age:.1f}s")
                    
                return task_data
                
            finally:
                self.lock.release()
                
        except Exception as e:
            logger.error(f"❌ Exception getting status for {task_id}: {str(e)}")
            return {"error": f"Status check failed: {str(e)}"}
        
    
    def _get_queue_position(self, task_id: str) -> int:
        """Calculate position in queue for a given task"""
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
    
    def _process_task_safe(self, task: RecipeTask):
        """Ultra-safe task processing with completion timestamp tracking"""
        thread_name = threading.current_thread().name
        
        try:
            # SAFE: Update processing count with timeout
            lock_acquired = self.lock.acquire(timeout=5.0)
            if not lock_acquired:
                logger.error(f"❌ [{thread_name}] Lock timeout starting task {task.task_id}")
                return
            
            try:
                self.processing_count += 1
                task.status = TaskStatus.PROCESSING
                task.progress = {"step": "processing", "message": "Starting recipe generation..."}
            finally:
                self.lock.release()
            
            logger.info(f"🎯 [{thread_name}] Processing task: {task.task_id}")
            
            # Run pipeline without holding locks
            result = self._run_minimal_pipeline(task)  # ← FIXED: result is defined here
            
            # SAFE: Update completion with timeout
            lock_acquired = self.lock.acquire(timeout=5.0)
            if lock_acquired:
                try:
                    task.status = TaskStatus.COMPLETED
                    task.result = result  # ← FIXED: Now result is in scope
                    task.progress = {"step": "completed", "message": "Recipe generation complete!"}
                    # ADD: Track completion time for cleanup
                    task.completion_time = time.time()
                finally:
                    self.lock.release()
            
            logger.info(f"✅ [{thread_name}] Task completed: {task.task_id}")
            
        except Exception as e:
            logger.error(f"❌ [{thread_name}] Task failed: {task.task_id} - {str(e)}")
            
            # SAFE: Mark as failed with timeout
            lock_acquired = self.lock.acquire(timeout=3.0)
            if lock_acquired:
                try:
                    task.status = TaskStatus.FAILED
                    task.error = str(e)
                    task.progress = {"step": "failed", "message": f"Processing failed: {str(e)}"}
                    # ADD: Track completion time for cleanup (even for failures)
                    task.completion_time = time.time()
                finally:
                    self.lock.release()
            
        finally:
            # CRITICAL: Always decrement processing count
            lock_acquired = self.lock.acquire(timeout=5.0)
            if lock_acquired:
                try:
                    self.processing_count -= 1
                finally:
                    self.lock.release()
            
            logger.info(f"🔄 [{thread_name}] Processing count decremented for {task.task_id}")
            
    
    def _run_minimal_pipeline(self, task):
        """Minimal pipeline that works even if agents fail to import"""
        
        start_time = time.time()
        
        # Try to use agents, but fall back to basic generation if imports fail
        try:
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
            
            logger.info("✅ Generator imported successfully")
            
            # Generate base recipe
            task.progress = {"step": "generating", "message": "🤖 Creating recipe..."}
            base_recipe = generator.create_recipe(task.user_request, task.complexity)
            
            if not base_recipe.get('success'):
                raise Exception("Generator failed")
            
            logger.info(f"✅ Generated: {base_recipe.get('title', 'Unknown')}")
            
            # Try enhancement if possible
            try:
                from recipe_enhancer import RecipeEnhancer
                enhancer = RecipeEnhancer()
                enhanced_recipe = enhancer.enhance_recipe(base_recipe, None, task.complexity)
                logger.info("✅ Enhancement successful")
            except Exception as e:
                logger.warning(f"⚠️ Enhancement failed, using base recipe: {str(e)}")
                enhanced_recipe = base_recipe
            
            # Try other agents with fallbacks
            nutrition_data = None
            try:
                from nutrition_analyst import NutritionAnalyst
                analyst = NutritionAnalyst()
                nutrition_data = analyst.analyze_nutrition(enhanced_recipe)
                logger.info("✅ Nutrition analysis successful")
            except Exception as e:
                logger.warning(f"⚠️ Nutrition analysis failed: {str(e)}")
                nutrition_data = self._create_fallback_nutrition(enhanced_recipe)
            
            quality_data = None
            try:
                from quality_evaluator import QualityEvaluator
                evaluator = QualityEvaluator()
                quality_data = evaluator.evaluate_recipe(enhanced_recipe, nutrition_data, None, task.complexity)
                logger.info("✅ Quality evaluation successful")
            except Exception as e:
                logger.warning(f"⚠️ Quality evaluation failed: {str(e)}")
                quality_data = self._create_fallback_quality()
            
            # Create result
            result = {
                'success': True,
                'recipe': enhanced_recipe,
                'nutrition': nutrition_data,
                'quality': quality_data,
                'iterations': 1,
                'complexity_requested': task.complexity,
                'generation_time': int(time.time() - start_time),
                'inspiration_used': False
            }
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Full pipeline failed: {str(e)}")
            logger.error(traceback.format_exc())
            
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
    
    def get_queue_stats(self) -> Dict:
        """Get queue statistics with task retention info"""
        
        # Run cleanup before getting stats
        self._cleanup_old_tasks()
        
        try:
            lock_acquired = self.lock.acquire(timeout=2.0)
            if not lock_acquired:
                logger.error("❌ Lock timeout getting queue stats")
                return {
                    'error': 'System busy',
                    'processing_count': -1,
                    'max_concurrent': self.max_concurrent,
                    'total_tasks': -1,
                    'queue_size': self.queue.qsize() if hasattr(self.queue, 'qsize') else -1,
                    'worker_alive': False,
                    'startup_complete': self.startup_complete
                }
            
            try:
                stats = {
                    'processing_count': self.processing_count,
                    'max_concurrent': self.max_concurrent,
                    'total_tasks': len(self.tasks),
                    'queue_size': self.queue.qsize(),
                    'worker_alive': self.worker_thread.is_alive() if self.worker_thread else False,
                    'startup_complete': self.startup_complete,
                    'tasks_by_status': {},
                    # ADD: Task retention info
                    'task_retention_minutes': self.task_retention_time / 60,
                    'last_cleanup_ago': int(time.time() - self.last_cleanup)
                }
                
                # Count tasks by status
                for task in self.tasks.values():
                    status = task.status.value
                    stats['tasks_by_status'][status] = stats['tasks_by_status'].get(status, 0) + 1
                
                return stats
                
            finally:
                self.lock.release()
                
        except Exception as e:
            logger.error(f"❌ Exception getting queue stats: {str(e)}")
            return {'error': str(e)}
        
            
    def _setup_graceful_shutdown(self):
        """Setup graceful shutdown for the worker thread"""
        
        def shutdown_handler(signum=None, frame=None):
            logger.info("🛑 Shutting down queue worker...")
            self.running = False
            if self.worker_thread and self.worker_thread.is_alive():
                self.worker_thread.join(timeout=5)
            logger.info("🛑 Queue worker shutdown complete")
        
        # Register shutdown handlers
        try:
            signal.signal(signal.SIGTERM, shutdown_handler)
            signal.signal(signal.SIGINT, shutdown_handler)
            atexit.register(shutdown_handler)
        except Exception as e:
            logger.warning(f"⚠️ Could not setup signal handlers: {str(e)}")
    
    def restart_worker(self):
        """Restart the worker thread (for debugging/recovery)"""
        logger.info("🔄 Restarting worker thread...")
        
        # Stop the old worker
        self.running = False
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=5)
        
        # Reset state
        self.running = True
        self.startup_complete = False
        
        # Start new worker
        self._ensure_worker_started()
        
        return {
            'success': True,
            'worker_alive': self.worker_thread.is_alive() if self.worker_thread else False
        }
    
    def shutdown(self):
        """Shutdown the queue worker"""
        logger.info("🛑 Shutting down queue...")
        self.running = False
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=10)
        logger.info("🛑 Queue shutdown complete")

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
            result = self.queue._run_minimal_pipeline(task)
            
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
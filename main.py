# main.py - Optimized with async processing and queue management
import asyncio
import time
from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor
import uuid
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

class RecipeQueue:
    def __init__(self):
        self.tasks = {}
        self.queue = asyncio.Queue(maxsize=50)  # Limit concurrent requests
        self.processing_count = 0
        self.max_concurrent = 3  # Limit simultaneous recipe generations
        
    async def add_task(self, user_request: str, complexity: str) -> str:
        task_id = str(uuid.uuid4())
        task = RecipeTask(
            task_id=task_id,
            user_request=user_request,
            complexity=complexity,
            status=TaskStatus.QUEUED,
            created_at=time.time(),
            progress={"step": "queued", "message": "Request queued for processing"}
        )
        
        self.tasks[task_id] = task
        await self.queue.put(task)
        return task_id
    
    def get_task_status(self, task_id: str) -> Dict:
        task = self.tasks.get(task_id)
        if not task:
            return {"error": "Task not found"}
        
        return {
            "task_id": task.task_id,
            "status": task.status.value,
            "progress": task.progress,
            "result": task.result,
            "error": task.error,
            "queue_position": self._get_queue_position(task_id) if task.status == TaskStatus.QUEUED else None
        }
    
    def _get_queue_position(self, task_id: str) -> int:
        position = 1
        for stored_task in self.tasks.values():
            if stored_task.task_id == task_id:
                break
            if stored_task.status == TaskStatus.QUEUED and stored_task.created_at < self.tasks[task_id].created_at:
                position += 1
        return position

class OptimizedRecipeAgentTeam:
    def __init__(self):
        # Initialize agents (same as before)
        from recipe_generator import RecipeGenerator
        from recipe_enhancer import RecipeEnhancer
        from web_researcher import WebResearcher
        from nutrition_analyst import NutritionAnalyst
        from quality_evaluator import QualityEvaluator
        
        self.generator = RecipeGenerator()
        self.enhancer = RecipeEnhancer()
        self.researcher = WebResearcher()
        self.nutrition_analyst = NutritionAnalyst()
        self.quality_evaluator = QualityEvaluator()
        
        # Thread pool for CPU-bound tasks
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Task queue
        self.queue = RecipeQueue()
        
        # Start queue processor
        asyncio.create_task(self._process_queue())
        
        print("✅ Optimized Recipe Agent Team initialized with async processing")
    
    async def queue_recipe_generation(self, user_request: str, complexity: str = "Medium") -> str:
        """Queue a recipe generation request and return task ID"""
        task_id = await self.queue.add_task(user_request, complexity)
        print(f"🎯 Recipe queued: {task_id} for '{user_request}' ({complexity})")
        return task_id
    
    def get_recipe_status(self, task_id: str) -> Dict:
        """Get status of queued/processing recipe"""
        return self.queue.get_task_status(task_id)
    
    async def _process_queue(self):
        """Process recipe generation queue with concurrency limits"""
        while True:
            try:
                # Wait for task and check concurrency limit
                task = await self.queue.queue.get()
                
                if self.queue.processing_count >= self.queue.max_concurrent:
                    # Put task back in queue if at capacity
                    await self.queue.queue.put(task)
                    await asyncio.sleep(1)
                    continue
                
                # Process task asynchronously
                asyncio.create_task(self._process_recipe_task(task))
                
            except Exception as e:
                print(f"❌ Queue processing error: {str(e)}")
                await asyncio.sleep(1)
    
    async def _process_recipe_task(self, task: RecipeTask):
        """Process individual recipe generation task"""
        try:
            self.queue.processing_count += 1
            task.status = TaskStatus.PROCESSING
            task.progress = {"step": "processing", "message": "Starting recipe generation..."}
            
            # Run the recipe generation pipeline
            result = await self._run_async_pipeline(task)
            
            task.status = TaskStatus.COMPLETED
            task.result = result
            task.progress = {"step": "completed", "message": "Recipe generation complete!"}
            
            print(f"✅ Recipe completed: {task.task_id}")
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.progress = {"step": "failed", "message": f"Generation failed: {str(e)}"}
            print(f"❌ Recipe failed: {task.task_id} - {str(e)}")
            
        finally:
            self.queue.processing_count -= 1
    
    async def _run_async_pipeline(self, task: RecipeTask) -> Dict:
        """Run the recipe generation pipeline with async operations"""
        
        # Step 1: Generate base recipe (CPU-bound, use thread pool)
        task.progress = {"step": "generating", "message": "🤖 Creating base recipe..."}
        
        loop = asyncio.get_event_loop()
        base_recipe = await loop.run_in_executor(
            self.executor, 
            self.generator.create_recipe, 
            task.user_request, 
            task.complexity
        )
        
        if not base_recipe.get('success'):
            raise Exception(base_recipe.get('error', 'Recipe generation failed'))
        
        # Step 2: Web research (I/O-bound, can run concurrently)
        task.progress = {"step": "researching", "message": "🔍 Finding cooking inspiration..."}
        
        inspiration_task = asyncio.create_task(
            self._async_web_research(base_recipe.get('title', ''), base_recipe.get('meal_type'))
        )
        
        # Step 3: While research runs, start enhancement preparation
        enhanced_recipe = base_recipe
        
        # Wait for research to complete
        inspiration_data = await inspiration_task
        
        # Step 4: Enhance recipe (CPU-bound)
        task.progress = {"step": "enhancing", "message": "📝 Adding creative improvements..."}
        
        enhanced_recipe = await loop.run_in_executor(
            self.executor,
            self.enhancer.enhance_recipe,
            base_recipe,
            inspiration_data,
            task.complexity  # Now correctly passing complexity as third argument
        )
        
        # Step 5: Run nutrition and quality in parallel (both CPU-bound)
        task.progress = {"step": "analyzing", "message": "🥗 Analyzing nutrition & quality..."}
        
        nutrition_task = loop.run_in_executor(
            self.executor,
            self.nutrition_analyst.analyze_nutrition,
            enhanced_recipe
        )
        
        quality_task = loop.run_in_executor(
            self.executor,
            self.quality_evaluator.evaluate_recipe,
            enhanced_recipe,
            None,  # Will get nutrition data after it completes
            inspiration_data,
            task.complexity
        )
        
        # Wait for both to complete
        nutrition_data, quality_data = await asyncio.gather(nutrition_task, quality_task)
        
        # Final result
        return {
            'success': True,
            'recipe': enhanced_recipe,
            'nutrition': nutrition_data,
            'quality': quality_data,
            'iterations': 1,
            'complexity_requested': task.complexity,
            'generation_time': int(time.time() - task.created_at),
            'inspiration_used': inspiration_data is not None
        }
    
    async def _async_web_research(self, recipe_title: str, meal_type: str = None):
        """Async wrapper for web research"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self.researcher.find_inspiration,
            recipe_title,
            meal_type
        )

# Global instance
recipe_team = None

def get_recipe_team():
    global recipe_team
    if recipe_team is None:
        recipe_team = OptimizedRecipeAgentTeam()
    return recipe_team
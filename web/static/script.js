class RecipeGenerator {
    constructor() {
        this.hasGeneratedFirstRecipe = false; // Track if user has generated their first recipe
        this.init();
    }
    
    init() {
        this.recipeInput = document.getElementById('recipeInput');
        this.complexityControl = document.getElementById('complexityControl');
        this.generateBtn = document.getElementById('generateBtn');
        this.loading = document.getElementById('loading');
        this.progressLog = document.getElementById('progressLog');
        this.recipeResult = document.getElementById('recipeResult');
        this.errorMessage = document.getElementById('errorMessage');
        this.recentRecipesList = document.getElementById('recentRecipesList');
        this.recentRecipesSection = document.getElementById('recentRecipesSection');
        this.cookingFactsContainer = document.getElementById('cookingFactsContainer');
        this.cookingFact = document.getElementById('cookingFact');
        
        // Filter elements
        this.toggleFiltersBtn = document.getElementById('toggleFilters');
        this.filterPanel = document.getElementById('filterPanel');
        this.searchInput = document.getElementById('searchInput');
        this.mealTypeFilter = document.getElementById('mealTypeFilter');
        this.difficultyFilter = document.getElementById('difficultyFilter');
        this.applyFiltersBtn = document.getElementById('applyFilters');
        this.clearFiltersBtn = document.getElementById('clearFilters');
        
        // Modal elements
        this.recipeModal = document.getElementById('recipeModal');
        this.modalRecipeTitle = document.getElementById('modalRecipeTitle');
        this.modalRecipeContent = document.getElementById('modalRecipeContent');
        this.closeModalBtn = document.getElementById('closeModal');
        this.printRecipeBtn = document.getElementById('printRecipeBtn');
        this.viewAllRecipesLink = document.getElementById('viewAllRecipesLink');
        
        // Cooking facts for loading entertainment
        this.cookingFacts = [
            "🍅 Tomatoes are technically fruits, not vegetables!",
            "🧄 Garlic can help reduce blood pressure and cholesterol.",
            "🍯 Honey never spoils - archaeologists found edible honey in Egyptian tombs!",
            "🧅 Cutting onions releases sulfuric compounds that make you cry.",
            "🥑 Avocados are berries, but strawberries aren't!",
            "🌶️ Capsaicin in chili peppers can boost your metabolism.",
            "🧂 Salt was once so valuable it was used as currency.",
            "🥚 Fresh eggs sink in water, while old eggs float.",
            "🍄 Mushrooms are more closely related to humans than plants!",
            "🍫 Dark chocolate contains antioxidants that are good for your heart.",
            "🥕 Carrots were originally purple, not orange!",
            "🍞 Bread was the first food baked in space.",
            "🧀 It takes about 10 pounds of milk to make 1 pound of cheese.",
            "🍋 Lemons contain more sugar than strawberries!",
            "🥜 Peanuts aren't actually nuts - they're legumes like peas.",
            "🍎 Apples float because they're 25% air.",
            "🥥 Coconut water can be used as blood plasma in emergencies.",
            "🌽 Corn is grown on every continent except Antarctica.",
            "🥒 Cucumbers are 96% water, making them very hydrating.",
            "🍌 Bananas are berries, but raspberries aren't!",
            "🥩 Marbling in meat comes from intramuscular fat distribution.",
            "🐟 Fish continues to cook from residual heat after removing from heat.",
            "🍳 The Maillard reaction creates the browning and flavor in cooked foods.",
            "🧊 Ice cubes made with hot water freeze faster than those made with cold.",
            "🥘 Searing meat doesn't actually 'seal in' juices - that's a myth!",
            "🔥 The 'smoke point' of oil determines its best cooking method.",
            "🌿 Fresh herbs should be added at the end to preserve their flavor.",
            "⏰ Resting meat after cooking allows juices to redistribute evenly.",
            "🧈 Butter burns at a lower temperature than most cooking oils.",
            "🥄 A pinch of salt can enhance sweetness in desserts!",
            "🍇 Grapes explode when you put them in the microwave.",
            "🥖 French baguettes are required by law to contain only 4 ingredients.",
            "🦞 Lobsters were once considered prison food for the poor.",
            "🍓 Strawberries have more vitamin C than oranges!",
            "🥬 Lettuce belongs to the sunflower family.",
            "🌰 Chestnuts are the only nuts that contain vitamin C.",
            "🍊 Orange peels contain more fiber than the fruit itself.",
            "🥦 Broccoli contains more protein per calorie than steak.",
            "🍪 The chocolate chip cookie was invented by accident.",
            "🌮 Cilantro tastes like soap to 14% of people due to genetics.",
            "🥝 Kiwi fruits contain more vitamin C than oranges.",
            "🧅 Onions make you cry less when they're cold.",
            "🍰 Vanilla is the second most expensive spice after saffron.",
            "🥓 Bacon was used as currency in Colonial America.",
            "🍉 Watermelons are 91% water and related to cucumbers.",
            "🌶️ Birds can't taste spicy food because they lack heat receptors.",
            "🥨 Pretzels were originally created by monks as rewards for prayers.",
            "🧄 Elephant garlic isn't actually garlic - it's a type of leek.",
            "🍯 It takes 556 worker bees to gather 1 pound of honey.",
            "🥔 Potatoes were the first vegetable grown in space.",
            "🍋 Meyer lemons are actually a cross between lemons and oranges.",
            "🥩 Wagyu beef comes from cows that are massaged and fed beer.",
            "🌽 Popcorn is over 5,000 years old!",
            "🧀 Roquefort cheese can only be made in caves in France.",
            "🥭 Mangoes are the most consumed fruit in the world.",
            "🍄 Some mushrooms glow in the dark naturally.",
            "🥑 Avocados are toxic to dogs and cats.",
            "🍎 There are over 7,500 varieties of apples worldwide.",
            "🥥 Coconuts aren't nuts - they're actually seeds.",
            "🌶️ The Carolina Reaper is the world's hottest pepper.",
            "🧄 Garlic can be used as a natural antibiotic.",
            "🍯 Honey has natural antibacterial properties.",
            "🥜 Almonds are actually seeds, not nuts.",
            "🍊 Orange vegetables get their color from beta-carotene.",
            "🥬 Iceberg lettuce is 95% water.",
            "🍓 Strawberries are the only fruit with seeds on the outside.",
            "🧅 Cutting onions under running water reduces tears.",
            "🥕 Baby carrots are just regular carrots cut into small pieces.",
            "🍋 Lemons were once more valuable than gold.",
            "🥔 Green potatoes are toxic and shouldn't be eaten.",
            "🌽 Each kernel of corn is a separate fruit.",
            "🥦 Broccoli, cauliflower, and cabbage are all the same species.",
            "🍄 Mushrooms have their own immune system.",
            "🧀 Cheese is the most stolen food in the world.",
            "🥩 Dry-aging beef can take up to 120 days.",
            "🐟 Salmon get their pink color from eating shrimp.",
            "🍳 Brown eggs aren't healthier - shell color depends on hen breed.",
            "🧂 Himalayan pink salt is actually mined in Pakistan.",
            "🌿 Basil repels mosquitoes naturally.",
            "🥄 Wooden spoons don't conduct heat like metal ones.",
            "🔥 Capsaicin is measured in Scoville Heat Units.",
            "🧊 Adding salt to ice makes it melt faster and get colder.",
            "🥘 Cast iron pans can add iron to your food.",
            "⏰ Food tastes different on airplanes due to low humidity and pressure."
        ];
        
        this.factInterval = null;
        this.currentFactIndex = 0;
        
        this.bindEvents();
        // Don't load recent recipes on initial page load
        
        // Track page load after PostHog is ready
        this.waitForPostHog(() => {
            this.trackEvent('page_loaded', {
                timestamp: new Date().toISOString()
            });
        });
    }
    
    waitForPostHog(callback) {
        // Check if PostHog is loaded and ready
        if (typeof posthog !== 'undefined' && posthog.capture) {
            callback();
        } else {
            // Wait a bit and try again
            setTimeout(() => this.waitForPostHog(callback), 100);
        }
    }
    
    trackEvent(eventName, properties = {}) {
        try {
            if (typeof posthog !== 'undefined' && posthog.capture) {
                posthog.capture(eventName, properties);
                console.log(`📊 Tracked: ${eventName}`, properties);
            } else {
                console.log(`📊 PostHog not ready, queuing: ${eventName}`);
                // Queue the event to track once PostHog is ready
                this.waitForPostHog(() => {
                    posthog.capture(eventName, properties);
                    console.log(`📊 Tracked (queued): ${eventName}`, properties);
                });
            }
        } catch (error) {
            console.log('PostHog tracking error:', error);
        }
    }
    
    bindEvents() {
        this.generateBtn.addEventListener('click', () => this.generateRecipe());
        this.recipeInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.generateRecipe();
        });
        
        // Filter events
        this.toggleFiltersBtn.addEventListener('click', () => this.toggleFilters());
        this.applyFiltersBtn.addEventListener('click', () => this.applyFilters());
        this.clearFiltersBtn.addEventListener('click', () => this.clearFilters());
        this.searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.applyFilters();
        });
        
        // Modal events
        this.closeModalBtn.addEventListener('click', () => this.closeModal());
        this.printRecipeBtn.addEventListener('click', () => this.printModalRecipe());
        this.recipeModal.addEventListener('click', (e) => {
            if (e.target === this.recipeModal) this.closeModal();
        });
        
        // View all recipes link
        this.viewAllRecipesLink.addEventListener('click', (e) => {
            e.preventDefault();
            this.showAllRecipes();
        });
    }
    
    async generateRecipe() {
        const request = this.recipeInput.value.trim();
        const complexityRadio = this.complexityControl.querySelector('input[name="complexity"]:checked');
        const complexity = complexityRadio ? complexityRadio.value : 'Medium';
        
        if (!request) {
            this.showError('Please enter a recipe request');
            return;
        }
        
        // Track recipe generation start
        this.trackEvent('recipe_generation_started', {
            recipe_request: request,
            complexity: complexity,
            timestamp: new Date().toISOString()
        });
        
        this.showLoading();
        this.hideError();
        
        const startTime = Date.now();
        
        try {
            const response = await fetch('/api/generate-recipe', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    recipe_request: request,
                    complexity: complexity 
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                const generationTime = (Date.now() - startTime) / 1000;
                
                // Track successful recipe generation
                this.trackEvent('recipe_generated_success', {
                    recipe_title: data.recipe?.title,
                    recipe_request: request,
                    complexity: complexity,
                    generation_time: generationTime,
                    server_generation_time: data.generation_time,
                    meal_type: data.recipe?.meal_type,
                    cuisine_type: data.recipe?.cuisine_type,
                    ingredients_count: data.recipe?.ingredients?.length || 0,
                    instructions_count: data.recipe?.instructions?.length || 0,
                    quality_score: data.quality?.score,
                    nutrition_method: data.nutrition?.analysis_method,
                    timestamp: new Date().toISOString()
                });
                
                this.displayRecipe(data);
                
                // Show recent recipes section after first successful generation
                if (!this.hasGeneratedFirstRecipe) {
                    this.hasGeneratedFirstRecipe = true;
                    this.showRecentRecipesSection();
                    
                    // Track first recipe milestone
                    this.trackEvent('first_recipe_generated', {
                        recipe_title: data.recipe?.title,
                        complexity: complexity,
                        timestamp: new Date().toISOString()
                    });
                }
                
                this.loadRecentRecipes();
            } else {
                // Track recipe generation failure
                this.trackEvent('recipe_generation_failed', {
                    recipe_request: request,
                    complexity: complexity,
                    error: data.error,
                    generation_time: (Date.now() - startTime) / 1000,
                    timestamp: new Date().toISOString()
                });
                
                this.showError(data.error || 'Recipe generation failed');
            }
        } catch (error) {
            console.error('Error:', error);
            
            // Track network/system errors
            this.trackEvent('recipe_generation_error', {
                recipe_request: request,
                complexity: complexity,
                error: error.message,
                generation_time: (Date.now() - startTime) / 1000,
                timestamp: new Date().toISOString()
            });
            
            this.showError('Network error. Please try again.');
        } finally {
            this.hideLoading();
        }
    }
    
    showRecentRecipesSection() {
        // Show the recent recipes section with a smooth reveal
        this.recentRecipesSection.style.display = 'block';
        
        // Do NOT auto-scroll to the recent recipes section
        // Let the user stay focused on their newly generated recipe
    }
    
    showAllRecipes() {
        // Track view all recipes action
        this.trackEvent('view_all_recipes_clicked', {
            timestamp: new Date().toISOString()
        });
        
        // Show recent recipes section if not already visible
        if (!this.hasGeneratedFirstRecipe) {
            this.hasGeneratedFirstRecipe = true;
            this.showRecentRecipesSection();
        }
        
        // Load recipes and scroll to them
        this.loadRecentRecipes();
        
        // Smooth scroll to the recipes section
        setTimeout(() => {
            this.recentRecipesSection.scrollIntoView({ 
                behavior: 'smooth', 
                block: 'start' 
            });
        }, 100);
    }
    
    showLoading() {
        this.generateBtn.disabled = true;
        this.generateBtn.textContent = 'Generating...';
        this.loading.style.display = 'block';
        this.recipeResult.style.display = 'none';
        this.startCookingFacts();
        this.simulateProgress();
    }
    
    hideLoading() {
        this.generateBtn.disabled = false;
        this.generateBtn.textContent = '🍳 Generate Recipe';
        this.loading.style.display = 'none';
        this.stopCookingFacts();
    }
    
    startCookingFacts() {
        // Show the container
        this.cookingFactsContainer.style.display = 'block';
        
        // Wait 2 seconds before showing the first fact
        setTimeout(() => {
            this.currentFactIndex = 0;
            this.showCookingFact();
            
            // Set interval to rotate facts every 3.5 seconds
            this.factInterval = setInterval(() => {
                this.showCookingFact();
            }, 3500);
        }, 2000);
    }
    
    stopCookingFacts() {
        if (this.factInterval) {
            clearInterval(this.factInterval);
            this.factInterval = null;
        }
        this.cookingFactsContainer.style.display = 'none';
    }
    
    showCookingFact() {
        const fact = this.cookingFacts[this.currentFactIndex];
        
        // Start slide-out animation for current fact
        this.cookingFact.classList.add('slide-out');
        
        // After slide-out completes, change text and slide in
        setTimeout(() => {
            this.cookingFact.textContent = fact;
            this.cookingFact.classList.remove('slide-out');
            this.cookingFact.classList.add('slide-in');
            
            // Remove slide-in class after animation
            setTimeout(() => {
                this.cookingFact.classList.remove('slide-in');
            }, 500);
            
        }, 300); // Wait for slide-out to complete
        
        // Move to next fact
        this.currentFactIndex = (this.currentFactIndex + 1) % this.cookingFacts.length;
    }
    
    simulateProgress() {
        const steps = [
            '🤖 Recipe Generator: Creating base recipe...',
            '🔍 Web Researcher: Finding cooking inspiration...',
            '📝 Recipe Enhancer: Adding creative improvements...',
            '🥗 Nutrition Analyst: Calculating health metrics...',
            '⭐ Quality Evaluator: Scoring recipe quality...'
        ];
        
        let currentStep = 0;
        this.progressLog.innerHTML = '';
        
        const interval = setInterval(() => {
            if (currentStep < steps.length) {
                const progressItem = document.createElement('div');
                progressItem.className = 'progress-item in-progress';
                progressItem.textContent = steps[currentStep];
                this.progressLog.appendChild(progressItem);
                
                if (currentStep > 0) {
                    const prevItem = this.progressLog.children[currentStep - 1];
                    prevItem.className = 'progress-item completed';
                    prevItem.textContent += ' ✓';
                }
                
                currentStep++;
                this.progressLog.scrollTop = this.progressLog.scrollHeight;
            } else {
                clearInterval(interval);
                if (this.progressLog.children.length > 0) {
                    const lastItem = this.progressLog.children[this.progressLog.children.length - 1];
                    lastItem.className = 'progress-item completed';
                    lastItem.textContent += ' ✓';
                }
            }
        }, 2500);
    }
    
    displayRecipe(data) {
        const recipe = data.recipe;
        const nutrition = data.nutrition;
        const quality = data.quality;
        
        const html = `
            <div class="recipe-header">
                <h1 class="recipe-title">${recipe.title}</h1>
                <p class="recipe-description">${recipe.description || ''}</p>
                
                <div class="recipe-meta">
                    <span class="meta-item">⏱️ Prep: ${recipe.prep_time}</span>
                    <span class="meta-item">🔥 Cook: ${recipe.cook_time}</span>
                    <span class="meta-item">👥 Serves: ${recipe.servings}</span>
                    <span class="meta-item">📊 ${recipe.difficulty}</span>
                </div>
            </div>
            
            <div class="recipe-section">
                <h2 class="section-title">🥘 Ingredients</h2>
                <div class="ingredients-grid">
                    ${recipe.ingredients.map(ingredient => 
                        `<div class="ingredient-item">${ingredient}</div>`
                    ).join('')}
                </div>
            </div>
            
            <div class="recipe-section">
                <h2 class="section-title">👨‍🍳 Instructions</h2>
                <div class="instructions-list">
                    ${recipe.instructions.map(instruction => 
                        `<div class="instruction-item">${instruction}</div>`
                    ).join('')}
                </div>
            </div>
            
            ${nutrition && nutrition.nutrition_per_serving ? `
            <div class="recipe-section">
                <h2 class="section-title">📊 Nutrition (per serving)</h2>
                <div class="nutrition-grid">
                    <div class="nutrition-card">
                        <div class="nutrition-value">${nutrition.nutrition_per_serving.calories || 'N/A'}</div>
                        <div class="nutrition-label">Calories</div>
                    </div>
                    <div class="nutrition-card">
                        <div class="nutrition-value">${nutrition.nutrition_per_serving.protein || 'N/A'}g</div>
                        <div class="nutrition-label">Protein</div>
                    </div>
                    <div class="nutrition-card">
                        <div class="nutrition-value">${nutrition.nutrition_per_serving.carbs || 'N/A'}g</div>
                        <div class="nutrition-label">Carbs</div>
                    </div>
                    <div class="nutrition-card">
                        <div class="nutrition-value">${nutrition.nutrition_per_serving.fat || 'N/A'}g</div>
                        <div class="nutrition-label">Fat</div>
                    </div>
                </div>
                
                ${nutrition.health_insights && nutrition.health_insights.length > 0 ? `
                <div class="health-insights">
                    <h3>💡 Health Insights</h3>
                    <ul>
                        ${nutrition.health_insights.slice(0, 3).map(insight => 
                            `<li>${insight}</li>`
                        ).join('')}
                    </ul>
                </div>
                ` : ''}
            </div>
            ` : ''}
            
            ${recipe.enhancements_made && recipe.enhancements_made.length > 0 ? `
            <div class="recipe-section">
                <h2 class="section-title">✨ AI Enhancements</h2>
                <div class="enhancement-list">
                    <ul>
                        ${recipe.enhancements_made.map(enhancement => 
                            `<li>${enhancement}</li>`
                        ).join('')}
                    </ul>
                </div>
            </div>
            ` : ''}
            
            <div class="generation-stats">
                <p><strong>Generated in ${data.generation_time} seconds with ${data.iterations} iteration${data.iterations > 1 ? 's' : ''}</strong></p>
                <p style="margin-top: 10px; color: #666;">Complexity: ${recipe.difficulty}</p>
                <div style="margin-top: 15px;">
                    <button onclick="recipeApp.printCurrentRecipe()" class="print-recipe-btn">🖨️ Print Recipe</button>
                </div>
            </div>
        `;
        
        this.recipeResult.innerHTML = html;
        this.recipeResult.style.display = 'block';
        this.recipeResult.scrollIntoView({ behavior: 'smooth' });
    }
    
    async loadRecentRecipes(filters = {}) {
        try {
            console.log('📋 loadRecentRecipes called with filters:', filters);
            
            const params = new URLSearchParams();
            params.append('limit', '25');
            
            if (filters.search) {
                params.append('search', filters.search);
                console.log('📋 Added search filter:', filters.search);
            }
            if (filters.meal_type && filters.meal_type !== 'all') {
                params.append('meal_type', filters.meal_type);
                console.log('📋 Added meal_type filter:', filters.meal_type);
            }
            if (filters.difficulty && filters.difficulty !== 'all') {
                params.append('difficulty', filters.difficulty);
                console.log('📋 Added difficulty filter:', filters.difficulty);
            }
            
            const apiUrl = `/api/recipes?${params.toString()}`;
            console.log('📋 API URL:', apiUrl);
            
            const response = await fetch(apiUrl);
            const data = await response.json();
            
            console.log('📋 API Response:', data);
            
            if (data.success && data.recipes.length > 0) {
                const html = data.recipes.map(recipe => `
                    <div class="recent-recipe-item" onclick="recipeApp.viewRecipe('${recipe.id}')">
                        <div>
                            <strong>${recipe.title}</strong>
                            <br>
                            <small style="color: #666;">
                                ${recipe.meal_type || 'Unknown'} • ${recipe.difficulty || 'Unknown'}
                            </small>
                            ${recipe.views_count ? `<div class="recipe-views">👁️ ${recipe.views_count} views</div>` : ''}
                        </div>
                        <div style="color: #999; font-size: 0.9rem;">
                            ${new Date(recipe.created_at).toLocaleDateString()}
                        </div>
                    </div>
                `).join('');
                
                this.recentRecipesList.innerHTML = html;
                console.log('📋 Updated recipe list with', data.recipes.length, 'recipes');
                
                if (Object.keys(filters).some(key => filters[key] && filters[key] !== 'all')) {
                    const filterInfo = document.createElement('div');
                    filterInfo.style.cssText = 'background: #e3f2fd; padding: 10px; border-radius: 8px; margin-bottom: 15px; color: #1976d2;';
                    filterInfo.innerHTML = `📊 Found ${data.count} recipes matching your search`;
                    this.recentRecipesList.insertBefore(filterInfo, this.recentRecipesList.firstChild);
                    console.log('📋 Added filter info banner');
                }
            } else {
                const hasActiveFilters = Object.keys(filters).some(key => filters[key] && filters[key] !== 'all');
                const message = hasActiveFilters 
                    ? 'No recipes match your search criteria. Try adjusting your filters.'
                    : 'No recipes generated yet. Be the first!';
                this.recentRecipesList.innerHTML = `<p style="color: #666;">${message}</p>`;
                console.log('📋 No recipes found, showing message:', message);
            }
        } catch (error) {
            console.error('❌ Error loading recipes:', error);
            this.recentRecipesList.innerHTML = '<p style="color: #999;">Unable to load recipes</p>';
        }
    }
    
    toggleFilters() {
        const isVisible = this.filterPanel.style.display !== 'none';
        this.filterPanel.style.display = isVisible ? 'none' : 'block';
        this.toggleFiltersBtn.textContent = isVisible ? '🔍 Search All Recipes' : '🔍 Hide Search';
    }
    
    applyFilters() {
        console.log('🔍 Apply Filters clicked - gathering filter values...');
        
        const filters = {
            search: this.searchInput.value.trim(),
            meal_type: this.mealTypeFilter.value,
            difficulty: this.difficultyFilter.value
        };
        
        // Track filter usage
        this.trackEvent('filters_applied', {
            search_term: filters.search || null,
            meal_type: filters.meal_type !== 'all' ? filters.meal_type : null,
            difficulty: filters.difficulty !== 'all' ? filters.difficulty : null,
            has_search: !!filters.search,
            has_meal_filter: filters.meal_type !== 'all',
            has_difficulty_filter: filters.difficulty !== 'all',
            timestamp: new Date().toISOString()
        });
        
        console.log('🔍 Filter values:', filters);
        console.log('🔍 Calling loadRecentRecipes with filters...');
        
        this.loadRecentRecipes(filters);
    }
    
    clearFilters() {
        console.log('🔍 Clear Filters clicked - resetting all values...');
        
        this.searchInput.value = '';
        this.mealTypeFilter.value = 'all';
        this.difficultyFilter.value = 'all';
        
        console.log('🔍 Calling loadRecentRecipes without filters...');
        this.loadRecentRecipes();
    }
    
    async viewRecipe(recipeId) {
        try {
            console.log('Requesting recipe data for ID:', recipeId);
            
            // Track recipe view
            this.trackEvent('recipe_viewed', {
                recipe_id: recipeId,
                timestamp: new Date().toISOString()
            });
            
            const response = await fetch(`/api/recipes/${recipeId}`);
            const data = await response.json();
            
            if (data.success) {
                console.log('Got data for recipe ', recipeId)
                this.displayRecipeInModal(data.recipe);
                
                // Track successful recipe modal open
                this.trackEvent('recipe_modal_opened', {
                    recipe_id: recipeId,
                    recipe_title: data.recipe?.title,
                    complexity: data.recipe?.difficulty,
                    meal_type: data.recipe?.meal_type,
                    timestamp: new Date().toISOString()
                });
            } else {
                console.error('Error viewing recipe:', data.error);
                alert('Error loading recipe: ' + data.error);
            }
        } catch (error) {
            console.error('Error encountered trying to view recipe:', error);
            alert('Error loading recipe. Please try again.');
        }
    }
    
    displayRecipeInModal(recipe) {
        this.modalRecipeTitle.textContent = recipe.title;
        
        const nutritionData = recipe.nutrition_data;
        const nutritionHtml = nutritionData && nutritionData.nutrition_per_serving ? `
            <div class="recipe-section">
                <h2 class="section-title">📊 Nutrition (per serving)</h2>
                <div class="nutrition-grid">
                    <div class="nutrition-card">
                        <div class="nutrition-value">${nutritionData.nutrition_per_serving.calories || 'N/A'}</div>
                        <div class="nutrition-label">Calories</div>
                    </div>
                    <div class="nutrition-card">
                        <div class="nutrition-value">${nutritionData.nutrition_per_serving.protein || 'N/A'}g</div>
                        <div class="nutrition-label">Protein</div>
                    </div>
                    <div class="nutrition-card">
                        <div class="nutrition-value">${nutritionData.nutrition_per_serving.carbs || 'N/A'}g</div>
                        <div class="nutrition-label">Carbs</div>
                    </div>
                    <div class="nutrition-card">
                        <div class="nutrition-value">${nutritionData.nutrition_per_serving.fat || 'N/A'}g</div>
                        <div class="nutrition-label">Fat</div>
                    </div>
                </div>
                
                ${nutritionData.health_insights && nutritionData.health_insights.length > 0 ? `
                <div class="health-insights">
                    <h3>💡 Health Insights</h3>
                    <ul>
                        ${nutritionData.health_insights.slice(0, 3).map(insight => 
                            `<li>${insight}</li>`
                        ).join('')}
                    </ul>
                </div>
                ` : ''}
            </div>
        ` : '';
        
        const html = `
            <div class="recipe-header">
                <p class="recipe-description">${recipe.description || ''}</p>
                
                <div class="recipe-meta">
                    <span class="meta-item">⏱️ Prep: ${recipe.prep_time}</span>
                    <span class="meta-item">🔥 Cook: ${recipe.cook_time}</span>
                    <span class="meta-item">👥 Serves: ${recipe.servings}</span>
                    <span class="meta-item">📊 ${recipe.difficulty}</span>
                </div>
            </div>
            
            <div class="recipe-section">
                <h2 class="section-title">🥘 Ingredients</h2>
                <div class="ingredients-grid">
                    ${recipe.ingredients.map(ingredient => 
                        `<div class="ingredient-item">${ingredient}</div>`
                    ).join('')}
                </div>
            </div>
            
            <div class="recipe-section">
                <h2 class="section-title">👨‍🍳 Instructions</h2>
                <div class="instructions-list">
                    ${recipe.instructions.map(instruction => 
                        `<div class="instruction-item">${instruction}</div>`
                    ).join('')}
                </div>
            </div>
            
            ${nutritionHtml}
            
            ${recipe.enhancements_made && recipe.enhancements_made.length > 0 ? `
            <div class="recipe-section">
                <h2 class="section-title">✨ AI Enhancements</h2>
                <div class="enhancement-list">
                    <ul>
                        ${recipe.enhancements_made.map(enhancement => 
                            `<li>${enhancement}</li>`
                        ).join('')}
                    </ul>
                </div>
            </div>
            ` : ''}
            
            <div class="generation-stats">
                <p>Generated ${recipe.iterations_count} iteration${recipe.iterations_count > 1 ? 's' : ''} • Views: ${recipe.views_count || 0}</p>
                <p style="margin-top: 5px; color: #666;">Created: ${new Date(recipe.created_at).toLocaleDateString()}</p>
            </div>
        `;
        
        this.modalRecipeContent.innerHTML = html;
        this.recipeModal.style.display = 'block';
        document.body.style.overflow = 'hidden';
    }
    
    closeModal() {
        this.recipeModal.style.display = 'none';
        document.body.style.overflow = 'auto';
    }
    
    printCurrentRecipe() {
        // Track print action for current recipe
        this.trackEvent('current_recipe_printed', {
            timestamp: new Date().toISOString()
        });
        
        // Create a clean print version of the current recipe
        const recipeContent = this.recipeResult.cloneNode(true);
        
        // Remove the print button from the cloned content
        const printBtn = recipeContent.querySelector('.print-recipe-btn');
        if (printBtn) {
            printBtn.remove();
        }
        
        // Create a new window for printing
        const printWindow = window.open('', '_blank');
        printWindow.document.write(`
            <!DOCTYPE html>
            <html>
            <head>
                <title>Recipe - Print</title>
                <style>
                    ${this.getPrintStyles()}
                </style>
            </head>
            <body>
                <div class="print-container">
                    ${recipeContent.innerHTML}
                </div>
            </body>
            </html>
        `);
        
        printWindow.document.close();
        printWindow.focus();
        
        // Wait for content to load, then print
        setTimeout(() => {
            printWindow.print();
            printWindow.close();
        }, 250);
    }
    
    printModalRecipe() {
        // Track print action for modal recipe
        this.trackEvent('modal_recipe_printed', {
            timestamp: new Date().toISOString()
        });
        
        // Create a clean print version of the modal content
        const modalContent = this.modalRecipeContent.cloneNode(true);
        const modalTitle = this.modalRecipeTitle.textContent;
        
        // Create a new window for printing
        const printWindow = window.open('', '_blank');
        printWindow.document.write(`
            <!DOCTYPE html>
            <html>
            <head>
                <title>${modalTitle} - Print</title>
                <style>
                    ${this.getPrintStyles()}
                </style>
            </head>
            <body>
                <div class="print-container">
                    <div class="recipe-header">
                        <h1 class="recipe-title">${modalTitle}</h1>
                    </div>
                    ${modalContent.innerHTML}
                </div>
            </body>
            </html>
        `);
        
        printWindow.document.close();
        printWindow.focus();
        
        // Wait for content to load, then print
        setTimeout(() => {
            printWindow.print();
            printWindow.close();
        }, 250);
    }
    
    getPrintStyles() {
        // All print styles are handled in styles.css
        return '';
    }
    
    showError(message) {
        this.errorMessage.textContent = message;
        this.errorMessage.style.display = 'block';
    }
    
    hideError() {
        this.errorMessage.style.display = 'none';
    }
}

// Initialize the app
let recipeApp;
document.addEventListener('DOMContentLoaded', () => {
    recipeApp = new RecipeGenerator();
});
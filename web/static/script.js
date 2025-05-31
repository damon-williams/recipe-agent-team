class RecipeGenerator {
    constructor() {
        this.init();
    }
    
    init() {
        this.recipeInput = document.getElementById('recipeInput');
        this.generateBtn = document.getElementById('generateBtn');
        this.loading = document.getElementById('loading');
        this.progressLog = document.getElementById('progressLog');
        this.recipeResult = document.getElementById('recipeResult');
        this.errorMessage = document.getElementById('errorMessage');
        this.recentRecipesList = document.getElementById('recentRecipesList');
        
        // Filter elements
        this.toggleFiltersBtn = document.getElementById('toggleFilters');
        this.filterPanel = document.getElementById('filterPanel');
        this.searchInput = document.getElementById('searchInput');
        this.mealTypeFilter = document.getElementById('mealTypeFilter');
        this.difficultyFilter = document.getElementById('difficultyFilter');
        this.qualityFilter = document.getElementById('qualityFilter');
        this.applyFiltersBtn = document.getElementById('applyFilters');
        this.clearFiltersBtn = document.getElementById('clearFilters');
        
        // Modal elements
        this.recipeModal = document.getElementById('recipeModal');
        this.modalRecipeTitle = document.getElementById('modalRecipeTitle');
        this.modalRecipeContent = document.getElementById('modalRecipeContent');
        this.closeModalBtn = document.getElementById('closeModal');
        this.printRecipeBtn = document.getElementById('printRecipeBtn');
        
        this.bindEvents();
        this.loadRecentRecipes();
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
        this.printRecipeBtn.addEventListener('click', () => this.printRecipe());
        this.recipeModal.addEventListener('click', (e) => {
            if (e.target === this.recipeModal) this.closeModal();
        });
    }
    
    async generateRecipe() {
        const request = this.recipeInput.value.trim();
        if (!request) {
            this.showError('Please enter a recipe request');
            return;
        }
        
        this.showLoading();
        this.hideError();
        
        try {
            const response = await fetch('/api/generate-recipe', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ recipe_request: request })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.displayRecipe(data);
                this.loadRecentRecipes();
            } else {
                this.showError(data.error || 'Recipe generation failed');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showError('Network error. Please try again.');
        } finally {
            this.hideLoading();
        }
    }
    
    showLoading() {
        this.generateBtn.disabled = true;
        this.generateBtn.textContent = 'Generating...';
        this.loading.style.display = 'block';
        this.recipeResult.style.display = 'none';
        this.simulateProgress();
    }
    
    hideLoading() {
        this.generateBtn.disabled = false;
        this.generateBtn.textContent = '🚀 Generate Recipe with AI Agents';
        this.loading.style.display = 'none';
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
                    <span class="quality-score">⭐ ${quality.score}/10</span>
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
            
            <div class="tags">
                ${recipe.tags ? recipe.tags.map(tag => `<span class="tag">${tag}</span>`).join('') : ''}
                ${nutrition?.dietary_tags ? nutrition.dietary_tags.map(tag => `<span class="tag">${tag}</span>`).join('') : ''}
            </div>
            
            <div class="generation-stats">
                <p><strong>Generated in ${data.generation_time} seconds with ${data.iterations} iteration${data.iterations > 1 ? 's' : ''}</strong></p>
                <p style="margin-top: 10px; color: #666;">Quality Level: ${quality.quality_level} | Confidence: ${quality.confidence}</p>
            </div>
        `;
        
        this.recipeResult.innerHTML = html;
        this.recipeResult.style.display = 'block';
        this.recipeResult.scrollIntoView({ behavior: 'smooth' });
    }
    
    async loadRecentRecipes(filters = {}) {
        try {
            const params = new URLSearchParams();
            params.append('limit', '10');
            
            if (filters.search) params.append('search', filters.search);
            if (filters.meal_type && filters.meal_type !== 'all') params.append('meal_type', filters.meal_type);
            if (filters.difficulty && filters.difficulty !== 'all') params.append('difficulty', filters.difficulty);
            if (filters.min_quality > 0) params.append('min_quality', filters.min_quality);
            
            const response = await fetch(`/api/recipes?${params.toString()}`);
            const data = await response.json();
            
            if (data.success && data.recipes.length > 0) {
                const html = data.recipes.map(recipe => `
                    <div class="recent-recipe-item" onclick="recipeApp.viewRecipe('${recipe.id}')">
                        <div>
                            <strong>${recipe.title}</strong>
                            <br>
                            <small style="color: #666;">
                                ${recipe.meal_type || 'Unknown'} • ${recipe.difficulty || 'Unknown'} • ⭐ ${recipe.quality_score || 'N/A'}/10
                            </small>
                            ${recipe.views_count ? `<div class="recipe-views">👁️ ${recipe.views_count} views</div>` : ''}
                        </div>
                        <div style="color: #999; font-size: 0.9rem;">
                            ${new Date(recipe.created_at).toLocaleDateString()}
                        </div>
                    </div>
                `).join('');
                
                this.recentRecipesList.innerHTML = html;
                
                if (Object.keys(filters).length > 0) {
                    const filterInfo = document.createElement('div');
                    filterInfo.style.cssText = 'background: #e3f2fd; padding: 10px; border-radius: 8px; margin-bottom: 15px; color: #1976d2;';
                    filterInfo.innerHTML = `📊 Found ${data.count} recipes matching your filters`;
                    this.recentRecipesList.insertBefore(filterInfo, this.recentRecipesList.firstChild);
                }
            } else {
                const message = Object.keys(filters).length > 0 
                    ? 'No recipes match your filters. Try adjusting your search criteria.'
                    : 'No recipes generated yet. Be the first!';
                this.recentRecipesList.innerHTML = `<p style="color: #666;">${message}</p>`;
            }
        } catch (error) {
            console.error('Error loading recipes:', error);
            this.recentRecipesList.innerHTML = '<p style="color: #999;">Unable to load recipes</p>';
        }
    }
    
    toggleFilters() {
        const isVisible = this.filterPanel.style.display !== 'none';
        this.filterPanel.style.display = isVisible ? 'none' : 'block';
        this.toggleFiltersBtn.textContent = isVisible ? '🔍 Filters' : '🔍 Hide Filters';
    }
    
    applyFilters() {
        const filters = {
            search: this.searchInput.value.trim(),
            meal_type: this.mealTypeFilter.value,
            difficulty: this.difficultyFilter.value,
            min_quality: parseFloat(this.qualityFilter.value)
        };
        this.loadRecentRecipes(filters);
    }
    
    clearFilters() {
        this.searchInput.value = '';
        this.mealTypeFilter.value = 'all';
        this.difficultyFilter.value = 'all';
        this.qualityFilter.value = '0';
        this.loadRecentRecipes();
    }
    
    async viewRecipe(recipeId) {
        try {
            console.log('Requesting recipe data for ID:', recipeId);
            const response = await fetch(`/api/recipes/${recipeId}`);
            const data = await response.json();
            
            if (data.success) {
                console.log('Got data for recipe ', recipeId)
                this.displayRecipeInModal(data.recipe);
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
                    <span class="quality-score">⭐ ${recipe.quality_score}/10</span>
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
            
            <div class="tags">
                ${recipe.tags ? recipe.tags.map(tag => `<span class="tag">${tag}</span>`).join('') : ''}
                ${recipe.dietary_tags ? recipe.dietary_tags.map(tag => `<span class="tag">${tag}</span>`).join('') : ''}
            </div>
            
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
    
    printRecipe() {
        window.print();
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
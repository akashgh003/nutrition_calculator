import os
import json
import logging
from openai import OpenAI
from typing import Dict, List, Optional, Tuple

logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RecipeFetcher:
    def __init__(self, api_key: Optional[str] = None):

        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("No OpenAI API key provided. Recipe fetching will not work.")
        else:
            self.client = OpenAI(api_key=self.api_key)
    
    def fetch_recipe(self, dish_name: str) -> Dict:

        if not self.api_key:
            logger.error("OpenAI API key not provided. Cannot fetch recipe.")
            return self._get_fallback_recipe(dish_name)
        
        try:

            prompt = self._craft_recipe_prompt(dish_name)

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a knowledgeable Indian cuisine expert."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.5
            )
            
            recipe_data = json.loads(response.choices[0].message.content)

            if not self._validate_recipe_data(recipe_data):
                logger.warning(f"Invalid recipe data for {dish_name}. Using fallback.")
                return self._get_fallback_recipe(dish_name)
            
            logger.info(f"Successfully fetched recipe for {dish_name}")
            return recipe_data
            
        except Exception as e:
            logger.error(f"Error fetching recipe for {dish_name}: {str(e)}")
            return self._get_fallback_recipe(dish_name)
    
    def _craft_recipe_prompt(self, dish_name: str) -> str:

        return f"""
        Generate detailed recipe information for the Indian dish: "{dish_name}".
        
        Please provide the following information in JSON format:
        1. Dish name (the traditional/correct name)
        2. Dish type (e.g., Wet Sabzi, Dry Sabzi, Dal, Rice, Roti/Bread, Non-Veg Curry, Dessert, etc.)
        3. Ingredients list with quantities (using household measurements like cups, tablespoons, teaspoons, etc.)
        4. Estimated total cooked weight in grams
        5. Standard number of servings this recipe yields (typically 4 servings)
        
        IMPORTANT:
        - Use realistic quantities for 4 servings
        - Include all ingredients including oil, spices, water, etc.
        - Be specific with ingredient names
        - List measurements in household units (katori, cups, tablespoons, teaspoons, etc.)
        - Only provide the recipe data, not cooking instructions
        
        Your response must be a valid JSON object with the following structure:
        {{
          "dish_name": "Proper name of the dish",
          "dish_type": "Category of the dish",
          "total_cooked_weight_grams": estimated total weight in grams,
          "servings": number of servings (typically 4),
          "ingredients": [
            {{"name": "Ingredient 1", "quantity": "amount with unit"}},
            {{"name": "Ingredient 2", "quantity": "amount with unit"}},
            ...
          ]
        }}
        """
    
    def _validate_recipe_data(self, recipe_data: Dict) -> bool:

        required_fields = ["dish_name", "dish_type", "ingredients"]

        if not all(field in recipe_data for field in required_fields):
            logger.warning(f"Missing required fields in recipe data. Found: {list(recipe_data.keys())}")
            return False

        if not recipe_data["ingredients"] or len(recipe_data["ingredients"]) == 0:
            logger.warning("Ingredients list is empty")
            return False
  
        for ingredient in recipe_data["ingredients"]:
            if "name" not in ingredient or "quantity" not in ingredient:
                logger.warning(f"Ingredient missing name or quantity: {ingredient}")
                return False
        
        return True
    
    def _get_fallback_recipe(self, dish_name: str) -> Dict:

        common_recipes = {
            "paneer butter masala": {
                "dish_name": "Paneer Butter Masala",
                "dish_type": "Wet Sabzi",
                "total_cooked_weight_grams": 800,
                "servings": 4,
                "ingredients": [
                    {"name": "Paneer", "quantity": "250 grams"},
                    {"name": "Tomato", "quantity": "4 medium"},
                    {"name": "Onion", "quantity": "2 medium"},
                    {"name": "Butter", "quantity": "3 tablespoons"},
                    {"name": "Cream", "quantity": "3 tablespoons"},
                    {"name": "Ginger Garlic Paste", "quantity": "1 tablespoon"},
                    {"name": "Green Chili", "quantity": "2 pieces"},
                    {"name": "Red Chili Powder", "quantity": "1 teaspoon"},
                    {"name": "Turmeric", "quantity": "1/2 teaspoon"},
                    {"name": "Garam Masala", "quantity": "1 teaspoon"},
                    {"name": "Salt", "quantity": "1 teaspoon"},
                    {"name": "Water", "quantity": "1 cup"}
                ]
            },
            "dal makhani": {
                "dish_name": "Dal Makhani",
                "dish_type": "Dal",
                "total_cooked_weight_grams": 900,
                "servings": 4,
                "ingredients": [
                    {"name": "Black Gram (Whole Urad Dal)", "quantity": "1 cup"},
                    {"name": "Kidney Beans (Rajma)", "quantity": "1/4 cup"},
                    {"name": "Butter", "quantity": "3 tablespoons"},
                    {"name": "Cream", "quantity": "2 tablespoons"},
                    {"name": "Onion", "quantity": "1 medium"},
                    {"name": "Tomato", "quantity": "2 medium"},
                    {"name": "Ginger Garlic Paste", "quantity": "1 tablespoon"},
                    {"name": "Red Chili Powder", "quantity": "1 teaspoon"},
                    {"name": "Garam Masala", "quantity": "1 teaspoon"},
                    {"name": "Cumin Seeds", "quantity": "1 teaspoon"},
                    {"name": "Salt", "quantity": "1 teaspoon"},
                    {"name": "Water", "quantity": "4 cups"}
                ]
            },
            "aloo gobi": {
                "dish_name": "Aloo Gobi",
                "dish_type": "Dry Sabzi",
                "total_cooked_weight_grams": 700,
                "servings": 4,
                "ingredients": [
                    {"name": "Potato", "quantity": "3 medium"},
                    {"name": "Cauliflower", "quantity": "1 small"},
                    {"name": "Onion", "quantity": "1 medium"},
                    {"name": "Tomato", "quantity": "1 medium"},
                    {"name": "Oil", "quantity": "2 tablespoons"},
                    {"name": "Cumin Seeds", "quantity": "1 teaspoon"},
                    {"name": "Turmeric", "quantity": "1/2 teaspoon"},
                    {"name": "Red Chili Powder", "quantity": "1 teaspoon"},
                    {"name": "Coriander Powder", "quantity": "1 teaspoon"},
                    {"name": "Garam Masala", "quantity": "1/2 teaspoon"},
                    {"name": "Salt", "quantity": "1 teaspoon"},
                    {"name": "Coriander Leaves", "quantity": "2 tablespoons"}
                ]
            }
        }

        for key, recipe in common_recipes.items():
            if key in dish_name.lower():
                logger.info(f"Using fallback recipe for {dish_name}")
                return recipe
        

        logger.info(f"Using generic fallback recipe for {dish_name}")
        return {
            "dish_name": dish_name.title(),
            "dish_type": "Unknown",
            "total_cooked_weight_grams": 800,
            "servings": 4,
            "ingredients": [
                {"name": "Main Ingredient", "quantity": "2 cups"},
                {"name": "Onion", "quantity": "1 medium"},
                {"name": "Tomato", "quantity": "1 medium"},
                {"name": "Oil", "quantity": "2 tablespoons"},
                {"name": "Salt", "quantity": "1 teaspoon"},
                {"name": "Spices", "quantity": "2 teaspoons"}
            ]
        }

import os
import json
import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for

from utils.recipe_fetcher import RecipeFetcher
from utils.ingredient_processor import IngredientProcessor
from utils.nutrition_calculator import NutritionCalculator
from config import OPENAI_API_KEY, NUTRITION_DB_FILE

logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "nutrition-calculator-app")

recipe_fetcher = RecipeFetcher(OPENAI_API_KEY)
ingredient_processor = IngredientProcessor()
nutrition_calculator = NutritionCalculator(NUTRITION_DB_FILE)

@app.route('/')
def index():

    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():

    try:
        dish_name = request.form.get('dish_name', '')
        if not dish_name:
            return render_template('index.html', error="Please enter a dish name")
        
        logger.info(f"Processing nutrition calculation for dish: {dish_name}")

        recipe_data = recipe_fetcher.fetch_recipe(dish_name)
        if not recipe_data:
            return render_template('index.html', error="Could not fetch recipe. Please try again.")

        processed_ingredients = ingredient_processor.process_ingredients(recipe_data["ingredients"])

        total_cooked_weight = recipe_data.get("total_cooked_weight_grams")
        servings = recipe_data.get("servings", 4)
        
        nutrition_result = nutrition_calculator.calculate_nutrition(
            recipe_data["dish_name"],
            recipe_data["dish_type"],
            processed_ingredients,
            total_cooked_weight,
            servings
        )
        
        logger.info(f"Calculation complete for dish: {dish_name}")

        return render_template('result.html', 
                              dish=nutrition_result, 
                              recipe=recipe_data,
                              processed_ingredients=processed_ingredients)
        
    except Exception as e:
        logger.error(f"Error calculating nutrition: {str(e)}")
        return render_template('index.html', error=f"An error occurred: {str(e)}")

@app.route('/api/calculate', methods=['POST'])
def api_calculate():

    try:
        data = request.get_json()
        
        if not data or 'dish_name' not in data:
            return jsonify({'error': 'Missing dish_name parameter'}), 400
        
        dish_name = data['dish_name']
        logger.info(f"API request for dish: {dish_name}")

        recipe_data = recipe_fetcher.fetch_recipe(dish_name)

        processed_ingredients = ingredient_processor.process_ingredients(recipe_data["ingredients"])

        total_cooked_weight = recipe_data.get("total_cooked_weight_grams")
        servings = recipe_data.get("servings", 4)
        
        nutrition_result = nutrition_calculator.calculate_nutrition(
            recipe_data["dish_name"],
            recipe_data["dish_type"],
            processed_ingredients,
            total_cooked_weight,
            servings
        )
        
        logger.info(f"API calculation complete for dish: {dish_name}")
        
        return jsonify(nutrition_result)
        
    except Exception as e:
        logger.error(f"API error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def page_not_found(e):

    return render_template('index.html', error="Page not found"), 404

@app.errorhandler(500)
def server_error(e):

    return render_template('index.html', error=f"Server error: {str(e)}"), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

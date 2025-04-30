import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
NUTRITION_DB_FILE = "attached_assets/Assignment Inputs - Nutrition source.csv"

FOOD_CATEGORIES = {
    "Wet Sabzi": {"serving_unit": "katori", "serving_grams": 180},
    "Dry Sabzi": {"serving_unit": "katori", "serving_grams": 150},
    "Dal": {"serving_unit": "katori", "serving_grams": 200},
    "Rice": {"serving_unit": "katori", "serving_grams": 150},
    "Roti/Bread": {"serving_unit": "piece", "serving_grams": 30},
    "Non-Veg Curry": {"serving_unit": "katori", "serving_grams": 180},
    "Dessert": {"serving_unit": "katori", "serving_grams": 100},
    "Breakfast Item": {"serving_unit": "plate", "serving_grams": 120},
    "Snack": {"serving_unit": "plate", "serving_grams": 80},
    "Soup": {"serving_unit": "bowl", "serving_grams": 250},
    "Salad": {"serving_unit": "katori", "serving_grams": 100},
    "Chutney/Pickle": {"serving_unit": "teaspoon", "serving_grams": 15},
}

HOUSEHOLD_MEASUREMENTS = {
    "cup": 250,               
    "katori": 200,            
    "glass": 250,             
    "tablespoon": 15,         
    "teaspoon": 5,            
    "piece": 1,              
    "pinch": 0.5,             
    "handful": 30,            
}

DENSITY_FACTORS = {
    "Water": 1.0,            
    "Milk": 1.03,
    "Oil": 0.92,
    "Ghee": 0.91,
    "Flour": 0.55,
    "Sugar": 0.85,
    "Rice": 0.75,
    "Salt": 1.2,
    "Spices": 0.5,
    "Vegetables": 0.6,
    "Leafy Vegetables": 0.3,
    "Default": 0.7,           
}

DEFAULT_RECIPE_SERVINGS = 4

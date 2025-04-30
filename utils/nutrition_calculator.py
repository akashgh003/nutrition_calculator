import logging
from typing import Dict, List, Optional, Union, Any
import math

from utils.db_loader import NutritionDatabaseLoader
from utils.food_classifier import FoodClassifier

logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NutritionCalculator:

    def __init__(self, nutrition_db_path: str):

        self.db_loader = NutritionDatabaseLoader(nutrition_db_path)
        self.nutrition_db = self.db_loader.load_database()
        self.food_classifier = FoodClassifier()

        self.default_nutrition = {
            'calories': 100,
            'carbs': 15,
            'protein': 5,
            'fat': 3,
            'fiber': 2
        }

        self.nutrition_ranges = {
            'calories': {'min': 20, 'max': 900},
            'carbs': {'min': 0, 'max': 90},
            'protein': {'min': 0, 'max': 40},
            'fat': {'min': 0, 'max': 80},
            'fiber': {'min': 0, 'max': 30}
        }
    
    def calculate_nutrition(self, dish_name: str, dish_type: Optional[str], 
                            ingredients: List[Dict], total_cooked_weight: Optional[int] = None,
                            servings: int = 4) -> Dict:

        try:

            ingredient_nutrition = []
            total_raw_weight = 0
            
            for ingredient in ingredients:
                ingredient_name = ingredient.get('name', '')
                grams = ingredient.get('grams', 0)

                if grams is None or grams <= 0:
                    logger.warning(f"Skipping ingredient with invalid weight: {ingredient_name}")
                    continue

                nutrition = self.db_loader.get_ingredient_nutrition(ingredient_name)

                if not nutrition:
                    logger.warning(f"No nutrition data found for: {ingredient_name}. Using defaults.")
                    nutrition = self._get_estimated_nutrition(ingredient_name)

                nutrition_per_serving = self._calculate_scaled_nutrition(nutrition, grams)
                
                ingredient_nutrition.append({
                    'ingredient': ingredient_name,
                    'quantity': ingredient.get('quantity', ''),
                    'grams': grams,
                    'nutrition': nutrition_per_serving
                })

                total_raw_weight += grams
            
            total_nutrition = self._sum_nutrition(ingredient_nutrition)
            
            if total_cooked_weight and total_cooked_weight > 0:
                logger.info(f"Using provided total cooked weight: {total_cooked_weight}g")
                if total_raw_weight > 0 and abs(total_raw_weight - total_cooked_weight) / total_raw_weight > 0.5:
                    logger.warning(f"Large difference between raw ingredients ({total_raw_weight}g) and "
                                  f"cooked weight ({total_cooked_weight}g). This might affect accuracy.")
            else:
                total_cooked_weight = self._estimate_cooked_weight(total_raw_weight, dish_type)
                logger.info(f"Estimated cooked weight: {total_cooked_weight}g from raw weight: {total_raw_weight}g")
            
            dish_classification = self.food_classifier.classify_dish(
                dish_name, dish_type, ingredients
            )
            
            serving_unit = dish_classification.get('serving_unit', 'katori')
            serving_grams = dish_classification.get('serving_grams', 180)
            standard_dish_type = dish_classification.get('dish_type', 'Wet Sabzi')
            
            nutrition_per_serving = self._calculate_nutrition_per_serving(
                total_nutrition, total_cooked_weight, serving_grams, servings
            )
            
            nutrition_per_serving = self._validate_nutrition_values(nutrition_per_serving)
            
            return {
                "dish_name": dish_name,
                "dish_type": standard_dish_type,
                f"estimated_nutrition_per_{serving_unit}": {
                    "calories": round(nutrition_per_serving['calories']),
                    "protein": round(nutrition_per_serving['protein']),
                    "carbs": round(nutrition_per_serving['carbs']),
                    "fat": round(nutrition_per_serving['fat']),
                    "fiber": round(nutrition_per_serving['fiber'], 1)
                },
                "serving_size_grams": serving_grams,
                "total_cooked_weight_grams": total_cooked_weight,
                "servings": servings,
                "ingredients_used": [
                    {
                        "ingredient": item['ingredient'],
                        "quantity": item['quantity']
                    } for item in ingredient_nutrition
                ]
            }
            
        except Exception as e:
            logger.error(f"Error calculating nutrition for {dish_name}: {str(e)}")
            return {
                "dish_name": dish_name,
                "dish_type": dish_type or "Unknown",
                "estimated_nutrition_per_serving": self.default_nutrition,
                "error": f"Calculation error: {str(e)}",
                "ingredients_used": [
                    {"ingredient": ing.get('name', 'unknown'), 
                     "quantity": ing.get('quantity', 'unknown')} 
                    for ing in ingredients if 'name' in ing
                ]
            }
    
    def _get_estimated_nutrition(self, ingredient_name: str) -> Dict:
        categories = {
            'meat': {'calories': 200, 'carbs': 0, 'protein': 25, 'fat': 10, 'fiber': 0},
            'vegetable': {'calories': 50, 'carbs': 10, 'protein': 2, 'fat': 0, 'fiber': 3},
            'grain': {'calories': 350, 'carbs': 70, 'protein': 10, 'fat': 2, 'fiber': 10},
            'dairy': {'calories': 150, 'carbs': 5, 'protein': 8, 'fat': 10, 'fiber': 0},
            'oil': {'calories': 880, 'carbs': 0, 'protein': 0, 'fat': 100, 'fiber': 0},
            'spice': {'calories': 30, 'carbs': 5, 'protein': 1, 'fat': 1, 'fiber': 2},
            'fruit': {'calories': 70, 'carbs': 20, 'protein': 1, 'fat': 0, 'fiber': 2},
            'legume': {'calories': 300, 'carbs': 50, 'protein': 20, 'fat': 5, 'fiber': 15}
        }
        
        ingredient_lower = ingredient_name.lower()
        
        category_mapping = {
            'meat': ['chicken', 'mutton', 'lamb', 'beef', 'pork', 'fish', 'prawn', 'crab', 'meat', 'egg'],
            'vegetable': ['vegetable', 'onion', 'tomato', 'potato', 'carrot', 'cabbage', 'cauliflower', 
                         'eggplant', 'brinjal', 'spinach', 'palak', 'methi', 'capsicum', 'gourd',
                         'beans', 'peas', 'garlic', 'ginger'],
            'grain': ['rice', 'wheat', 'flour', 'atta', 'maida', 'bread', 'roti', 'cereal', 'millet',
                      'barley', 'corn', 'oats', 'quinoa', 'vermicelli', 'noodle', 'pasta'],
            'dairy': ['milk', 'curd', 'yogurt', 'cheese', 'paneer', 'cream', 'butter', 'ghee'],
            'oil': ['oil', 'ghee', 'butter', 'margarine', 'vanaspati', 'fat'],
            'spice': ['spice', 'masala', 'chili', 'pepper', 'cumin', 'coriander', 'turmeric', 
                     'cardamom', 'cinnamon', 'clove', 'bay', 'salt', 'saffron', 'asafoetida'],
            'fruit': ['fruit', 'mango', 'apple', 'banana', 'grapes', 'orange', 'lemon', 'lime',
                     'coconut', 'date', 'raisin', 'berry', 'plum', 'peach'],
            'legume': ['dal', 'lentil', 'pulse', 'chickpea', 'bean', 'soybean', 'rajma', 'chana', 
                      'moong', 'urad', 'masoor', 'tur', 'peas']
        }
        
        for category, keywords in category_mapping.items():
            if any(keyword in ingredient_lower for keyword in keywords):
                logger.info(f"Estimated nutrition for '{ingredient_name}' based on category: '{category}'")
                return {
                    'ingredient': ingredient_name,
                    **categories[category]
                }
        
        logger.warning(f"Using default nutrition values for '{ingredient_name}'")
        return {
            'ingredient': ingredient_name,
            **self.default_nutrition
        }
    
    def _calculate_scaled_nutrition(self, nutrition: Dict, grams: float) -> Dict:

        if not nutrition:
            return self.default_nutrition
        
        scale_factor = grams / 100.0  
        
        return {
            'calories': nutrition['calories'] * scale_factor,
            'carbs': nutrition['carbs'] * scale_factor,
            'protein': nutrition['protein'] * scale_factor,
            'fat': nutrition['fat'] * scale_factor,
            'fiber': nutrition['fiber'] * scale_factor
        }
    
    def _sum_nutrition(self, ingredient_nutrition: List[Dict]) -> Dict:

        total = {
            'calories': 0,
            'carbs': 0,
            'protein': 0,
            'fat': 0,
            'fiber': 0
        }
        
        for item in ingredient_nutrition:
            nutrition = item.get('nutrition', {})
            for key in total:
                total[key] += nutrition.get(key, 0)
        
        return total
    
    def _estimate_cooked_weight(self, raw_weight: float, dish_type: Optional[str] = None) -> int:

        if not dish_type:
            return int(raw_weight)
        
        dish_type_lower = dish_type.lower()
        
        if any(grain in dish_type_lower for grain in ['rice', 'pulao', 'biryani']):
            return int(raw_weight * 2.5)
        
        elif any(dal in dish_type_lower for dal in ['dal', 'sambar', 'lentil']):
            return int(raw_weight * 2.2)
        
        elif any(dry in dish_type_lower for dry in ['dry', 'sukhi', 'bread', 'roti']):
            return int(raw_weight * 0.8)
        
        elif any(curry in dish_type_lower for curry in ['curry', 'gravy', 'sabzi', 'wet']):
            return int(raw_weight * 1.1)
        
        else:

            return int(raw_weight)
    
    def _calculate_nutrition_per_serving(self, total_nutrition: Dict, 
                                         total_weight: float, 
                                         serving_size: float,
                                         servings: int) -> Dict:

        if total_weight <= 0 or serving_size <= 0:
            logger.warning("Invalid weight values for serving calculation. Using defaults.")
            
            return {key: value / servings for key, value in total_nutrition.items()}
        
        scale_factor = serving_size / total_weight
        
        return {key: value * scale_factor for key, value in total_nutrition.items()}
    
    def _validate_nutrition_values(self, nutrition: Dict) -> Dict:
        validated = {}
        
        for nutrient, value in nutrition.items():
            if nutrient in self.nutrition_ranges:
                min_val = self.nutrition_ranges[nutrient]['min']
                max_val = self.nutrition_ranges[nutrient]['max']

                if value < 0:
                    logger.warning(f"Negative {nutrient} value ({value}). Setting to 0.")
                    validated[nutrient] = 0
                elif value > max_val * 5:  
                    logger.warning(f"Extreme {nutrient} value ({value}). Capping to maximum.")
                    validated[nutrient] = max_val
                else:
                    validated[nutrient] = value
            else:
                validated[nutrient] = value
        
        return validated

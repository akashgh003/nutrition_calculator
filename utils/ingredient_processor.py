"""
Module for processing and standardizing ingredient quantities.
"""

import re
import json
import logging
from typing import Dict, List, Tuple, Optional, Any
import os

logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IngredientProcessor:
    def __init__(self, household_measurements_path: str = "data/household_measurements.json"):
        self.measurements_data = self._load_measurements_data(household_measurements_path)
        self.density_mappings = {
            "oil": 0.92,
            "ghee": 0.91,
            "butter": 0.96,
            "milk": 1.03,
            "water": 1.0,
            "cream": 1.0,
            "flour": 0.55,
            "rice": 0.8,
            "sugar": 0.85,
            "salt": 1.2,
            "spices": 0.5,
            "default": 0.7  
        }

        self.quantity_patterns = [
            r'(\d+(?:\.\d+)?)\s*(?:-\s*\d+(?:\.\d+)?)?\s*(tablespoon|tbsp|tbs|cup|teaspoon|tsp|katori|glass|handful|pinch|gram|gm|g|kg|piece|ml|liter|lt|l)s?',
            r'(\d+(?:\.\d+)?)\s*/\s*(\d+)\s+(tablespoon|tbsp|tbs|cup|teaspoon|tsp|katori|glass|handful|pinch|gram|gm|g|kg|piece|ml|liter|lt|l)s?',
            r'(\d+(?:\.\d+)?)',
        ]
        
    def _load_measurements_data(self, file_path: str) -> Dict:
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    return json.load(f)
            else:
                logger.warning(f"Household measurements file not found at {file_path}. Using default values.")
                return {
                    "volume_to_weight": {
                        "cup": {"base_ml": 250, "Default": 250},
                        "katori": {"base_ml": 200, "Default": 200},
                        "glass": {"base_ml": 250, "Default": 250},
                        "tablespoon": {"base_ml": 15, "Default": 15},
                        "teaspoon": {"base_ml": 5, "Default": 5}
                    },
                    "count_to_weight": {
                        "piece": {"Default": 30},
                        "handful": {"Default": 30},
                        "pinch": {"Default": 0.5}
                    }
                }
        except Exception as e:
            logger.error(f"Error loading household measurements data: {str(e)}")
            return {
                "volume_to_weight": {
                    "cup": {"base_ml": 250, "Default": 250},
                    "katori": {"base_ml": 200, "Default": 200},
                    "glass": {"base_ml": 250, "Default": 250},
                    "tablespoon": {"base_ml": 15, "Default": 15},
                    "teaspoon": {"base_ml": 5, "Default": 5}
                },
                "count_to_weight": {
                    "piece": {"Default": 30},
                    "handful": {"Default": 30},
                    "pinch": {"Default": 0.5}
                }
            }
    
    def process_ingredients(self, ingredients: List[Dict]) -> List[Dict]:
        processed_ingredients = []
        
        for ingredient in ingredients:
            try:
                name = ingredient.get('name', '')
                quantity = ingredient.get('quantity', '')
                
                if not name or not quantity:
                    continue
                
                parsed_quantity, parsed_unit = self._parse_quantity(quantity)
                
                if parsed_quantity is None:
                    logger.warning(f"Could not parse quantity for {name}: {quantity}")
                    continue
                
                grams = self._convert_to_grams(parsed_quantity, parsed_unit, name)
                
                processed_ingredients.append({
                    'name': name,
                    'quantity': quantity,
                    'quantity_parsed': parsed_quantity,
                    'unit_parsed': parsed_unit,
                    'grams': grams
                })
                
            except Exception as e:
                logger.error(f"Error processing ingredient {ingredient.get('name', 'unknown')}: {str(e)}")
                processed_ingredients.append({
                    'name': ingredient.get('name', 'unknown'),
                    'quantity': ingredient.get('quantity', ''),
                    'quantity_parsed': None,
                    'unit_parsed': None,
                    'grams': None,
                    'error': str(e)
                })
        
        return processed_ingredients
    
    def _parse_quantity(self, quantity_str: str) -> Tuple[Optional[float], Optional[str]]:
        quantity_str = quantity_str.lower().strip()
        
        for pattern in self.quantity_patterns:
            match = re.search(pattern, quantity_str)
            if match:
                if pattern.startswith(r'(\d+(?:\.\d+)?)\s*/\s*(\d+)'):
                    numerator = float(match.group(1))
                    denominator = float(match.group(2))
                    quantity_value = numerator / denominator
                    unit = match.group(3)
                else:
                    quantity_value = float(match.group(1))
                    unit = match.group(2) if len(match.groups()) > 1 else None
                
                if unit:
                    if unit in ['tablespoon', 'tbsp', 'tbs']:
                        unit = 'tablespoon'
                    elif unit in ['teaspoon', 'tsp']:
                        unit = 'teaspoon'
                    elif unit in ['g', 'gm', 'gram']:
                        unit = 'gram'
                    elif unit in ['kg', 'kilogram']:
                        unit = 'kilogram'
                        quantity_value *= 1000  
                    elif unit in ['ml', 'milliliter']:
                        unit = 'ml'
                    elif unit in ['l', 'lt', 'liter']:
                        unit = 'liter'
                        quantity_value *= 1000  
                else:
                    unit = 'piece'
                
                return quantity_value, unit
        

        return None, None
    
    def _convert_to_grams(self, quantity: float, unit: str, ingredient_name: str) -> float:
        if unit in ['gram', 'g', 'gm']:
            return quantity
        elif unit in ['kilogram', 'kg']:
            return quantity * 1000

        if unit in ['ml', 'milliliter']:
            density = self._get_density_for_ingredient(ingredient_name)
            return quantity * density
        elif unit in ['liter', 'l', 'lt']:
            density = self._get_density_for_ingredient(ingredient_name)
            return quantity * 1000 * density

        volume_mappings = self.measurements_data.get("volume_to_weight", {})
        if unit in volume_mappings:

            base_ml = volume_mappings[unit].get("base_ml", 0)

            ingredient_type = self._get_ingredient_type(ingredient_name)

            weight_in_grams = volume_mappings[unit].get(ingredient_type, 
                                                      volume_mappings[unit].get("Default", base_ml * 0.8))
            
            return quantity * weight_in_grams

        count_mappings = self.measurements_data.get("count_to_weight", {})
        if unit in count_mappings:

            specific_weight = None
            for ingredient_type, weight in count_mappings[unit].items():
                if ingredient_type.lower() in ingredient_name.lower():
                    specific_weight = weight
                    break

            if specific_weight is None:
                specific_weight = count_mappings[unit].get("Default", 30) 
            
            return quantity * specific_weight
        
        logger.warning(f"Unrecognized unit '{unit}' for {ingredient_name}. Assuming 'piece'.")
        
        common_weights = {
            "onion": 100,
            "tomato": 80,
            "potato": 150,
            "green chili": 5,
            "garlic clove": 3,
            "egg": 50,
            "lemon": 60,
            "default": 30
        }

        for ingredient, weight in common_weights.items():
            if ingredient in ingredient_name.lower():
                return quantity * weight

        return quantity * common_weights["default"]
    
    def _get_density_for_ingredient(self, ingredient_name: str) -> float:
        ingredient_lower = ingredient_name.lower()
        
        for key, density in self.density_mappings.items():
            if key in ingredient_lower:
                return density
        
        return self.density_mappings["default"]
    
    def _get_ingredient_type(self, ingredient_name: str) -> str:
        ingredient_lower = ingredient_name.lower()

        mappings = {
            "oil": "Oil",
            "ghee": "Ghee",
            "butter": "Butter",
            "milk": "Milk",
            "cream": "Cream",
            "flour": "Flour",
            "rice": "Rice",
            "sugar": "Sugar",
            "salt": "Salt",
            "chili powder": "Spices",
            "turmeric": "Spices",
            "garam masala": "Spices",
            "cumin": "Spices",
            "coriander": "Spices",
            "spice": "Spices",
            "onion": "Vegetables Chopped",
            "tomato": "Vegetables Chopped",
            "potato": "Vegetables Chopped",
            "carrot": "Vegetables Chopped",
            "capsicum": "Vegetables Chopped",
            "spinach": "Leafy Vegetables",
            "methi": "Leafy Vegetables",
            "palak": "Leafy Vegetables",
            "coriander leaves": "Leafy Vegetables",
            "cilantro": "Leafy Vegetables",
            "dal": "Pulses",
            "lentil": "Pulses",
            "chicken": "Meat",
            "mutton": "Meat",
            "fish": "Meat",
            "paneer": "Paneer"
        }

        for keyword, category in mappings.items():
            if keyword in ingredient_lower:
                return category

        if any(word in ingredient_lower for word in ["water", "liquid", "juice", "soup"]):
            return "Wet Ingredients"

        return "Dry Ingredients"

import logging
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FoodClassifier:

    def __init__(self):

        self.food_categories = {
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
            "Chutney/Pickle": {"serving_unit": "teaspoon", "serving_grams": 15}
        }

        self.category_keywords = {
            "Wet Sabzi": ["curry", "gravy", "masala", "kofta", "butter", "makhani", 
                         "korma", "kadhai", "sabji", "sabzi", "saag", "paneer"],
            "Dry Sabzi": ["dry", "sukhi", "fry", "bhaji", "roast", "aloo", "gobi", 
                         "bhindi", "baingan", "matar", "shimla mirch", "poriyal"],
            "Dal": ["dal", "daal", "sambar", "lentil", "rajma", "chole", "chana", 
                   "beans", "moong", "toor", "urad"],
            "Rice": ["rice", "pulao", "biryani", "khichdi", "chawal", "bhaat", 
                    "fried rice", "jeera rice"],
            "Roti/Bread": ["roti", "chapati", "naan", "paratha", "kulcha", "bhakri", 
                          "phulka", "poori", "bread", "parotta"],
            "Non-Veg Curry": ["chicken", "mutton", "lamb", "fish", "prawn", "egg", 
                             "seafood", "meat", "keema", "korma", "non-veg"],
            "Dessert": ["kheer", "halwa", "barfi", "ladoo", "jalebi", "gulab jamun", 
                       "rasmalai", "rasgulla", "payasam", "sweet", "dessert", "mithai"],
            "Breakfast Item": ["upma", "poha", "idli", "dosa", "uttapam", "vada", 
                              "breakfast", "paratha", "sandwich", "cheela"],
            "Snack": ["pakora", "bhajji", "samosa", "chaat", "kachori", "tikki", 
                     "snack", "namkeen", "bhel", "puri", "golgappa", "dhokla"],
            "Soup": ["soup", "shorba", "rasam", "yakhni"],
            "Salad": ["salad", "koshimbir", "raita", "kosambari", "pacchadi"],
            "Chutney/Pickle": ["chutney", "pickle", "achar", "relish", "thecha", "pachadi"]
        }
    
    def classify_dish(self, dish_name: str, dish_type: Optional[str] = None, 
                      ingredients: Optional[List[Dict]] = None) -> Dict:
        if dish_type and dish_type in self.food_categories:
            logger.info(f"Using provided dish type: {dish_type} for {dish_name}")
            return {
                "dish_type": dish_type,
                **self.food_categories[dish_type]
            }

        matched_category = self._match_dish_name(dish_name)

        if not matched_category and ingredients:
            matched_category = self._match_from_ingredients(ingredients)

        if not matched_category and dish_type:
            matched_category = self._map_custom_type_to_standard(dish_type)
        
        if not matched_category:
            logger.warning(f"Could not classify dish: {dish_name}. Defaulting to 'Wet Sabzi'")
            matched_category = "Wet Sabzi"
        
        return {
            "dish_type": matched_category,
            **self.food_categories[matched_category]
        }
    
    def _match_dish_name(self, dish_name: str) -> Optional[str]:
        dish_lower = dish_name.lower()

        max_matches = 0
        best_category = None
        
        for category, keywords in self.category_keywords.items():
            matches = sum(1 for keyword in keywords if keyword.lower() in dish_lower)
            
            if matches > max_matches:
                max_matches = matches
                best_category = category
        
        if best_category:
            logger.info(f"Matched dish '{dish_name}' to category '{best_category}' based on name")
            return best_category
        
        return None
    
    def _match_from_ingredients(self, ingredients: List[Dict]) -> Optional[str]:

        ingredient_names = [ingredient.get("name", "").lower() for ingredient in ingredients]

        category_scores = {category: 0 for category in self.food_categories}

        non_veg_ingredients = ["chicken", "mutton", "lamb", "beef", "fish", "prawn", "crab", "egg"]
        if any(any(item in ing for ing in ingredient_names) for item in non_veg_ingredients):
            category_scores["Non-Veg Curry"] += 5
        
        dal_ingredients = ["dal", "lentil", "rajma", "chole", "chana", "beans", "pulse"]
        if any(any(item in ing for ing in ingredient_names) for item in dal_ingredients):
            category_scores["Dal"] += 5
        
        rice_ingredients = ["rice", "chawal", "basmati"]
        if any(any(item in ing for ing in ingredient_names) for item in rice_ingredients):
            category_scores["Rice"] += 5
        
        roti_ingredients = ["flour", "atta", "maida"]
        if any(any(item in ing for ing in ingredient_names) for item in roti_ingredients):
            category_scores["Roti/Bread"] += 5
        
        if any("paneer" in ing for ing in ingredient_names):
            category_scores["Wet Sabzi"] += 3
        
        sweet_ingredients = ["sugar", "jaggery", "syrup", "honey", "condensed milk", "khoya"]
        if any(any(item in ing for ing in ingredient_names) for item in sweet_ingredients):
            category_scores["Dessert"] += 4
        
        gravy_ingredients = ["water", "milk", "cream", "curd", "yogurt", "tomato puree"]
        has_gravy = any(any(item in ing for ing in ingredient_names) for item in gravy_ingredients)
        
        if has_gravy:
            category_scores["Wet Sabzi"] += 2
        else:
            category_scores["Dry Sabzi"] += 2
        
        best_category = max(category_scores.items(), key=lambda x: x[1])
        
        if best_category[1] > 0:
            logger.info(f"Matched to category '{best_category[0]}' based on ingredients")
            return best_category[0]
        
        return None
    
    def _map_custom_type_to_standard(self, custom_type: str) -> Optional[str]:
        custom_lower = custom_type.lower()
        
        for category, keywords in self.category_keywords.items():
            if any(keyword.lower() in custom_lower for keyword in keywords):
                logger.info(f"Mapped custom type '{custom_type}' to standard category '{category}'")
                return category
        
        mappings = {
            "vegetable": "Wet Sabzi",
            "veg": "Wet Sabzi",
            "curry": "Wet Sabzi",
            "sabji": "Wet Sabzi", 
            "sabzi": "Wet Sabzi",
            "curry": "Wet Sabzi",
            "gravy": "Wet Sabzi",
            "main course": "Wet Sabzi",
            "side dish": "Dry Sabzi",
            "pulse": "Dal",
            "daal": "Dal",
            "bread": "Roti/Bread",
            "flatbread": "Roti/Bread",
            "meat": "Non-Veg Curry",
            "non-vegetarian": "Non-Veg Curry",
            "sweet": "Dessert",
            "mithai": "Dessert",
            "starter": "Snack",
            "appetizer": "Snack"
        }
        
        for key, value in mappings.items():
            if key in custom_lower:
                logger.info(f"Mapped custom type '{custom_type}' to standard category '{value}'")
                return value
        
        return None

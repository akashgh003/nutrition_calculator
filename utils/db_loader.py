import os
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NutritionDatabaseLoader:

    def __init__(self, db_path):
        self.db_path = db_path
        self.nutrition_df = None
        
    def load_database(self):
        try:
            if not os.path.exists(self.db_path):
                logger.error(f"Database file not found at: {self.db_path}")
                raise FileNotFoundError(f"Database file not found at: {self.db_path}")

            self.nutrition_df = pd.read_csv(self.db_path)

            self._prepare_dataframe()
            
            logger.info(f"Successfully loaded nutrition database with {len(self.nutrition_df)} entries")
            return self.nutrition_df
            
        except Exception as e:
            logger.error(f"Error loading nutrition database: {str(e)}")
            raise
    
    def _prepare_dataframe(self):
        if self.nutrition_df is None:
            return
        

        essential_columns = ['food_code', 'food_name', 'energy_kcal', 'carb_g', 
                            'protein_g', 'fat_g', 'fibre_g']

        missing_columns = [col for col in essential_columns if col not in self.nutrition_df.columns]
        if missing_columns:
            logger.warning(f"Missing essential columns in nutrition database: {missing_columns}")

            for col in missing_columns:
                self.nutrition_df[col] = float('nan')

        try:
            self.nutrition_df = self.nutrition_df[essential_columns]
            
            self.nutrition_df['food_name_lower'] = self.nutrition_df['food_name'].str.lower()

            numerical_columns = ['energy_kcal', 'carb_g', 'protein_g', 'fat_g', 'fibre_g']
            self.nutrition_df[numerical_columns] = self.nutrition_df[numerical_columns].fillna(0)
            
        except Exception as e:
            logger.error(f"Error preparing nutrition dataframe: {str(e)}")
            raise
    
    def get_ingredient_nutrition(self, ingredient_name):
        if self.nutrition_df is None:
            logger.warning("Nutrition database not loaded. Loading now...")
            self.load_database()

        ingredient_lower = ingredient_name.lower()

        matches = self.nutrition_df[self.nutrition_df['food_name_lower'] == ingredient_lower]

        if len(matches) == 0:
            matches = self.nutrition_df[self.nutrition_df['food_name_lower'].str.contains(ingredient_lower)]

        if len(matches) == 0:
            words = ingredient_lower.split()
            if len(words) > 1:  
                for word in words:
                    if len(word) > 3:  
                        word_matches = self.nutrition_df[self.nutrition_df['food_name_lower'].str.contains(word)]
                        if len(word_matches) > 0:
                            matches = word_matches
                            logger.info(f"Found partial match for '{ingredient_name}' using word '{word}'")
                            break
        
        if len(matches) > 0:

            if len(matches) > 1:
                logger.info(f"Multiple matches found for '{ingredient_name}'. Using first match: '{matches.iloc[0]['food_name']}'")

            nutrition_data = matches.iloc[0].to_dict()
            return {
                'ingredient': matches.iloc[0]['food_name'],
                'calories': nutrition_data['energy_kcal'],
                'carbs': nutrition_data['carb_g'],
                'protein': nutrition_data['protein_g'],
                'fat': nutrition_data['fat_g'],
                'fiber': nutrition_data['fibre_g']
            }
        else:
            logger.warning(f"No match found for ingredient: '{ingredient_name}'")
            return None

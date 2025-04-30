import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.nutrition_calculator import NutritionCalculator
from utils.db_loader import NutritionDatabaseLoader

class TestNutritionCalculator(unittest.TestCase):

    def setUp(self):
        self.mock_db_loader = MagicMock(spec=NutritionDatabaseLoader)
        self.mock_db_loader.load_database.return_value = "mocked_df"

        with patch('utils.nutrition_calculator.NutritionDatabaseLoader', return_value=self.mock_db_loader):
            self.calculator = NutritionCalculator("dummy_path")
    
    def test_estimate_cooked_weight(self):

        self.assertEqual(self.calculator._estimate_cooked_weight(100, "rice"), 250)
        self.assertEqual(self.calculator._estimate_cooked_weight(100, "dal"), 220)
        self.assertEqual(self.calculator._estimate_cooked_weight(100, "dry sabzi"), 80)
        self.assertEqual(self.calculator._estimate_cooked_weight(100, "curry"), 110)
        self.assertEqual(self.calculator._estimate_cooked_weight(100, None), 100)
    
    def test_calculate_scaled_nutrition(self):

        sample_nutrition = {
            'ingredient': 'Test Ingredient',
            'calories': 100,
            'carbs': 10,
            'protein': 5,
            'fat': 2,
            'fiber': 3
        }

        scaled = self.calculator._calculate_scaled_nutrition(sample_nutrition, 200)
        
        self.assertEqual(scaled['calories'], 200)
        self.assertEqual(scaled['carbs'], 20)
        self.assertEqual(scaled['protein'], 10)
        self.assertEqual(scaled['fat'], 4)
        self.assertEqual(scaled['fiber'], 6)
        
        scaled_none = self.calculator._calculate_scaled_nutrition(None, 100)
        self.assertEqual(scaled_none, self.calculator.default_nutrition)
    
    def test_validate_nutrition_values(self):
        normal_values = {
            'calories': 300,
            'carbs': 30,
            'protein': 15,
            'fat': 10,
            'fiber': 5
        }
        
        validated = self.calculator._validate_nutrition_values(normal_values)
        self.assertEqual(validated, normal_values)
        
        negative_values = {
            'calories': -100,
            'carbs': 30,
            'protein': -5,
            'fat': 10,
            'fiber': 5
        }
        
        validated = self.calculator._validate_nutrition_values(negative_values)
        self.assertEqual(validated['calories'], 0)
        self.assertEqual(validated['protein'], 0)

        extreme_values = {
            'calories': 10000, 
            'carbs': 30,
            'protein': 15,
            'fat': 10,
            'fiber': 5
        }
        
        validated = self.calculator._validate_nutrition_values(extreme_values)
        self.assertEqual(validated['calories'], 900)  

if __name__ == '__main__':
    unittest.main()

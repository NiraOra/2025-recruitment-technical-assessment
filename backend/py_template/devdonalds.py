from dataclasses import dataclass
from typing import List, Dict, Union
from flask import Flask, request, jsonify
import re

# ==== Type Definitions, feel free to add or modify ===========================
@dataclass
class CookbookEntry:
	name: str

@dataclass
class RequiredItem():
	name: str
	quantity: int

@dataclass
class Recipe(CookbookEntry):
	required_items: List[RequiredItem]

@dataclass
class Ingredient(CookbookEntry):
	cook_time: int


# =============================================================================
# ==== HTTP Endpoint Stubs ====================================================
# =============================================================================
app = Flask(__name__)

# Store your recipes here!
cookbook = {}

# Task 1 helper (don't touch)
@app.route("/parse", methods=['POST'])
def parse():
	data = request.get_json()
	recipe_name = data.get('input', '')
	parsed_name = parse_handwriting(recipe_name)
	if parsed_name is None:
		return 'Invalid recipe name', 400
	return jsonify({'msg': parsed_name}), 200

# [TASK 1] ====================================================================
# Takes in a recipeName and returns it in a form that 
def parse_handwriting(recipeName: str) -> Union[str | None]:
    # p1: hyphen + underscore to whitespace
    # p2: only a-z or A-Z chars + make first letter of each word caps
    # p3: check for whitespaces and make it singular
    recipeName = re.sub(r'[-_]', ' ', recipeName)
    recipeName = re.sub(r'[^a-zA-Z ]', '', recipeName)
    recipeName = re.sub(r'\s+', ' ', recipeName).strip()
    recipeName = recipeName.title()
    # special case: return None if length == 0
    return recipeName if recipeName else None


# [TASK 2] ====================================================================
# Endpoint that adds a CookbookEntry to your magical cookbook
@app.route('/entry', methods=['POST'])
def create_entry():
    # Get all data in json format
	data = request.get_json()
	type_ = data.get('type')
	name = data.get('name')

	# INTERMEDIATE CHECKS: 200 if all successful + added
	# 1. Check if the name is a string or not (additional check)
	# 2. Check if the name already exists
	# 3. Check if the type sent is an ingredient or a recipe
	# 4. Check if the requiredItems in the recipe only has one element

	# ELSE, returning 400
	if not isinstance(name, str) or not name:
		return 'Invalid name.', 400
	if name in cookbook:
		return 'Please make entry names unique!', 400
	if type_ == "recipe":
		required_items = data.get('requiredItems', [])
		
		# NOTE: seenitems is a set to check if items only have one element; duplicate check
		seen_items = set()
		for item in required_items:
			if not isinstance(item, dict) or 'name' not in item or 'quantity' not in item:
				return 'requiredItems should consist of name and quantity, try again!', 400
			if item['name'] in seen_items:
				return 'Items can only have one element per name', 400
			seen_items.add(item['name'])
		# Adding new Recipe
		cookbook[name] = Recipe(name, required_items)
	elif type_ == "ingredient":
		cook_time = data.get('cookTime')
		if not isinstance(cook_time, int) or cook_time < 0:
			return 'The cooking time should be greater than or equal to zero.', 400
		# Adding new Ingredient
		cookbook[name] = Ingredient(name, cook_time)
	else:
		return 'You can only add recipes or ingredients into the cookbook.', 400

	# Added successfully!
	return '', 200


# [TASK 3] ====================================================================
# Endpoint that returns a summary of a recipe that corresponds to a query name
@app.route('/summary', methods=['GET'])
def summary():
	recipe_name = request.args.get('name')

	# Check if the recipe exists in the cookbook
	if recipe_name not in cookbook or not isinstance(cookbook[recipe_name], Recipe):
		return 'Recipe not found or is not a recipe', 400

	recipe = cookbook[recipe_name]

	# Recursively get total cook time and base ingredients
	def get_recipe_summary(recipe, multiplier=1):
		total_cook_time = 0
		ingredients_map = {}

		for item in recipe.required_items:
			item_name = item.name
			quantity = item.quantity * multiplier

			if item_name not in cookbook:
				return None, None  # Recipe contains an unknown item
	
			entry = cookbook[item_name]

			if isinstance(entry, Ingredient):
				total_cook_time += entry.cook_time * quantity
				if item_name in ingredients_map:
					ingredients_map[item_name] += quantity
				else:
					ingredients_map[item_name] = quantity

			elif isinstance(entry, Recipe):
				sub_cook_time, sub_ingredients = get_recipe_summary(entry, quantity)
				if sub_cook_time is None:
					return None, None  # Found an unknown item

				total_cook_time += sub_cook_time
				for ing, qty in sub_ingredients.items():
					if ing in ingredients_map:
						ingredients_map[ing] += qty
					else:
						ingredients_map[ing] = qty

		return total_cook_time, ingredients_map

	total_cook_time, ingredients_map = get_recipe_summary(recipe)

	if total_cook_time is None:
		return 'Recipe contains unknown items', 400

	ingredients_list = [{"name": name, "quantity": quantity} for name, quantity in ingredients_map.items()]

	return jsonify({
		"name": recipe.name,
		"cookTime": total_cook_time,
		"ingredients": ingredients_list
	}), 200


# =============================================================================
# ==== DO NOT TOUCH ===========================================================
# =============================================================================

if __name__ == '__main__':
	app.run(debug=True, port=8080)

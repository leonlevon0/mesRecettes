#!/usr/bin/env python3
"""
Script pour générer automatiquement le fichier recettes-data.json
à partir des fichiers .qmd dans le dossier recettes/

Usage: python generate-recipes-json.py
"""

import os
import json
import re
from pathlib import Path


def parse_yaml_frontmatter(content):
    """Extraire le frontmatter YAML d'un fichier .qmd"""
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if not match:
        return None

    yaml_content = match.group(1)
    metadata = {}

    # Parser simple pour YAML (juste ce dont on a besoin)
    current_key = None
    list_mode = False

    for line in yaml_content.split('\n'):
        line = line.rstrip()

        # Détecter les clés principales
        if ':' in line and not line.strip().startswith('-'):
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip().strip('"\'')

            if value.startswith('['):
                # Liste inline [item1, item2]
                value = value.strip('[]')
                items = [item.strip().strip('"\'') for item in value.split(',')]
                metadata[key] = items
            elif value:
                # Valeur simple
                metadata[key] = value
            else:
                # Début d'une liste sur plusieurs lignes
                current_key = key
                metadata[key] = []
                list_mode = True

        # Détecter les éléments de liste
        elif line.strip().startswith('-') and list_mode:
            item = line.strip()[1:].strip().strip('"\'')
            if current_key:
                metadata[current_key].append(item)

    return metadata


def extract_ingredients(content):
    """Extraire la liste des ingrédients du contenu markdown"""
    # Chercher la section "Ingrédients"
    match = re.search(r'##\s+Ingrédients\s*\n(.*?)(?=\n##|\Z)', content, re.DOTALL | re.IGNORECASE)
    if not match:
        return []

    ingredients_section = match.group(1)

    # Extraire les items de la liste (lignes commençant par -)
    ingredients = []
    for line in ingredients_section.split('\n'):
        line = line.strip()
        if line.startswith('-'):
            ingredient = line[1:].strip()
            if ingredient:
                ingredients.append(ingredient)

    return ingredients


def generate_recipe_id(filepath):
    """Générer un ID unique pour la recette basé sur le nom du fichier"""
    return Path(filepath).stem


def parse_recipe_file(filepath):
    """Parser un fichier .qmd et extraire les données de la recette"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extraire le frontmatter
        metadata = parse_yaml_frontmatter(content)
        if not metadata:
            print(f"WARNING: Pas de frontmatter trouve dans {filepath}")
            return None

        # Extraire les ingrédients du contenu
        ingredients = extract_ingredients(content)

        # Construire l'objet recette
        recipe = {
            'id': generate_recipe_id(filepath),
            'title': metadata.get('title', 'Sans titre'),
            'category': metadata.get('categories', ['autre'])[0] if isinstance(metadata.get('categories'), list) else metadata.get('categories', 'autre'),
            'servings': int(metadata.get('servings', 4)),
            'ingredients': ingredients
        }

        return recipe

    except Exception as e:
        print(f"ERROR: Erreur lors du parsing de {filepath}: {e}")
        return None


def generate_recipes_json(recipes_dir='recettes', output_file='recettes/recettes-data.json'):
    """Générer le fichier JSON avec toutes les recettes"""
    recipes = []

    # Parcourir tous les fichiers .qmd dans le dossier recettes
    recipes_path = Path(recipes_dir)

    if not recipes_path.exists():
        print(f"ERROR: Le dossier {recipes_dir} n'existe pas!")
        return

    qmd_files = list(recipes_path.glob('*.qmd'))

    # Exclure le template
    qmd_files = [f for f in qmd_files if f.name != '_template.qmd']

    print(f"Trouve {len(qmd_files)} fichier(s) .qmd a traiter...")

    for filepath in sorted(qmd_files):
        print(f"Traitement de {filepath.name}...")
        recipe = parse_recipe_file(filepath)

        if recipe:
            recipes.append(recipe)
            print(f"  OK: {recipe['title']} - {len(recipe['ingredients'])} ingredients")

    # Écrire le fichier JSON
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(recipes, f, ensure_ascii=False, indent=2)

    print(f"\nSUCCESS: Fichier {output_file} genere avec succes!")
    print(f"Total: {len(recipes)} recette(s) exportee(s)")


if __name__ == '__main__':
    generate_recipes_json()

"""Escolhe automaticamente o backend de dados:
- Se NOTION_TOKEN estiver definido -> usa o Notion (notion_db.py)
- Caso contrário -> usa um ficheiro JSON local (local_db.py), para testares
  a app no PC sem precisares de configurar o Notion.

O app.py e as rotas usam sempre `data_store`, nunca diretamente notion_db ou local_db.
"""
import os

USING_NOTION = bool(os.environ.get("NOTION_TOKEN"))

if USING_NOTION:
    from notion_db import (  # noqa: F401
        configured, get_profile, save_profile,
        add_meal, get_meals_between, get_meals_for_day, get_meal, update_meal, delete_meal,
        get_pantry, add_pantry_item, delete_pantry_item,
        get_excluidos, add_excluido, delete_excluido,
        add_weight, get_weight_history,
        add_exercise, get_exercise_between,
        get_push_subscriptions, add_push_subscription, delete_push_subscription,
        get_custom_recipes, add_custom_recipe, delete_custom_recipe,
        get_custom_recipe, update_custom_recipe,
    )
    BACKEND_NAME = "Notion"
else:
    from local_db import (  # noqa: F401
        configured, get_profile, save_profile,
        add_meal, get_meals_between, get_meals_for_day, get_meal, update_meal, delete_meal,
        get_pantry, add_pantry_item, delete_pantry_item,
        get_excluidos, add_excluido, delete_excluido,
        add_weight, get_weight_history,
        add_exercise, get_exercise_between,
        get_push_subscriptions, add_push_subscription, delete_push_subscription,
        get_custom_recipes, add_custom_recipe, delete_custom_recipe,
        get_custom_recipe, update_custom_recipe,
    )
    BACKEND_NAME = "Local (ficheiro JSON, modo teste)"

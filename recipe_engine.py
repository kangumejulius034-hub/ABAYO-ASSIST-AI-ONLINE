from pathlib import Path
from typing import Any

from storage.json_store import load_json, save_json


BASE_DIR = Path(__file__).resolve().parent
RECIPES_FILE = BASE_DIR / "knowledge" / "recipes.json"


def load_recipes() -> list[dict[str, Any]]:
    """Load all recipe records safely."""

    data = load_json(RECIPES_FILE, [])
    if not isinstance(data, list):
        return []
    return [record for record in data if isinstance(record, dict)]


def save_all_recipes(recipes: list[dict[str, Any]]) -> None:
    """Save the complete recipe database."""

    save_json(RECIPES_FILE, recipes)


def recipe_sort_key(recipe_name: str) -> tuple[int, str]:
    """Sort recipe names by their numerical weight."""

    number_text = "".join(character for character in recipe_name if character.isdigit())
    if number_text:
        return int(number_text), recipe_name
    return 999999, recipe_name


def recipe_belongs_to_machine(
    recipe: dict[str, Any],
    *,
    machine_id: Any | None = None,
    machine_model: str = "",
    allow_legacy: bool = False,
) -> bool:
    """Return whether a recipe belongs to the selected machine.

    New records are isolated by database machine_id. Legacy records have no
    machine_id; they may only be exposed when a page explicitly opts into
    legacy data (used for the original Pakona profile).
    """

    saved_id = recipe.get("machine_id")

    if machine_id not in (None, ""):
        if saved_id not in (None, ""):
            return str(saved_id) == str(machine_id)
        if not allow_legacy:
            return False

    if machine_model:
        saved_model = str(recipe.get("machine_model") or recipe.get("machine") or "").strip()
        return saved_model.lower() == machine_model.strip().lower()

    return bool(allow_legacy or machine_id in (None, ""))


def recipes_for_machine(
    *,
    machine_id: Any | None,
    machine_model: str = "",
    allow_legacy: bool = False,
) -> list[dict[str, Any]]:
    """Return only recipes belonging to one machine profile."""

    return [
        recipe
        for recipe in load_recipes()
        if recipe_belongs_to_machine(
            recipe,
            machine_id=machine_id,
            machine_model=machine_model,
            allow_legacy=allow_legacy,
        )
    ]


def list_recipe_names(
    machine_model: str = "",
    *,
    machine_id: Any | None = None,
    allow_legacy: bool = False,
) -> list[str]:
    """Return recipe names belonging to one machine."""

    recipes = recipes_for_machine(
        machine_id=machine_id,
        machine_model=machine_model,
        allow_legacy=allow_legacy,
    )

    names = [
        str(recipe.get("recipe_name") or "")
        for recipe in recipes
        if recipe.get("recipe_name")
    ]
    return sorted(set(names), key=recipe_sort_key)


def get_recipe(
    machine_model: str,
    recipe_name: str,
    *,
    machine_id: Any | None = None,
    allow_legacy: bool = False,
) -> dict[str, Any] | None:
    """Find one recipe by selected machine and recipe name."""

    requested_name = recipe_name.strip().lower()

    for recipe in recipes_for_machine(
        machine_id=machine_id,
        machine_model=machine_model,
        allow_legacy=allow_legacy,
    ):
        saved_name = str(recipe.get("recipe_name") or "").strip().lower()
        if saved_name == requested_name:
            return recipe
    return None


def save_recipe(
    machine_model: str,
    recipe_name: str,
    status: str,
    parameters: dict[str, Any],
    notes: str,
    hmi_images: list[str] | None = None,
    *,
    machine_id: Any | None = None,
) -> str:
    """Create or update a recipe scoped to one machine."""

    recipes = load_recipes()
    clean_name = recipe_name.strip()

    for index, recipe in enumerate(recipes):
        saved_id = recipe.get("machine_id")
        if machine_id not in (None, ""):
            same_machine = saved_id not in (None, "") and str(saved_id) == str(machine_id)
        else:
            same_machine = str(recipe.get("machine_model") or "") == machine_model

        same_recipe = str(recipe.get("recipe_name") or "").strip().lower() == clean_name.lower()

        if same_machine and same_recipe:
            existing_images = recipe.get("hmi_images", [])
            combined_images = list(dict.fromkeys(existing_images + (hmi_images or [])))
            updated = dict(recipe)
            updated.update(
                {
                    "machine_id": machine_id,
                    "machine_model": machine_model,
                    "recipe_name": clean_name,
                    "status": status,
                    "parameters": parameters,
                    "notes": notes.strip(),
                    "hmi_images": combined_images,
                }
            )
            recipes[index] = updated
            save_all_recipes(recipes)
            return "updated"

    new_record = {
        "machine_id": machine_id,
        "machine_model": machine_model,
        "recipe_name": clean_name,
        "status": status,
        "parameters": parameters,
        "notes": notes.strip(),
        "hmi_images": hmi_images or [],
    }
    recipes.append(new_record)
    save_all_recipes(recipes)
    return "created"

from pathlib import Path
from typing import Any

from storage.json_store import load_json, save_json

BASE_DIR = Path(__file__).resolve().parent
RECIPES_FILE = BASE_DIR / "knowledge" / "recipes.json"


def _selected_scope(
    machine_id: Any | None,
    machine_model: str,
    allow_legacy: bool,
) -> tuple[Any | None, str, bool]:
    """Use the globally selected machine when an older page omits machine_id."""
    if machine_id not in (None, ""):
        return machine_id, machine_model, allow_legacy
    try:
        from core.machine_context import (
            current_machine,
            is_pakona_machine,
            machine_model_label,
            selected_machine_id,
        )
        selected_id = selected_machine_id()
        if selected_id in (None, ""):
            return machine_id, machine_model, allow_legacy
        machine = current_machine()
        return selected_id, machine_model_label(machine), is_pakona_machine(machine)
    except Exception:
        return machine_id, machine_model, allow_legacy


def load_recipes() -> list[dict[str, Any]]:
    data = load_json(RECIPES_FILE, [])
    if not isinstance(data, list):
        return []
    return [record for record in data if isinstance(record, dict)]


def save_all_recipes(recipes: list[dict[str, Any]]) -> None:
    save_json(RECIPES_FILE, recipes)


def recipe_sort_key(recipe_name: str) -> tuple[int, str]:
    digits = "".join(character for character in recipe_name if character.isdigit())
    if digits:
        return int(digits), recipe_name
    return 999999, recipe_name


def recipe_belongs_to_machine(
    recipe: dict[str, Any],
    *,
    machine_id: Any | None = None,
    machine_model: str = "",
    allow_legacy: bool = False,
) -> bool:
    machine_id, machine_model, allow_legacy = _selected_scope(
        machine_id, machine_model, allow_legacy
    )
    saved_id = recipe.get("machine_id")
    if machine_id not in (None, ""):
        if saved_id not in (None, ""):
            return str(saved_id) == str(machine_id)
        return allow_legacy
    if machine_model:
        saved_model = str(
            recipe.get("machine_model") or recipe.get("machine") or ""
        ).strip()
        return saved_model.lower() == machine_model.strip().lower()
    return True


def recipes_for_machine(
    *,
    machine_id: Any | None = None,
    machine_model: str = "",
    allow_legacy: bool = False,
) -> list[dict[str, Any]]:
    machine_id, machine_model, allow_legacy = _selected_scope(
        machine_id, machine_model, allow_legacy
    )
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
    machine_id, machine_model, _ = _selected_scope(
        machine_id, machine_model, False
    )
    recipes = load_recipes()
    clean_name = recipe_name.strip()

    for index, recipe in enumerate(recipes):
        saved_id = recipe.get("machine_id")
        if machine_id not in (None, ""):
            same_machine = (
                saved_id not in (None, "")
                and str(saved_id) == str(machine_id)
            )
        else:
            same_machine = str(recipe.get("machine_model") or "") == machine_model

        same_recipe = (
            str(recipe.get("recipe_name") or "").strip().lower()
            == clean_name.lower()
        )
        if same_machine and same_recipe:
            existing_images = recipe.get("hmi_images", []) or []
            combined_images = list(
                dict.fromkeys(existing_images + (hmi_images or []))
            )
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

    recipes.append(
        {
            "machine_id": machine_id,
            "machine_model": machine_model,
            "recipe_name": clean_name,
            "status": status,
            "parameters": parameters,
            "notes": notes.strip(),
            "hmi_images": hmi_images or [],
        }
    )
    save_all_recipes(recipes)
    return "created"

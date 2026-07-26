import json
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
RECIPES_FILE = BASE_DIR / "knowledge" / "recipes.json"


def load_recipes() -> list[dict[str, Any]]:
    """Load all recipe records safely."""

    try:
        with RECIPES_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if isinstance(data, list):
            return data

        return []

    except FileNotFoundError:
        RECIPES_FILE.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        save_all_recipes([])
        return []

    except json.JSONDecodeError:
        return []


def save_all_recipes(
    recipes: list[dict[str, Any]],
) -> None:
    """Save the complete recipe database."""

    RECIPES_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with RECIPES_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            recipes,
            file,
            indent=4,
            ensure_ascii=False,
        )


def recipe_sort_key(
    recipe_name: str,
) -> tuple[int, str]:
    """Sort recipe names by their numerical weight."""

    number_text = "".join(
        character
        for character in recipe_name
        if character.isdigit()
    )

    if number_text:
        return int(number_text), recipe_name

    return 999999, recipe_name


def list_recipe_names(
    machine_model: str,
) -> list[str]:
    """Return recipe names belonging to one machine."""

    recipes = load_recipes()

    names = [
        recipe.get("recipe_name", "")
        for recipe in recipes
        if recipe.get("machine_model") == machine_model
        and recipe.get("recipe_name")
    ]

    return sorted(
        set(names),
        key=recipe_sort_key,
    )


def get_recipe(
    machine_model: str,
    recipe_name: str,
) -> dict[str, Any] | None:
    """Find one recipe by machine and recipe name."""

    recipes = load_recipes()

    requested_name = recipe_name.strip().lower()

    for recipe in recipes:
        saved_machine = recipe.get(
            "machine_model",
            "",
        )

        saved_name = recipe.get(
            "recipe_name",
            "",
        ).strip().lower()

        if (
            saved_machine == machine_model
            and saved_name == requested_name
        ):
            return recipe

    return None


def save_recipe(
    machine_model: str,
    recipe_name: str,
    status: str,
    parameters: dict[str, Any],
    notes: str,
    hmi_images: list[str] | None = None,
) -> str:
    """
    Create or update a recipe.

    Parameters may contain:
    - ordinary single values
    - Delay and Action timing pairs
    """

    recipes = load_recipes()

    clean_name = recipe_name.strip()

    for index, recipe in enumerate(recipes):
        same_machine = (
            recipe.get("machine_model")
            == machine_model
        )

        same_recipe = (
            recipe.get(
                "recipe_name",
                "",
            ).strip().lower()
            == clean_name.lower()
        )

        if same_machine and same_recipe:
            existing_images = recipe.get(
                "hmi_images",
                [],
            )

            combined_images = list(
                dict.fromkeys(
                    existing_images
                    + (hmi_images or [])
                )
            )

            recipes[index] = {
                "machine_model": machine_model,
                "recipe_name": clean_name,
                "status": status,
                "parameters": parameters,
                "notes": notes.strip(),
                "hmi_images": combined_images,
            }

            save_all_recipes(recipes)
            return "updated"

    new_record = {
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
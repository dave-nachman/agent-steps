from typing import Optional

from pydantic import BaseModel

from agent_steps import step


class Recipe(BaseModel):
    description: str
    ingredients: list[str]
    instructions: list[str]
    tips: list[str]


@step(model="gpt-4o-mini")
def draft_recipe(query: str) -> Recipe:
    """You are an inventive chef"""
    return query


@step(model="gpt-4o-mini")
def improve_recipe(recipe: Recipe) -> Recipe:
    """You are a chef who is exacting for detail. Please return an improved version of the recipe"""
    return recipe


class ValidationResult(BaseModel):
    is_valid: bool
    reason: Optional[str] = None


@step(model="gpt-4o-mini")
def validate_recipe(recipe: Recipe) -> ValidationResult:
    """Please consider if this recipe is valid"""
    return recipe


@step(max_loops=3)
def create_recipe(query: str):
    recipe = draft_recipe(query)
    improved_recipe = improve_recipe(recipe)

    if not validate_recipe(improved_recipe).is_valid:
        return create_recipe(query)

    return improved_recipe

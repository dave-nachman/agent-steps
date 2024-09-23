from agent_steps import runtime

from .example import create_recipe


def test_steps():
    with runtime():
        result = create_recipe("pasta")
        assert result is not None

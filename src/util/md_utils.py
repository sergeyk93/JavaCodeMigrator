from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader


def generate_markdown_from_json(json_dict: dict[str, Any], template_path: Path, output_path: Path) -> None:
    env = Environment(
        loader=FileSystemLoader(template_path.parent),
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
    )

    template = env.get_template(template_path.name)
    # This only works assuming the template is aware of the JSON format
    markdown = template.render(**json_dict)
    output_path.write_text(markdown, encoding="utf-8")

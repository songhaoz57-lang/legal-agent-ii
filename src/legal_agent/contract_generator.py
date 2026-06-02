import json
from pathlib import Path

TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "contract_templates"


def list_templates():
    if not TEMPLATES_DIR.exists():
        return []
    templates = []
    for fp in sorted(TEMPLATES_DIR.glob("*.json")):
        try:
            data = json.loads(fp.read_text(encoding="utf-8-sig"))
            templates.append({
                "id": fp.stem,
                "name": data.get("name", fp.stem),
                "description": data.get("description", ""),
                "fields": data.get("fields", []),
            })
        except (json.JSONDecodeError, KeyError):
            continue
    return templates


def generate_contract(template_id: str, field_data: dict) -> dict:
    fp = TEMPLATES_DIR / f"{template_id}.json"
    if not fp.exists():
        return {"error": "Template not found"}

    data = json.loads(fp.read_text(encoding="utf-8-sig"))
    template = data.get("template", "")
    name = data.get("name", template_id)

    from datetime import date
    placeholders = {
        "date": date.today().strftime("%Y年%m月%d日"),
        "place": field_data.get("place", "________"),
    }
    placeholders.update(field_data)

    result = template
    for key, value in placeholders.items():
        result = result.replace("{" + key + "}", str(value))

    return {
        "template_id": template_id,
        "name": name,
        "content": result,
        "filled_fields": list(placeholders.keys()),
    }

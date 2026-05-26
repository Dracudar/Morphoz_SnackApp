from __future__ import annotations

import importlib.util
import unicodedata
from pathlib import Path
from typing import Any, Callable, Dict, Optional


PROJECT_ROOT = Path(__file__).resolve().parents[3]
MODULES_ROOT = PROJECT_ROOT / "src" / "modules"


def _normalize_text(value: str) -> str:
    ascii_text = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return "".join(character for character in ascii_text.lower() if character.isalnum())


def _load_module(module_path: Path):
    spec = importlib.util.spec_from_file_location(module_path.stem, module_path)
    if spec is None or spec.loader is None:
        return None

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _pick_icon(folder: Path) -> Optional[str]:
    for icon_name in ("icon.svg", "icon.png", "icon_HS.svg", "icon_HS.png"):
        icon_path = folder / icon_name
        if icon_path.exists():
            return str(icon_path)
    return None


def discover_module_registry() -> Dict[str, Dict[str, Any]]:
    registry: Dict[str, Dict[str, Any]] = {}

    if not MODULES_ROOT.exists():
        return registry

    for folder in MODULES_ROOT.iterdir():
        if not folder.is_dir():
            continue

        descriptor: Dict[str, Any] = {
            "slug": folder.name,
            "label": folder.name.replace("_", " ").strip().title(),
            "icon_path": _pick_icon(folder),
            "action": None,
            "tooltip": None,
            "enabled": True,
        }

        module_file = folder / "module.py"
        if module_file.exists():
            loaded_module = _load_module(module_file)
            if loaded_module is not None:
                if hasattr(loaded_module, "get_module_descriptor"):
                    module_descriptor = loaded_module.get_module_descriptor()
                    if isinstance(module_descriptor, dict):
                        descriptor.update(module_descriptor)
                else:
                    for key in ("label", "icon_path", "action", "tooltip", "enabled"):
                        if hasattr(loaded_module, key.upper()):
                            descriptor[key] = getattr(loaded_module, key.upper())

                if not descriptor.get("label"):
                    descriptor["label"] = folder.name.replace("_", " ").strip().title()
                if not descriptor.get("icon_path"):
                    descriptor["icon_path"] = _pick_icon(folder)

        registry[_normalize_text(descriptor["label"])] = descriptor
        registry[_normalize_text(folder.name)] = descriptor

    return registry

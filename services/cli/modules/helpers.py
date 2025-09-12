from __future__ import annotations

from typing import Any, Dict, List, Optional
from rich.table import Table


def print_kv(console, title: str, data: Dict[str, Any]) -> None:
    table = Table(title=title)
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="white")
    for k, v in (data or {}).items():
        table.add_row(str(k), str(v))
    console.print(table)


def print_list(console, title: str, items: List[Dict[str, Any]]) -> None:
    if not items:
        console.print("[yellow]No items found.[/yellow]")
        return
    table = Table(title=title)
    cols: List[str] = []
    for it in items:
        for k in it.keys():
            if k not in cols:
                cols.append(k)
    for c in cols:
        table.add_column(str(c))
    for it in items:
        row = [str(it.get(c, "")) for c in cols]
        table.add_row(*row)
    console.print(table)


async def save_data(console, data: Dict[str, Any], fmt: str, path: str, content_key: Optional[str] = None) -> None:
    import json, os
    fmt = (fmt or "json").lower()
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        if fmt == "json":
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        elif fmt in ("txt", "md"):
            text = ""
            if content_key and isinstance(data, dict) and content_key in data:
                text = str(data.get(content_key) or "")
            else:
                text = json.dumps(data, indent=2, ensure_ascii=False)
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
        else:
            with open(path, "w", encoding="utf-8") as f:
                f.write(str(data))
        print_kv(console, "Saved", {"saved": True, "path": path, "format": fmt})
    except Exception as e:
        print_kv(console, "Saved", {"saved": False, "path": path, "error": str(e)})



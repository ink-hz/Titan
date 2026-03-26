"""
Titan CLI -- Command-line interface for Titan framework.

Usage:
    titan init <template>        -- Initialize a new project from template
    titan serve [--port N]       -- Start the super-agent server
    titan tools                  -- List registered tools
    titan templates              -- List available templates

Or via module:
    python -m titan.serve --template security --port 8086
"""

import argparse
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        prog="titan",
        description="Titan -- Build Super-Intelligent Agent Products. From Agent Framework to Agent Product.",
    )
    subparsers = parser.add_subparsers(dest="command")

    # ---- titan init --------------------------------------------------------
    init_parser = subparsers.add_parser("init", help="Initialize new project from template")
    init_parser.add_argument("template", help="Template name (security, devops, data-analysis, customer-service)")
    init_parser.add_argument("--dir", default=".", help="Target directory (default: current)")

    # ---- titan serve -------------------------------------------------------
    serve_parser = subparsers.add_parser("serve", help="Start super-agent server")
    serve_parser.add_argument("--port", type=int, default=8086, help="Port to listen on (default: 8086)")
    serve_parser.add_argument("--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)")
    serve_parser.add_argument("--template", default=None, help="Template name to load")
    serve_parser.add_argument("--model", default="deepseek-r1", help="Model to use (default: deepseek-r1)")
    serve_parser.add_argument("--ui", default="panorama+chat+workspace", help="UI modes (default: panorama+chat+workspace)")
    serve_parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    # ---- titan tools -------------------------------------------------------
    subparsers.add_parser("tools", help="List registered tools")

    # ---- titan templates ---------------------------------------------------
    subparsers.add_parser("templates", help="List available templates")

    args = parser.parse_args()

    if args.command == "init":
        cmd_init(args)
    elif args.command == "serve":
        cmd_serve(args)
    elif args.command == "tools":
        cmd_tools(args)
    elif args.command == "templates":
        cmd_templates(args)
    else:
        parser.print_help()
        sys.exit(0)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_init(args):
    """Copy template to target directory and print next steps."""
    import shutil

    template_dir = Path(__file__).parent / "templates" / args.template
    if not template_dir.exists():
        print(f"Error: Template '{args.template}' not found.")
        _print_available_templates()
        sys.exit(1)

    target = Path(args.dir) / f"titan-{args.template}"
    shutil.copytree(template_dir, target, dirs_exist_ok=True)
    print(f"Initialized Titan project from '{args.template}' template.")
    print(f"  Directory: {target.resolve()}")
    print(f"  Next steps:")
    print(f"    cd {target}")
    print(f"    titan serve --template {args.template}")


def cmd_serve(args):
    """Start the super-agent server."""
    from .serve import serve

    print(f"Starting Titan Super-Agent on {args.host}:{args.port} ...")
    print(f"  Template : {args.template or '(none, provide --template)'}")
    print(f"  Model    : {args.model}")
    print(f"  UI       : {args.ui}")
    print(f"  Open http://localhost:{args.port} in your browser")
    print()

    if not args.template:
        # If no template, create a minimal brain with the specified model
        from .core.brain.engine import AgentBrain
        brain = AgentBrain(model=args.model, system_prompt="You are a Titan super-agent. Help the user with their tasks.")
        serve(brain=brain, port=args.port, host=args.host, ui=args.ui, debug=args.debug)
    else:
        serve(port=args.port, host=args.host, template=args.template, ui=args.ui, debug=args.debug)


def cmd_tools(args):
    """List all registered tools."""
    from .capability.mcp.decorator import get_registered_tools

    tools = get_registered_tools()
    if not tools:
        print("No tools registered.")
        print("Use @tool decorator or load a template with 'titan serve --template <name>'.")
        return

    # Group by category
    by_category = {}
    for name, t in tools.items():
        by_category.setdefault(t.category, []).append(t)

    category_labels = {
        "perception": "Perception",
        "decision": "Decision",
        "execution": "Execution",
        "presentation": "Presentation",
        "memory": "Memory",
    }

    total = 0
    for cat in ["perception", "decision", "execution", "presentation", "memory"]:
        if cat not in by_category:
            continue
        print(f"\n  [{category_labels.get(cat, cat)}]")
        for t in by_category[cat]:
            trust = t.trust_level.name.lower().replace("_", "-")
            print(f"    {t.name:30s}  {t.description}  ({trust})")
            total += 1

    print(f"\n  Total: {total} tools")


def cmd_templates(args):
    """List available templates."""
    _print_available_templates()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _print_available_templates():
    """Print all available templates with description."""
    templates_dir = Path(__file__).parent / "templates"
    if not templates_dir.exists():
        print("No templates directory found.")
        return

    dirs = sorted(
        d.name for d in templates_dir.iterdir()
        if d.is_dir() and not d.name.startswith("_")
    )

    if not dirs:
        print("No templates available.")
        return

    print("Available templates:")
    for name in dirs:
        config_file = templates_dir / name / "titan.yaml"
        desc = ""
        if config_file.exists():
            import yaml
            with open(config_file, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
            desc = config.get("description", "")
        print(f"  {name:20s}  {desc}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    main()

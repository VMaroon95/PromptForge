"""
PromptForge CLI — optimize, analyze, bench commands.
Uses Rich for terminal UI when available, falls back to plain text.
"""

import sys
import argparse
import textwrap

from .optimizer import optimize
from .scorer import score_prompt, score_delta
from .tokenizer import count_tokens, format_token_stats, token_delta
from .models import list_models, get_model

# Rich is optional — graceful fallback
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich import box
    RICH = True
    console = Console()
except ImportError:
    RICH = False
    console = None


# ─── helpers ────────────────────────────────────────────────────────────────

def _print(msg: str):
    if RICH:
        console.print(msg)
    else:
        print(msg)

def _rule(title: str = ""):
    if RICH:
        console.rule(title)
    else:
        print(f"\n{'─' * 60}")
        if title:
            print(f" {title}")
        print('─' * 60)

def _read_prompt(args) -> str:
    """Read prompt from arg, stdin pipe, or interactive input."""
    if args.prompt:
        return " ".join(args.prompt)
    if not sys.stdin.isatty():
        return sys.stdin.read().strip()
    _print("[yellow]Enter your prompt (Ctrl+D when done):[/yellow]" if RICH
           else "Enter your prompt (Ctrl+D when done):")
    try:
        return sys.stdin.read().strip()
    except EOFError:
        return ""


# ─── commands ───────────────────────────────────────────────────────────────

def cmd_optimize(args):
    prompt = _read_prompt(args)
    if not prompt:
        _print("[red]Error: no prompt provided.[/red]" if RICH else "Error: no prompt provided.")
        sys.exit(1)

    result = optimize(prompt, model=args.model)

    if RICH:
        _rule("PromptForge — Optimize")

        # Before / After panels
        console.print(Panel(result.original, title="[red]BEFORE[/red]", border_style="red"))
        console.print(Panel(result.optimized, title="[green]AFTER[/green]", border_style="green"))

        # Stats table
        table = Table(box=box.SIMPLE, show_header=True, header_style="bold cyan")
        table.add_column("Metric", style="cyan")
        table.add_column("Before", justify="right")
        table.add_column("After", justify="right")
        table.add_column("Change", justify="right")

        b, a = result.score_before, result.score_after
        tok = result.token_stats

        table.add_row("Quality score", str(b.total), str(a.total),
                      f"[green]+{a.total-b.total}[/green]" if a.total >= b.total else f"[red]{a.total-b.total}[/red]")
        table.add_row("  · Clarity",     str(b.clarity),     str(a.clarity),     _delta_str(a.clarity - b.clarity))
        table.add_row("  · Specificity", str(b.specificity), str(a.specificity), _delta_str(a.specificity - b.specificity))
        table.add_row("  · Structure",   str(b.structure),   str(a.structure),   _delta_str(a.structure - b.structure))
        table.add_row("  · Grounding",   str(b.grounding),   str(a.grounding),   _delta_str(a.grounding - b.grounding))
        table.add_row("Tokens", str(tok["original"]), str(tok["optimized"]),
                      _token_change_str(tok))

        console.print(table)

        # Passes applied
        if result.passes_applied:
            console.print(f"\n[dim]Passes applied: {', '.join(result.passes_applied)}[/dim]")
    else:
        # Plain text fallback
        print("\n=== BEFORE ===")
        print(result.original)
        print("\n=== AFTER ===")
        print(result.optimized)
        print("\n=== STATS ===")
        b, a = result.score_before, result.score_after
        print(f"Quality: {b.total} → {a.total} ({'+' if a.total>=b.total else ''}{a.total-b.total})")
        print(format_token_stats(result.token_stats))
        print(f"Passes: {', '.join(result.passes_applied)}")


def cmd_analyze(args):
    prompt = _read_prompt(args)
    if not prompt:
        _print("[red]Error: no prompt provided.[/red]" if RICH else "Error: no prompt provided.")
        sys.exit(1)

    score = score_prompt(prompt)
    tokens = count_tokens(prompt, args.model or "gpt-4")

    if RICH:
        _rule("PromptForge — Analyze")
        console.print(Panel(prompt, title="[cyan]Prompt[/cyan]", border_style="dim"))

        table = Table(box=box.SIMPLE, show_header=True, header_style="bold cyan")
        table.add_column("Dimension",  style="cyan", width=16)
        table.add_column("Score",      justify="right", width=8)
        table.add_column("Max",        justify="right", width=6)
        table.add_column("Assessment", width=40)

        def bar(val, max_val=25) -> str:
            filled = int(val / max_val * 10)
            return "█" * filled + "░" * (10 - filled)

        assessments = {
            "clarity":     ("⚠ Needs a clearer action verb", "✓ Clear task statement"),
            "specificity": ("⚠ Add format/length constraints", "✓ Well-constrained"),
            "structure":   ("⚠ Consider adding context/role", "✓ Well-structured"),
            "grounding":   ("⚠ Add anti-hallucination guardrails", "✓ Grounded"),
        }

        for dim, (warn, good) in assessments.items():
            val = getattr(score, dim)
            assessment = good if val >= 18 else warn
            color = "green" if val >= 18 else "yellow" if val >= 10 else "red"
            table.add_row(
                dim.capitalize(),
                f"[{color}]{val}[/{color}]",
                "25",
                f"{bar(val)} {assessment}"
            )

        console.print(table)
        color = "green" if score.total >= 75 else "yellow" if score.total >= 50 else "red"
        console.print(f"\n[bold]Total: [{color}]{score.total}/100[/{color}][/bold]  |  Tokens: {tokens}")

        if score.total < 50:
            console.print("\n[yellow]💡 Run `promptforge optimize` to improve this prompt.[/yellow]")
    else:
        print(f"\nQuality Score: {score.total}/100")
        print(f"  Clarity:     {score.clarity}/25")
        print(f"  Specificity: {score.specificity}/25")
        print(f"  Structure:   {score.structure}/25")
        print(f"  Grounding:   {score.grounding}/25")
        print(f"Tokens: {tokens}")


def cmd_bench(args):
    prompt = _read_prompt(args)
    if not prompt:
        _print("[red]Error: no prompt provided.[/red]" if RICH else "Error: no prompt provided.")
        sys.exit(1)

    models_to_test = args.models.split(",") if args.models else [
        "claude-3-5-sonnet", "gpt-4o", "llama-3-70b", "gemini-1.5-pro"
    ]

    if RICH:
        _rule("PromptForge — Bench")
        console.print(f"[dim]Benchmarking prompt across {len(models_to_test)} models...[/dim]\n")

        table = Table(box=box.SIMPLE, show_header=True, header_style="bold cyan")
        table.add_column("Model",       style="cyan", width=22)
        table.add_column("Quality",     justify="right", width=10)
        table.add_column("Tokens",      justify="right", width=10)
        table.add_column("Token Δ",     justify="right", width=10)
        table.add_column("Key change",  width=30)

        for m in models_to_test:
            result = optimize(prompt, model=m)
            tok = result.token_stats
            q_delta = result.quality_delta
            key_pass = result.passes_applied[0] if result.passes_applied else "none"

            q_color = "green" if q_delta > 0 else "yellow" if q_delta == 0 else "red"
            t_str = _token_change_str(tok)

            table.add_row(
                m,
                f"[{q_color}]{result.score_before.total}→{result.score_after.total}[/{q_color}]",
                str(tok["original"]),
                t_str,
                key_pass,
            )

        console.print(table)
    else:
        print(f"\nBenchmarking across {len(models_to_test)} models:")
        for m in models_to_test:
            result = optimize(prompt, model=m)
            tok = result.token_stats
            print(f"\n{m}:")
            print(f"  Quality: {result.score_before.total} → {result.score_after.total}")
            print(f"  {format_token_stats(tok)}")
            print(f"  Passes: {', '.join(result.passes_applied) or 'none'}")


def cmd_models(_args):
    _print("\n[bold cyan]Available models:[/bold cyan]" if RICH else "\nAvailable models:")
    for name in list_models():
        cfg = get_model(name)
        info = f"  {name:<25} context={cfg.context_window:>10,}  family={cfg.family}"
        _print(info)


# ─── helpers ────────────────────────────────────────────────────────────────

def _delta_str(d: int) -> str:
    if not RICH:
        return f"+{d}" if d > 0 else str(d)
    if d > 0:
        return f"[green]+{d}[/green]"
    elif d < 0:
        return f"[red]{d}[/red]"
    return "[dim]—[/dim]"

def _token_change_str(tok: dict) -> str:
    d = tok["delta"]
    pct = abs(tok["pct_change"])
    if not RICH:
        return f"+{d} (+{pct}%)" if d > 0 else f"{d} ({pct}% saved)" if d < 0 else "—"
    if d > 0:
        return f"[yellow]+{d} (+{pct}%)[/yellow]"
    elif d < 0:
        return f"[green]{d} ({pct}% saved)[/green]"
    return "[dim]—[/dim]"


# ─── main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        prog="promptforge",
        description="Local-first, model-aware prompt optimizer.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
        Examples:
          promptforge optimize "tell me about python"
          promptforge optimize "tell me about python" --model claude-3-5-sonnet
          echo "my prompt" | promptforge analyze
          promptforge bench "explain neural networks" --models gpt-4o,claude-3-5-sonnet
          promptforge models
        """)
    )
    sub = parser.add_subparsers(dest="command")

    # optimize
    p_opt = sub.add_parser("optimize", help="Optimize a prompt and show before/after diff")
    p_opt.add_argument("prompt", nargs="*", help="Prompt text (or pipe via stdin)")
    p_opt.add_argument("--model", "-m", help="Target model (e.g. claude-3-5-sonnet, gpt-4o)")
    p_opt.set_defaults(func=cmd_optimize)

    # analyze
    p_ana = sub.add_parser("analyze", help="Analyze prompt quality (no optimization)")
    p_ana.add_argument("prompt", nargs="*", help="Prompt text (or pipe via stdin)")
    p_ana.add_argument("--model", "-m", default="gpt-4", help="Model for token counting")
    p_ana.set_defaults(func=cmd_analyze)

    # bench
    p_bench = sub.add_parser("bench", help="Benchmark prompt optimization across multiple models")
    p_bench.add_argument("prompt", nargs="*", help="Prompt text (or pipe via stdin)")
    p_bench.add_argument("--models", help="Comma-separated model list (default: top 4)")
    p_bench.set_defaults(func=cmd_bench)

    # models
    p_models = sub.add_parser("models", help="List supported models")
    p_models.set_defaults(func=cmd_models)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()

from __future__ import annotations

import sys
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich import print as rprint

from roteamento.config import (
    ComplexityLevel,
    DireciondorConfig,
    LLMEntry,
    add_llm,
    load_config,
    remove_llm,
    resolve_api_key,
    save_config,
    set_direcionador,
)
from roteamento.direcionador import evaluate_complexity, pick_llm
from roteamento.adapters import call_llm

app = typer.Typer(
    name="rllm",
    help="[bold cyan]rllm[/] — Roteamento inteligente de modelos LLM",
    rich_markup_mode="rich",
    no_args_is_help=True,
)

console = Console()

COMPLEXITY_COLORS = {
    ComplexityLevel.LOW: "green",
    ComplexityLevel.MEDIUM: "yellow",
    ComplexityLevel.HIGH: "red",
}

COMPLEXITY_LABELS = {
    ComplexityLevel.LOW: "Baixa",
    ComplexityLevel.MEDIUM: "Média",
    ComplexityLevel.HIGH: "Alta",
}

KNOWN_PROVIDERS = {
    "openai": "OpenAI",
    "anthropic": "Anthropic",
    "google": "Google (Gemini)",
    "groq": "Groq",
    "ollama": "Ollama (local)",
    "openrouter": "OpenRouter",
    "mistral": "Mistral",
    "cohere": "Cohere",
    "together": "Together AI",
    "perplexity": "Perplexity",
    "deepseek": "DeepSeek",
    "xai": "xAI (Grok)",
}


# ---------------------------------------------------------------------------
# chat
# ---------------------------------------------------------------------------


@app.command()
def chat(
    prompt: Annotated[str, typer.Argument(help="Prompt a ser enviado")],
    alias: Annotated[Optional[str], typer.Option("--use", "-u", help="Forçar um LLM específico pelo alias")] = None,
    show_routing: Annotated[bool, typer.Option("--routing/--no-routing", help="Mostrar decisão de roteamento")] = True,
):
    """Envia um prompt. O direcionador escolhe o melhor modelo automaticamente."""
    config = load_config()

    if not config.arsenal:
        console.print(
            Panel(
                "[yellow]Arsenal vazio![/] Adicione modelos com [bold cyan]rllm add[/].",
                title="Aviso",
                border_style="yellow",
            )
        )
        raise typer.Exit(1)

    if alias:
        llm = config.get_llm_by_alias(alias)
        if not llm:
            console.print(f"[red]Alias '{alias}' não encontrado no arsenal.[/]")
            raise typer.Exit(1)
        if show_routing:
            console.print(f"[dim]Forçando uso de [bold]{alias}[/] ({llm.provider}/{llm.model})[/]")
    else:
        with console.status("[dim]Direcionador avaliando complexidade...[/]", spinner="dots"):
            try:
                level, reason = evaluate_complexity(prompt, config.direcionador)
            except Exception as e:
                console.print(f"[red]Erro no direcionador:[/] {e}")
                raise typer.Exit(1)

        llm = pick_llm(config, level)

        if show_routing:
            color = COMPLEXITY_COLORS[level]
            label = COMPLEXITY_LABELS[level]
            console.print(
                f"[dim]Complexidade: [{color}]{label}[/] · {reason}[/]"
            )
            console.print(
                f"[dim]Roteando para: [bold]{llm.alias}[/] ({llm.provider}/{llm.model})[/]"
            )

    console.print()

    messages = [{"role": "user", "content": prompt}]

    try:
        buffer = ""
        with Live(console=console, refresh_per_second=15) as live:
            for chunk in call_llm(llm, messages, stream=True):
                buffer += chunk
                live.update(Markdown(buffer))
        console.print()
    except EnvironmentError as e:
        console.print(f"\n[red]Erro de configuração:[/] {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"\n[red]Erro ao chamar o modelo:[/] {e}")
        raise typer.Exit(1)


# ---------------------------------------------------------------------------
# add
# ---------------------------------------------------------------------------


@app.command()
def add(
    alias: Annotated[Optional[str], typer.Argument(help="Alias para o modelo")] = None,
):
    """Adiciona um LLM ao arsenal de forma interativa."""
    console.print(Panel("[bold cyan]Adicionar LLM ao Arsenal[/]", border_style="cyan"))

    if not alias:
        alias = Prompt.ask("[bold]Alias[/] (nome curto para este modelo)")

    # Provider
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("#", style="dim", width=4)
    table.add_column("Provider")
    table.add_column("Nome")
    providers = list(KNOWN_PROVIDERS.items())
    for i, (key, name) in enumerate(providers, 1):
        table.add_row(str(i), key, name)
    console.print(table)

    provider_input = Prompt.ask("[bold]Provider[/] (nome ou número da tabela acima)")
    if provider_input.isdigit():
        idx = int(provider_input) - 1
        if 0 <= idx < len(providers):
            provider = providers[idx][0]
        else:
            console.print("[red]Número inválido.[/]")
            raise typer.Exit(1)
    else:
        provider = provider_input.strip().lower()

    model = Prompt.ask("[bold]Modelo[/] (ex: gpt-4o, claude-sonnet-4-6, llama-3.1-8b-instant)")

    api_key = Prompt.ask(
        "[bold]API Key[/] (valor direto ou [dim]env:NOME_DA_VAR[/dim])",
        password=True,
    )

    # Complexity levels
    console.print("\nNíveis de complexidade que este modelo deve atender:")
    console.print("  [green]low[/]    — perguntas simples, traduções, formatação")
    console.print("  [yellow]medium[/] — análise, debugging, código moderado")
    console.print("  [red]high[/]   — raciocínio complexo, arquitetura, pesquisa")
    levels_input = Prompt.ask(
        "[bold]Níveis[/] (separados por vírgula)",
        default="medium",
    )
    raw_levels = [l.strip().lower() for l in levels_input.split(",")]
    try:
        complexity_levels = [ComplexityLevel(l) for l in raw_levels]
    except ValueError as e:
        console.print(f"[red]Nível inválido:[/] {e}")
        raise typer.Exit(1)

    description = Prompt.ask("[bold]Descrição[/] (opcional)", default="")

    entry = LLMEntry(
        alias=alias,
        provider=provider,
        model=model,
        api_key=api_key,
        complexity_levels=complexity_levels,
        description=description or None,
    )

    # Validate API key resolution before saving
    try:
        resolve_api_key(api_key)
    except EnvironmentError as e:
        console.print(f"[yellow]Aviso:[/] {e} — o modelo será salvo, mas certifique-se de definir a variável.")

    add_llm(entry)
    console.print(f"\n[green]✓[/] LLM [bold]{alias}[/] adicionado ao arsenal com sucesso.")


# ---------------------------------------------------------------------------
# remove
# ---------------------------------------------------------------------------


@app.command()
def remove(
    alias: Annotated[str, typer.Argument(help="Alias do LLM a remover")],
    force: Annotated[bool, typer.Option("--force", "-f", help="Pular confirmação")] = False,
):
    """Remove um LLM do arsenal."""
    if not force:
        ok = Confirm.ask(f"Remover [bold]{alias}[/] do arsenal?")
        if not ok:
            raise typer.Exit()

    removed = remove_llm(alias)
    if removed:
        console.print(f"[green]✓[/] [bold]{alias}[/] removido.")
    else:
        console.print(f"[red]Alias '{alias}' não encontrado.[/]")
        raise typer.Exit(1)


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------


@app.command(name="list")
def list_llms():
    """Lista os LLMs configurados no arsenal."""
    config = load_config()

    # Direcionador info
    d = config.direcionador
    console.print(
        Panel(
            f"[bold]{d.provider}[/] / {d.model}  |  chave: [dim]{d.api_key}[/]",
            title="[cyan]Direcionador[/]",
            border_style="cyan",
        )
    )

    if not config.arsenal:
        console.print("[yellow]Arsenal vazio.[/] Use [bold cyan]rllm add[/] para adicionar modelos.")
        return

    table = Table(show_header=True, header_style="bold magenta", expand=True)
    table.add_column("Alias", style="bold")
    table.add_column("Provider")
    table.add_column("Modelo")
    table.add_column("Níveis")
    table.add_column("Descrição", style="dim")

    for llm in config.arsenal:
        levels_str = ", ".join(
            f"[{COMPLEXITY_COLORS[l]}]{l.value}[/]" for l in llm.complexity_levels
        )
        table.add_row(
            llm.alias,
            llm.provider,
            llm.model,
            levels_str,
            llm.description or "",
        )

    console.print(table)


# ---------------------------------------------------------------------------
# direcionador
# ---------------------------------------------------------------------------


direcionador_app = typer.Typer(
    name="direcionador",
    help="Gerencia o modelo orquestrador (direcionador).",
    rich_markup_mode="rich",
    no_args_is_help=True,
)
app.add_typer(direcionador_app)


@direcionador_app.command("set")
def direcionador_set(
    provider: Annotated[Optional[str], typer.Option("--provider", "-p")] = None,
    model: Annotated[Optional[str], typer.Option("--model", "-m")] = None,
    api_key: Annotated[Optional[str], typer.Option("--api-key", "-k")] = None,
):
    """Configura o modelo direcionador."""
    config = load_config()
    current = config.direcionador

    console.print(Panel("[bold cyan]Configurar Direcionador[/]", border_style="cyan"))
    console.print(
        "[dim]Recomendação: use um modelo gratuito ou de baixo custo como "
        "Groq (llama-3.1-8b-instant), Gemini Flash, ou Ollama local.[/]\n"
    )

    new_provider = provider or Prompt.ask("[bold]Provider[/]", default=current.provider)
    new_model = model or Prompt.ask("[bold]Modelo[/]", default=current.model)
    new_key = api_key or Prompt.ask(
        "[bold]API Key[/] (valor ou [dim]env:VAR[/dim])",
        default=current.api_key,
        password=True,
    )

    new_config = DireciondorConfig(provider=new_provider, model=new_model, api_key=new_key)
    set_direcionador(new_config)
    console.print(f"\n[green]✓[/] Direcionador configurado: [bold]{new_provider}[/] / {new_model}")


@direcionador_app.command("show")
def direcionador_show():
    """Mostra a configuração atual do direcionador."""
    config = load_config()
    d = config.direcionador
    console.print(
        Panel(
            f"Provider: [bold]{d.provider}[/]\nModelo:   [bold]{d.model}[/]\nAPI Key:  [dim]{d.api_key}[/]",
            title="[cyan]Direcionador Atual[/]",
            border_style="cyan",
        )
    )


@direcionador_app.command("test")
def direcionador_test(
    prompt: Annotated[str, typer.Argument(help="Prompt para testar a avaliação")] = "Qual é a capital do Brasil?",
):
    """Testa a avaliação de complexidade do direcionador sem enviar para o LLM."""
    config = load_config()
    with console.status("[dim]Avaliando...[/]", spinner="dots"):
        try:
            level, reason = evaluate_complexity(prompt, config.direcionador)
        except Exception as e:
            console.print(f"[red]Erro:[/] {e}")
            raise typer.Exit(1)

    color = COMPLEXITY_COLORS[level]
    label = COMPLEXITY_LABELS[level]
    console.print(f"Prompt:      [italic]{prompt}[/]")
    console.print(f"Complexidade: [{color}][bold]{label}[/][/]")
    console.print(f"Motivo:      {reason}")

    candidates = config.get_llms_for_complexity(level)
    if candidates:
        selected = pick_llm(config, level)
        console.print(f"Rotearia para: [bold]{selected.alias}[/] ({selected.provider}/{selected.model})")
    else:
        console.print("[yellow]Nenhum LLM configurado para este nível no arsenal.[/]")


# ---------------------------------------------------------------------------
# config
# ---------------------------------------------------------------------------


config_app = typer.Typer(
    name="config",
    help="Exibe e exporta a configuração.",
    rich_markup_mode="rich",
    no_args_is_help=True,
)
app.add_typer(config_app)


@config_app.command("show")
def config_show():
    """Mostra a configuração completa em YAML."""
    import yaml
    from roteamento.config.manager import CONFIG_FILE

    config = load_config()
    console.print(f"[dim]Arquivo: {CONFIG_FILE}[/]\n")
    console.print(yaml.dump(config.model_dump(mode="json"), default_flow_style=False, allow_unicode=True))


@config_app.command("path")
def config_path():
    """Mostra o caminho do arquivo de configuração."""
    from roteamento.config.manager import CONFIG_FILE
    console.print(str(CONFIG_FILE))


# ---------------------------------------------------------------------------
# version
# ---------------------------------------------------------------------------


@app.command()
def version():
    """Mostra a versão do rllm."""
    from importlib.metadata import version as pkg_version
    try:
        v = pkg_version("roteamento-llm")
    except Exception:
        v = "dev"
    console.print(f"rllm [bold cyan]{v}[/]")


if __name__ == "__main__":
    app()

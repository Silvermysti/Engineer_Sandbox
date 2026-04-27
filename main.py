"""main.py — Core entry point and Typer CLI loop for Engineer Sandbox."""
import typer
import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from storage.database import setup_db, get_scenario_count
from agents.scenario_generator import ScenarioGenerator
from agents.agent_factory import create_cast

app = typer.Typer(help="Engineer Sandbox CLI - Multi-Agent Simulation")
console = Console()

async def run_scenario():
    console.print("[bold cyan]Initializing Engineer Sandbox...[/bold cyan]")
    setup_db()
    
    scenario_num = get_scenario_count() + 1
    generator = ScenarioGenerator()
    
    with console.status(f"[yellow]Generating Scenario #{scenario_num} (Querying Ollama...)[/yellow]"):
        spec = await generator.generate(scenario_number=scenario_num)
        
    cast_agents = create_cast(spec)
    
    # Display Scenario Intro
    console.print()
    console.print(Panel(
        f"[bold]{spec.opening_hook}[/bold]\n\n{spec.description}", 
        title=f"Scenario: {spec.title} ({spec.scenario_type})", 
        border_style="green"
    ))
    
    # Show Cast
    cast_text = "\n".join([f"• [bold]{a.name}[/bold] ({a.role})" for a in spec.cast])
    console.print(Panel(cast_text, title="The Cast", border_style="blue"))
    
    console.print("\n[bold]Suggested Actions:[/bold]")
    for i, opt in enumerate(spec.decision_options, 1):
        console.print(f"  [cyan]{i}.[/cyan] {opt}")
        
    # Phase 2 Core Loop
    turn = 1
    max_turns = 4
    
    while turn <= max_turns:
        console.print(f"\n[bold magenta]--- Turn {turn} of {max_turns} ---[/bold magenta]")
        decision = Prompt.ask("\n[bold]Your action[/bold] (Type a number from above, or write your own custom response)")
        
        if decision.lower() in ['quit', 'exit', 'q']:
            console.print("[red]Exiting simulation early...[/red]")
            break
            
        # If user picked a number, map it to the string
        if decision.isdigit() and 1 <= int(decision) <= len(spec.decision_options):
            decision = spec.decision_options[int(decision) - 1]
            console.print(f"[dim]You chose: {decision}[/dim]\n")
            
        with console.status("[yellow]Agents are reacting...[/yellow]"):
            # Run agents in parallel
            tasks = [agent.decide(spec.description, decision) for agent in cast_agents]
            reactions = await asyncio.gather(*tasks)
            
        # Display Agent Reactions Sequentially (as per Phase 2 constraints)
        for reaction, agent_spec in zip(reactions, spec.cast):
            if reaction and reaction.should_react:
                color = agent_spec.color if agent_spec.color else "white"
                console.print(Panel(
                    f"[italic dim]Thoughts: {reaction.reasoning}[/italic dim]\n\n[bold]\"{reaction.message}\"[/bold]",
                    title=f"{agent_spec.name} ({agent_spec.role})",
                    border_style=color
                ))
        
        turn += 1
        
    console.print("\n[bold green]Scenario Concluded![/bold green]")
    console.print("[dim](Phase 5: The Scoring Agent logic will be executed here in the future.)[/dim]\n")

@app.command()
def start():
    """Starts a new scenario run."""
    try:
        asyncio.run(run_scenario())
    except KeyboardInterrupt:
        console.print("\n[red]Simulation interrupted by user.[/red]")

@app.command()
def reset():
    """Clears the local SQLite database."""
    import os
    if os.path.exists("storage/sandbox.db"):
        os.remove("storage/sandbox.db")
        console.print("[green]Database reset successfully.[/green]")
    else:
        console.print("[yellow]Database does not exist yet.[/yellow]")

if __name__ == "__main__":
    app()

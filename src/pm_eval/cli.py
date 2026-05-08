"""pm-eval CLI entry point."""

import click


@click.group()
@click.version_option()
def main():
    """pm-eval — provider-agnostic eval harness for LLM and agent output."""
    pass


@main.command()
@click.option("--input", "-i", required=True, help="Path to the artifact to grade.")
@click.option("--rubric", "-r", required=True, help="Path to a rubric YAML file.")
@click.option("--provider", "-p", default="anthropic",
              type=click.Choice(["anthropic", "openai", "local"]),
              help="Judge provider to use.")
@click.option("--model", "-m", default=None, help="Model name override.")
def grade(input, rubric, provider, model):
    """Grade a single input against a rubric."""
    # TODO (v0.1): wire to Grader + provider factory
    click.echo(f"Grading {input} against {rubric} via {provider}/{model or '<default>'}")
    click.echo("(implementation pending — see roadmap in README)")


@main.command()
@click.option("--inputs", required=True, help="Directory of artifacts to grade.")
@click.option("--rubric", "-r", required=True, help="Rubric YAML file.")
@click.option("--provider", "-p", default="anthropic",
              type=click.Choice(["anthropic", "openai", "local"]))
def suite(inputs, rubric, provider):
    """Run a rubric across many inputs (regression suite)."""
    click.echo(f"Suite: {inputs} against {rubric} via {provider}")
    click.echo("(implementation pending — see roadmap in README)")


if __name__ == "__main__":
    main()

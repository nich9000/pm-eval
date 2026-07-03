"""pm-eval CLI."""

import json
import sys
from pathlib import Path

import click

from pm_eval import Grader, Rubric


def _get_provider(name: str, model: str | None):
    if name == "anthropic":
        from pm_eval.providers.anthropic import ClaudeProvider
        return ClaudeProvider(model=model or "claude-sonnet-4-6")
    if name == "openai":
        from pm_eval.providers.openai import OpenAIProvider
        return OpenAIProvider(model=model or "gpt-4o")
    if name == "local":
        from pm_eval.providers.local import LocalProvider
        return LocalProvider(model=model or "llama3.1:8b")
    raise click.ClickException(f"Unknown provider: {name}")


@click.group()
@click.version_option()
def main():
    """pm-eval — provider-agnostic eval harness for LLM and agent output."""
    pass


@main.command()
@click.option("--input", "-i", "input_path", required=True,
              type=click.Path(exists=True, dir_okay=False),
              help="Path to the artifact to grade.")
@click.option("--rubric", "-r", "rubric_path", required=True,
              type=click.Path(exists=True, dir_okay=False),
              help="Path to a rubric YAML file.")
@click.option("--provider", "-p", default="anthropic",
              type=click.Choice(["anthropic", "openai", "local"]),
              help="Judge provider to use.")
@click.option("--model", "-m", default=None,
              help="Model name override (default depends on provider).")
@click.option("--output", "-o", "output_path", default=None,
              type=click.Path(dir_okay=False),
              help="Output file. If omitted, prints to stdout.")
@click.option("--format", "out_format", default="markdown",
              type=click.Choice(["markdown", "json"]),
              help="Output format.")
def grade(input_path, rubric_path, provider, model, output_path, out_format):
    """Grade a single input against a rubric."""
    rubric_obj = Rubric.from_file(rubric_path)
    provider_obj = _get_provider(provider, model)
    grader = Grader(provider=provider_obj, rubric=rubric_obj)

    click.echo(
        f"Grading {input_path} against {rubric_obj.name} "
        f"via {provider}/{provider_obj.model}…",
        err=True,
    )
    input_text = Path(input_path).read_text(encoding="utf-8")
    result = grader.grade(input_text)

    if out_format == "json":
        out_text = json.dumps(result.to_dict(), indent=2)
    else:
        out_text = result.to_markdown()

    if output_path:
        Path(output_path).write_text(out_text, encoding="utf-8")
        click.echo(f"Wrote {output_path}", err=True)
    else:
        click.echo(out_text)

    if result.parse_error:
        sys.exit(2)


@main.command()
@click.option("--inputs", "inputs_dir", required=True,
              type=click.Path(exists=True, file_okay=False),
              help="Directory of artifacts to grade.")
@click.option("--rubric", "-r", "rubric_path", required=True,
              type=click.Path(exists=True, dir_okay=False))
@click.option("--provider", "-p", default="anthropic",
              type=click.Choice(["anthropic", "openai", "local"]))
@click.option("--glob", default="*.md", help="Filename glob.")
def suite(inputs_dir, rubric_path, provider, glob):
    """Run a rubric across many inputs (regression suite)."""
    click.echo(f"Suite: {inputs_dir} against {rubric_path} via {provider}", err=True)
    click.echo("(suite runner is v0.3 work — implement in pm_eval.runner.Runner.run)", err=True)


@main.command()
@click.option("--input", "-i", "input_path", required=True,
              type=click.Path(exists=True, dir_okay=False),
              help="Path to the artifact to grade.")
@click.option("--rubric", "-r", "rubric_path", required=True,
              type=click.Path(exists=True, dir_okay=False),
              help="Path to a rubric YAML file (shared by all judges).")
@click.option("--judge", "-j", "judge_specs", multiple=True, required=True,
              help="A judge as provider[:model], e.g. -j anthropic:claude-sonnet-4-6 "
                   "-j anthropic:claude-haiku-4-5-20251001. Repeat for each judge (min 2).")
@click.option("--threshold", "-t", default=0.25, show_default=True,
              help="Per-dimension spread at or above which judges are counted as disagreeing.")
@click.option("--output", "-o", "output_path", default=None,
              type=click.Path(dir_okay=False),
              help="Output file. If omitted, prints to stdout.")
@click.option("--format", "out_format", default="markdown",
              type=click.Choice(["markdown", "json"]),
              help="Output format.")
def consensus(input_path, rubric_path, judge_specs, threshold, output_path, out_format):
    """Grade one input with a panel of judges; disagreement is the signal.

    Exit codes: 0 = judges agree, 3 = judges disagree (review the report),
    2 = every judge errored.
    """
    from pm_eval.consensus import ConsensusGrader

    rubric_obj = Rubric.from_file(rubric_path)
    judges = {}
    for spec in judge_specs:
        provider_name, _, model = spec.partition(":")
        provider_obj = _get_provider(provider_name, model or None)
        label = f"{provider_name}/{provider_obj.model}"
        if label in judges:  # same provider+model twice: keep both, disambiguate
            label = f"{label}#{sum(1 for k in judges if k.startswith(label)) + 1}"
        judges[label] = Grader(provider=provider_obj, rubric=rubric_obj)

    if len(judges) < 2:
        raise click.ClickException("Consensus needs at least 2 judges (-j, repeatable).")

    panel = ConsensusGrader(judges, disagreement_threshold=threshold)
    click.echo(f"Consensus: {input_path} against {rubric_obj.name} "
               f"with {len(judges)} judges…", err=True)
    input_text = Path(input_path).read_text(encoding="utf-8")
    result = panel.grade(input_text)

    out_text = (json.dumps(result.to_dict(), indent=2) if out_format == "json"
                else result.to_markdown())
    if output_path:
        Path(output_path).write_text(out_text, encoding="utf-8")
        click.echo(f"Wrote {output_path}", err=True)
    else:
        click.echo(out_text)

    if not result.results or len(result.errored_judges) == len(result.results):
        sys.exit(2)
    if not result.agreement:
        sys.exit(3)


if __name__ == "__main__":
    main()

"""pm-eval — provider-agnostic eval harness for LLM and agent output.

The Evaluation rung of The PM Scaffold.
https://github.com/nich9000/pm-scaffold
"""

from pm_eval.grader import Grader, GradeResult
from pm_eval.rubric import Rubric

__version__ = "0.0.1"
__all__ = ["Grader", "GradeResult", "Rubric"]

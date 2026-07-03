"""pm-eval — provider-agnostic eval harness for LLM and agent output.

The Evaluation rung of The PM Scaffold.
https://github.com/nich9000/pm-scaffold
"""

from pm_eval.consensus import ConsensusGrader, ConsensusResult, Disagreement
from pm_eval.grader import Grader, GradeResult
from pm_eval.rubric import Rubric

__version__ = "0.2.0"
__all__ = ["ConsensusGrader", "ConsensusResult", "Disagreement", "Grader", "GradeResult", "Rubric"]

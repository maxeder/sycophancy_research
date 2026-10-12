from .base import Approach, Case, TargetSession
from .multi_turn import MultiTurn
from .real_world import RealWorld
from .real_world.replay import Replay
from .simulated_user import SimulatedUser
from .single_turn import SingleTurn

APPROACHES: dict[str, type[Approach]] = {
    cls.name: cls for cls in (SingleTurn, MultiTurn, SimulatedUser, RealWorld, Replay)
}

__all__ = ["APPROACHES", "Approach", "Case", "TargetSession"]

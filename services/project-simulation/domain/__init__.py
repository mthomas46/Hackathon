"""Domain layer - Delegates to simulation.domain for audit framework compatibility."""

# Import everything from simulation.domain to make it available at service root
from simulation.domain import *

__all__ = []  # Import all from simulation.domain

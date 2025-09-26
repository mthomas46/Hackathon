"""Application layer - Delegates to simulation.application for audit framework compatibility."""

# Import everything from simulation.application to make it available at service root
from simulation.application import *

__all__ = []  # Import all from simulation.application

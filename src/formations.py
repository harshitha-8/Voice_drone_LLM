#!/usr/bin/env python3
"""
Formation Matrix Definitions
============================
Predefined formation patterns for swarm control.

Each formation is defined as a list of (North, East, Alt) offsets from home position.
"""

from typing import List, Tuple, Dict
from dataclasses import dataclass


@dataclass
class FormationPoint:
    """Single point in a formation."""
    vehicle_id: int
    north: float
    east: float
    alt: float
    
    def to_mavproxy_cmd(self) -> str:
        """Generate MAVProxy guided command."""
        return f"vehicle {self.vehicle_id}\nmode GUIDED\nguided {self.north} {self.east} {self.alt}"


class FormationLibrary:
    """Library of predefined swarm formations."""
    
    @staticmethod
    def spread_2x4(alt: float = 10) -> List[FormationPoint]:
        """
        2 columns x 4 rows spread formation.
        
        Layout (top-down view):
            [7] [8]
            [4] [5] [6]
            [1] [2] [3]
        """
        return [
            FormationPoint(1, 20, 0, alt),
            FormationPoint(2, 20, 10, alt),
            FormationPoint(3, 20, -10, alt),
            FormationPoint(4, 30, 0, alt),
            FormationPoint(5, 30, 10, alt),
            FormationPoint(6, 30, -10, alt),
            FormationPoint(7, 40, 0, alt),
            FormationPoint(8, 40, 10, alt),
        ]
    
    @staticmethod
    def line_formation(num_vehicles: int = 8, spacing: float = 10, alt: float = 10) -> List[FormationPoint]:
        """
        Single line formation.
        
        Layout: [1] [2] [3] [4] [5] [6] [7] [8]
        """
        return [
            FormationPoint(i + 1, 20, i * spacing, alt)
            for i in range(num_vehicles)
        ]
    
    @staticmethod
    def v_formation(num_vehicles: int = 8, spacing: float = 10, alt: float = 10) -> List[FormationPoint]:
        """
        V-shaped formation (like flying geese).
        """
        points = []
        half = num_vehicles // 2
        
        # Leader at front
        points.append(FormationPoint(1, 40, 0, alt))
        
        # Left wing
        for i in range(half):
            points.append(FormationPoint(
                i + 2,
                40 - (i + 1) * spacing,
                -(i + 1) * spacing,
                alt
            ))
        
        # Right wing
        for i in range(num_vehicles - half - 1):
            points.append(FormationPoint(
                half + i + 2,
                40 - (i + 1) * spacing,
                (i + 1) * spacing,
                alt
            ))
        
        return points
    
    @staticmethod
    def circle_formation(num_vehicles: int = 8, radius: float = 20, alt: float = 10) -> List[FormationPoint]:
        """
        Circular formation around center point.
        """
        import math
        points = []
        angle_step = 2 * math.pi / num_vehicles
        
        for i in range(num_vehicles):
            angle = i * angle_step
            north = 30 + radius * math.cos(angle)
            east = radius * math.sin(angle)
            points.append(FormationPoint(i + 1, north, east, alt))
        
        return points
    
    @staticmethod
    def grid_formation(rows: int = 2, cols: int = 4, spacing: float = 10, alt: float = 10) -> List[FormationPoint]:
        """
        Rectangular grid formation.
        """
        points = []
        vehicle_id = 1
        
        for row in range(rows):
            for col in range(cols):
                north = 20 + row * spacing
                east = (col - cols // 2) * spacing
                points.append(FormationPoint(vehicle_id, north, east, alt))
                vehicle_id += 1
        
        return points


def generate_mavproxy_script(formation: List[FormationPoint]) -> str:
    """
    Generate MAVProxy script content for a formation.
    
    Args:
        formation: List of FormationPoint objects
        
    Returns:
        String content for MAVProxy script file
    """
    lines = []
    for point in formation:
        lines.append(f"vehicle {point.vehicle_id}")
        lines.append("mode GUIDED")
        lines.append(f"guided {point.north} {point.east} {point.alt}")
    return "\n".join(lines)


def save_formation_script(formation: List[FormationPoint], filepath: str) -> None:
    """Save formation as MAVProxy script file."""
    content = generate_mavproxy_script(formation)
    with open(filepath, 'w') as f:
        f.write(content)
    print(f"Formation script saved to: {filepath}")


# Example usage and testing
if __name__ == "__main__":
    print("=== Formation Library Demo ===\n")
    
    # Generate spread formation
    spread = FormationLibrary.spread_2x4()
    print("Spread Formation (2x4):")
    print(generate_mavproxy_script(spread))
    print()
    
    # Generate V formation
    v_form = FormationLibrary.v_formation()
    print("\nV Formation:")
    print(generate_mavproxy_script(v_form))

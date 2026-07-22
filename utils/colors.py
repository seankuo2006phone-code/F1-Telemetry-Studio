"""
Color palettes for F1 teams and UI components.
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class UIColors:
    BACKGROUND: str = "#0D0D12"
    PANEL_BG: str = "#15151C"
    TEXT_PRIMARY: str = "#F1F1F2"
    TEXT_SECONDARY: str = "#8B8D97"
    GRID_LINE: str = "#23232D"
    ACCENT_RED: str = "#E10600" 

@dataclass(frozen=True)
class TeamColors:
    RED_BULL: str = "#3671C6"
    FERRARI: str = "#E80020"
    MERCEDES: str = "#27F4D2"
    MCLAREN: str = "#FF8000"
    ASTON_MARTIN: str = "#229971"
    ALPINE: str = "#0093CC"
    WILLIAMS: str = "#64C4FF"
    RB: str = "#6692FF"
    SAUBER: str = "#52E252"
    HAAS: str = "#B6BABD"
    DEFAULT: str = "#FFFFFF"

def get_team_color(team_name: str) -> str:
    name = str(team_name).upper()
    if "RED BULL" in name: return TeamColors.RED_BULL
    if "FERRARI" in name: return TeamColors.FERRARI
    if "MERCEDES" in name: return TeamColors.MERCEDES
    if "MCLAREN" in name: return TeamColors.MCLAREN
    if "ASTON MARTIN" in name: return TeamColors.ASTON_MARTIN
    if "ALPINE" in name or "RENAULT" in name: return TeamColors.ALPINE
    if "WILLIAMS" in name: return TeamColors.WILLIAMS
    if "ALPHATAURI" in name or "RB" in name or "TORO ROSSO" in name: return TeamColors.RB
    if "ALFA ROMEO" in name or "SAUBER" in name or "STAKE" in name: return TeamColors.SAUBER
    if "HAAS" in name: return TeamColors.HAAS
    return TeamColors.DEFAULT
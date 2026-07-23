"""
Domain-specific constants for Formula One telemetry analysis.
"""
from typing import Dict

SESSIONS: Dict[str, str] = {
    "FP1": "Practice 1",
    "FP2": "Practice 2",
    "FP3": "Practice 3",
    "SQ": "Sprint Shootout",
    "S": "Sprint",
    "Q": "Qualifying",
    "R": "Race"
}

TRACKS: list[str] = [
    "Bahrain", "Jeddah", "Melbourne", "Suzuka", "Shanghai", "Miami",
    "Imola", "Monaco", "Montreal", "Barcelona", "Spielberg", "Silverstone",
    "Budapest", "Spa", "Zandvoort", "Monza", "Baku", "Singapore",
    "Austin", "Mexico City", "Interlagos", "Las Vegas", "Lusail", "Abu Dhabi",
    "Paul Ricard", "Portimao", "Mugello", "Nurburgring", "Istanbul", "Sochi"
]

DRIVERS: Dict[str, str] = {
    "FASTEST OVERALL": "Fastest Overall",
    "VER": "Max Verstappen", "NOR": "Lando Norris", "LEC": "Charles Leclerc",
    "SAI": "Carlos Sainz", "HAM": "Lewis Hamilton", "RUS": "George Russell",
    "PIA": "Oscar Piastri", "PER": "Sergio Perez", "ALO": "Fernando Alonso",
    "STR": "Lance Stroll", "GAS": "Pierre Gasly", "OCO": "Esteban Ocon",
    "TSU": "Yuki Tsunoda", "ALB": "Alexander Albon", "BOT": "Valtteri Bottas",
    "MAG": "Kevin Magnussen", "HUL": "Nico Hulkenberg", "RIC": "Daniel Ricciardo",
    "ZHO": "Zhou Guanyu", "SAR": "Logan Sargeant", "VET": "Sebastian Vettel",
    "RAI": "Kimi Raikkonen", "MSC": "Mick Schumacher", "GIO": "Antonio Giovinazzi",
    "LAT": "Nicholas Latifi", "KUB": "Robert Kubica", "MAZ": "Nikita Mazepin",
    "DEV": "Nyck de Vries", "BEA": "Oliver Bearman", "LAW": "Liam Lawson",
    "COL": "Franco Colapinto"
}
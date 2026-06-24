from fastapi import APIRouter, HTTPException
from app.engines.players import player_analyzer

router = APIRouter()


@router.get("/nations")
def get_all_nations():
    return player_analyzer.get_all_nations()


@router.get("/clusters")
def get_cluster_profiles():
    return player_analyzer.get_cluster_profiles()


@router.get("/team-composition")
def get_all_team_composition():
    return player_analyzer.get_team_composition()


@router.get("/team-composition/{nation}")
def get_nation_composition(nation: str):
    comp = player_analyzer.get_team_composition(nation)
    if not comp:
        raise HTTPException(status_code=404, detail=f"No data for '{nation}'")
    return comp


@router.get("/players/{nation}")
def get_team_players(nation: str):
    players = player_analyzer.get_team_players(nation)
    if not players:
        raise HTTPException(status_code=404, detail=f"No players found for '{nation}'")
    return players


@router.get("/archetypes/{cluster_name}")
def get_top_by_archetype(cluster_name: str, limit: int = 10):
    return player_analyzer.get_top_by_cluster(cluster_name, limit)

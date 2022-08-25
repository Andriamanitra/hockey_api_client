import pytest

import hockey_api_client as nhl
from hockey_api_client import NotFoundException

# TODO: figure out some way to store api responses locally and mock the api


def test_conferences_all():
    current_conferences = nhl.Conferences.all()
    assert len(current_conferences) == 2
    assert current_conferences[0].active
    assert current_conferences[1].active


def test_conferences_by_id():
    eastern = nhl.Conference.by_id(6)
    assert str(eastern) == "Eastern"
    assert eastern.link == "https://statsapi.web.nhl.com/api/v1/conferences/6"


def test_divisions_all():
    current_divisions = nhl.Divisions.all()
    assert len(current_divisions) == 4


def test_divisions_by_id():
    pacific = nhl.Division.by_id(15)
    assert pacific.name == "Pacific"


def test_divisions_by_id_not_found():
    with pytest.raises(NotFoundException):
        nhl.Division.by_id(0)


def test_franchise_all():
    franchises = nhl.Franchises.all()
    assert 20 < len(franchises)


def test_franchise_by_id():
    bruins = nhl.Franchise.by_id(6)
    assert str(bruins) == "Boston Bruins"
    assert bruins.first_season_id == 19241925


def test_franchise_by_id_not_found():
    with pytest.raises(NotFoundException):
        nhl.Franchise.by_id(0)
    with pytest.raises(NotFoundException):
        nhl.Franchise.by_id(9001)


def test_franchise_by_location():
    edm_teams = nhl.Franchise.by_location("Edmonton")
    assert len(edm_teams) == 1
    oilers = edm_teams[0]
    assert oilers.location == "Edmonton"
    assert oilers.team_name == "Oilers"


def test_franchise_by_location_not_found():
    teams = nhl.Franchise.by_location("Ecuador")
    assert teams == []


def test_franchise_by_location_accents():
    mtl = nhl.Franchises.by_location("montréal")
    assert len(mtl) == 3
    mtl2 = nhl.Franchise.by_location("montrEal")
    assert len(mtl2) == 3


def test_franchise_by_name():
    rags = nhl.Franchise.by_name("Rangers")
    assert rags.location == "New York"


def test_franchise_by_name_not_found():
    with pytest.raises(NotFoundException):
        nhl.Franchise.by_name("Bitch Pigeons")


def test_franchise_link_validator():
    fr = nhl.Franchise.by_id(23)
    assert fr.link == "https://statsapi.web.nhl.com/api/v1/franchises/23"

# TODO: test Team


@pytest.mark.skip("I don't feel like testing this")
def test_franchise_not_duplicated():
    oilers_team = nhl.Team.by_id(22)
    oilers_franchise = nhl.Franchise.by_id(25)
    assert oilers_team.franchise is oilers_franchise


@pytest.mark.skip("I don't feel like testing this")
def test_team():
    oilers = nhl.Team.by_id(22)
    assert oilers.team_name == "Oilers"
    assert oilers.franchise.team_name == "Oilers"

from __future__ import annotations

import unicodedata
from typing import Any
from typing import ClassVar

import httpx
from pydantic import BaseModel
from pydantic import Extra
from pydantic import Field
from pydantic import validator

API_BASE_URL = "https://statsapi.web.nhl.com"


def clean_str(s: str) -> bytes:
    normalized_str = unicodedata.normalize("NFKD", s).casefold()
    return normalized_str.encode("ASCII", "ignore")


def string_equal(orig: str, search: str) -> bool:
    """
    Check if two strings are equal after normalizing characters with accents
    and other nasty stuff (case-insensitive).

    Examples:
    ========
    assert string_equal("Montréal", "montreal") is True
    assert string_equal("ab", "abc") is False
    """
    return clean_str(orig) == clean_str(search)


def link_validator(field_name: str):
    """
    Used as a validator for "link" fields of the models to
    turn links returned by the API (without base url) into
    something clickable.

    Examples:
    ========
    # inside a class inheriting from pydantic.BaseModel
    _link_validator = link_validator("link")
    """
    def prepend_base_url(link: str):
        return f"{API_BASE_URL}{link}"

    return validator(field_name, allow_reuse=True)(prepend_base_url)


class NotFoundException(Exception):
    pass


class Conference(BaseModel, extra=Extra.forbid):
    id: int
    name: str
    link: str
    abbreviation: str | None
    short_name: str | None = Field(None, alias="shortName")
    active: bool | None

    possible_expands: ClassVar[list[str]] = []

    # validators
    _link_validator = link_validator("link")

    def __str__(self):
        return self.name

    @classmethod
    def all(cls) -> list[Conference]:
        """
        Get a list of all currently active conferences in the league.

        Examples:
        ========
        conferences = Conference.all()
        """
        resp = httpx.get(f"{API_BASE_URL}/api/v1/conferences")
        resp_dict = resp.json()
        return [cls.parse_obj(obj) for obj in resp_dict["conferences"]]

    @classmethod
    def by_id(cls, id: int) -> Conference:
        """
        Find a conference by its id, raises an exception if not found

        Examples:
        ========
        cmbl = Conference.by_id(6)
        """
        resp = httpx.get(
            f"{API_BASE_URL}/api/v1/conferences",
            params={"conferenceId": id}
        )
        conferences = resp.json()["conferences"]
        if conferences == []:
            raise NotFoundException(f"No conference with {id=}")
        conference_obj, = conferences
        return cls.parse_obj(conference_obj)


class Division(BaseModel, extra=Extra.forbid):
    """
    Class representing a division in the National Hockey League.
    For most (but not all) of the NHL history the teams playing in the league have been
    divided into divisions. The names of the divisions (and which teams play in which
    division) have changed multiple times during the history of the league.

    Data source urls:
    ================
    https://statsapi.web.nhl.com/api/v1/divisions
    https://statsapi.web.nhl.com/api/v1/divisions/15
    https://statsapi.web.nhl.com/api/v1/divisions?divisionId=1,2,3&expand=division.conference
    """
    id: int
    name: str
    link: str
    abbreviation: str | None
    short_name: str | None = Field(None, alias="nameShort")
    conference: Conference | None
    active: bool | None

    possible_expands: ClassVar[list[str]] = [
        # Adds conference.{abbreviation,shortName,active}
        "division.conference",
    ]

    # validators
    _link_validator = link_validator("link")

    @classmethod
    def all(cls, expands: list[str] = []) -> list[Division]:
        """
        Get a list of all currently active divisions in the league.

        Examples:
        ========
        divisions = Division.all(expands=["division.conference"])
        """
        resp = httpx.get(f"{API_BASE_URL}/api/v1/divisions")
        resp_dict = resp.json()
        return [cls.parse_obj(obj) for obj in resp_dict["divisions"]]

    @classmethod
    def by_id(cls, id: int, expands: list[str] = []) -> Division:
        """
        Find a division by its id, raises an exception if not found

        Examples:
        ========
        pacific = Division.by_id(15)
        """
        resp = httpx.get(
            f"{API_BASE_URL}/api/v1/divisions",
            params={"divisionId": id, "expand": expands}
        )
        divisions = resp.json()["divisions"]
        if divisions == []:
            raise NotFoundException(f"No division with {id=}")
        division_obj, = divisions
        return cls.parse_obj(division_obj)


class Franchise(BaseModel, extra=Extra.forbid):
    """
    Class representing a National Hockey League franchise.
    Note that franchise is not the same as a team. This distinction is
    relevant for franchises that have changed name or location over the years.
    Franchise contains the up-to-date name and location but Teams will retain
    the name used at the time. For example the Team "Minnesota North Stars" is
    part of the "Dallas Stars" Franchise.

    Data source urls:
    ================
    https://statsapi.web.nhl.com/api/v1/franchises
    """
    id: int = Field(..., alias="franchiseId")
    team_name: str = Field(..., alias="teamName")
    location: str = Field(..., alias="locationName")
    most_recent_team_id: int = Field(..., alias="mostRecentTeamId")
    first_season_id: int = Field(..., alias="firstSeasonId")
    last_season_id: int | None = Field(None, alias="lastSeasonId")
    link: str

    possible_expands: ClassVar[list[str]] = []

    _fetched: ClassVar[bool] = False
    franchises_by_id: ClassVar[dict[int, Franchise]] = {}

    # validators
    _link_validator = link_validator("link")

    def __str__(self) -> str:
        return f"{self.location} {self.team_name}"

    @classmethod
    def all(cls) -> list[Franchise]:
        """
        Get a list of all franchises (both active and inactive).
        Because the list of franchises rarely changes, the results are
        cached so subsequent calls to methods in Franchise do not trigger
        network requests.
        """
        if cls._fetched:
            return list(cls.franchises_by_id.values())

        resp = httpx.get(f"{API_BASE_URL}/api/v1/franchises")
        resp_dict = resp.json()
        for franchise_json in resp_dict["franchises"]:
            franchise = Franchise.parse_obj(franchise_json)
            cls.franchises_by_id[franchise.id] = franchise
        Franchise._fetched = True
        return list(cls.franchises_by_id.values())

    @classmethod
    def by_id(cls, id: int) -> Franchise:
        """
        Find a franchise by its id. Raises an exception if not found.
        """
        if not cls._fetched:
            cls.all()
        try:
            return cls.franchises_by_id[id]
        except KeyError:
            raise NotFoundException(f"No franchise with {id=}")

    @classmethod
    def by_name(cls, name: str) -> Franchise:
        """
        Find a franchise by its name (NOT including location). Case-insensitive.
        Raises an exception if not found.

        Example:
        =======
        habs = Franchise.by_name("canadiens")
        """
        for fr in cls.all():
            if string_equal(fr.team_name, name):
                return fr
        raise NotFoundException(f"No franchise with {name=}")

    @classmethod
    def by_location(cls, location: str) -> list[Franchise]:
        """
        Find franchises by location. Case-insensitive.

        Example:
        montreal_teams = Franchise.by_location("montreal")
        """
        return [fr for fr in cls.all() if string_equal(fr.location, location)]


class Team(BaseModel, extra=Extra.forbid):
    """
    Class representing a National Hockey League team.
    Teams exist for multiple seasons but when a relocation happens they get a
    new id. It seems simple name changes do not cause a new id to be assigned
    (for example "Mighty Ducks of Anaheim" (1993–2006) do not have their own
    team id, they have been renamed to "Anaheim Ducks").

    Data source urls:
    ================
    https://statsapi.web.nhl.com/api/v1/teams
    https://statsapi.web.nhl.com/api/v1/teams?teamId=1,2,3
    https://statsapi.web.nhl.com/api/v1/teams?season=20112012
    https://statsapi.web.nhl.com/api/v1/teams/1
    https://statsapi.web.nhl.com/api/v1/teams/1?expand=team.stats,team.roster,team.division,team.conference,team.franchise,team.schedule.previous,team.schedule.next,team.ticket,team.content.home.all,team.content.sections,team.record,team.playoffs,team.name,team.social,team.deviceProperties
    """
    id: int
    name: str
    abbreviation: str
    team_name: str = Field(..., alias="teamName")
    short_name: str = Field(..., alias="shortName", repr=False)
    location: str = Field(..., alias="locationName")
    franchise_id: int = Field(..., alias="franchiseId")
    active: bool
    link: str
    first_year_of_play: str = Field("unknown", alias="firstYearOfPlay")
    venue: dict | None  # FIXME: implement Venue model
    division: Division
    conference: Conference | None
    franchise: Franchise | None
    official_site_url: str | None = Field(None, alias="officialSiteUrl")

    # these get added when using certain expands
    # FIXME: implement models for most of these
    team_stats: dict | None = Field(None, alias="teamStats")
    roster: dict | None = None
    next_game_schedule: dict | None = Field(None, alias="nextGameSchedule")
    previous_game_schedule: dict | None = Field(None, alias="previousGameSchedule")
    content: dict | None = None
    device_properties: dict | None = Field(None, alias="deviceProperties")
    social: dict | None = None
    record: dict | None = None
    playoff_info: dict | None = Field(None, alias="playoffInfo")
    tickets: dict | None = None
    other_names: dict | None = Field(None, alias="otherNames")

    possible_expands: ClassVar[list[str]] = [
        # Adds team_stats
        "team.stats",
        # Adds roster
        "team.roster",
        # Adds division.conference (but conference is already included in team root)
        "team.division",
        # Adds conference.{abbreviation,short_name,active}
        "team.conference",
        # This one is always unnecessary because the implementation uses Franchise class
        # to get the full franchise information directly anyway.
        # (would add franchise.{first_season_id,most_recent_team_id,location})
        "team.franchise",
        # Adds previous_game_schedule
        "team.schedule.previous",
        # Adds next_game_schedule
        "team.schedule.next",
        # Adds tickets
        "team.ticket",
        # Adds content
        "team.content.home.all",
        "team.content.sections",
        # Adds record (regular season)
        "team.record",
        # Adds playoff_info
        "team.playoffs",
        # Adds other_names
        "team.name",
        # Adds social (may contain links to twitter, facebook, instagram...)
        "team.social",
        # Adds device_properties (likely not very useful, I think this is made for a mobile app of some sort)
        "team.deviceProperties",
    ]

    # validators
    _link_validator = link_validator("link")

    @classmethod
    def from_obj(cls, obj: dict[str, Any]):
        # obj["franchise"] is always present in responses from the /teams end
        # point but it's missing some data unless ?expand=team.franchise was
        # specified, so we overwrite the field with data directly from
        # the Franchise class. Doing it this way also allows us to re-use the
        # same Franchise objects rather than creating a new one each time a
        # Team object is parsed.
        del obj["franchise"]
        team = cls.parse_obj(obj)
        team.franchise = Franchise.by_id(team.franchise_id)
        return team

    @classmethod
    def all(cls, expands: list[str] = []) -> list[Team]:
        """
        Return a list of all teams that are currently active

        Examples:
        ========
        currently_active_teams = Team.all()
        """
        resp = httpx.get(
            f"{API_BASE_URL}/api/v1/teams",
            params={"expand": expands}
        )
        resp_dict = resp.json()
        return [cls.from_obj(team_dict) for team_dict in resp_dict["teams"]]

    @classmethod
    def by_id(cls, id: int, expands: list[str] = []) -> Team:
        """
        Find a team by its id, raises an exception if not found

        Example:
        =======
        oilers = Team.by_id(22, expands=["team.stats"])
        """
        resp = httpx.get(
            f"{API_BASE_URL}/api/v1/teams",
            params={"teamId": id, "expand": expands}
        )
        resp_dict = resp.json()
        team = cls.from_obj(resp_dict["teams"][0])
        return team

    @classmethod
    def by_season(cls, season_id: int, expands: list[str] = []) -> list[Team]:
        """
        Return a list of teams active during the given season.

        Examples:
        ========
        teams = Team.by_season(20112012)  # Teams active during season 2011-2012
        """
        resp = httpx.get(
            f"{API_BASE_URL}/api/v1/teams",
            params={"season": season_id, "expand": expands}
        )
        resp_dict = resp.json()
        return [cls.from_obj(team_dict) for team_dict in resp_dict["teams"]]


Franchises = Franchise
Teams = Team
Divisions = Division
Conferences = Conference

Conference.by_id(6)

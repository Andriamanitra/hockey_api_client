**NOTE** The old nhl.com API at https://statsapi.web.nhl.com/api stopped working in October 2023 so continuing this (very unfinished) project is pointless.

# Hockey API Client

Python wrapper for NHL.com api (https://statsapi.web.nhl.com/api/v1). Since there is no official documentation for the API (that I'm aware of), this work is largely based on the documentation by dword4 on Gitlab: https://gitlab.com/dword4/nhlapi/-/blob/master/stats-api.md

## Work in progress!

End points covered (roughly in the order in which I am planning to implement them):
- [x] Franchises
- [x] Teams
- [x] Divisions
- [x] Conferences
- [ ] People (=players)
- [ ] Games
- [ ] Player stats
- [ ] Team stats
- [ ] Standings
- [ ] Schedule
- [ ] Seasons
- [ ] Venues
- [ ] Prospects
- [ ] Draft
- [ ] Awards
- [ ] Tournaments

## Example usage

```pycon
>>> import hockey_api_client as nhl
>>> nhl.Franchise.by_name("maroons")
Franchise(id=7, team_name='Maroons', location='Montreal', most_recent_team_id=43, first_
season_id=19241925, last_season_id=19371938, link='https://statsapi.web.nhl.com/api/v1/f
ranchises/7')
>>> ", ".join(team.name for team in nhl.Teams.by_season(19371938))
'Chicago Blackhawks, Detroit Red Wings, New York Rangers, Boston Bruins, Montréal Canadi
ens, Toronto Maple Leafs, Montreal Maroons, New York Americans'
```

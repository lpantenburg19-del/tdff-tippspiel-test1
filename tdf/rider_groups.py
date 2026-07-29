from .models import Rider, Team

TEAM_COLORS = [
    "#fde68a", "#bfdbfe", "#bbf7d0", "#fbcfe8", "#fdba74",
    "#ddd6fe", "#a7f3d0", "#fca5a5", "#c7d2fe", "#fef08a",
    "#d9f99d", "#fecaca", "#99f6e4", "#e9d5ff",
]


def team_color_map():
    names = sorted(t.name for t in Team.query.all())
    return {name: TEAM_COLORS[i % len(TEAM_COLORS)] for i, name in enumerate(names)}


def build_rider_groups():
    """Riders grouped by team (sorted alphabetically), each team with a stable
    color. Within each team, the captain (first rider in startlist) appears first,
    then other riders alphabetically.
    """
    colors = team_color_map()
    riders = (
        Rider.query.order_by(Rider.team_name.asc(), Rider.is_captain.desc(), Rider.name.asc()).all()
    )

    groups = {}
    order = []
    for r in riders:
        team = r.team_name or "Ohne Team"
        if team not in groups:
            groups[team] = []
            order.append(team)
        groups[team].append(r)

    return [
        {
            "team_name": team,
            "color": colors.get(team, "#e5e5e5"),
            "riders": [{"name": r.name, "is_captain": r.is_captain} for r in groups[team]],
        }
        for team in order
    ]


def build_team_options():
    colors = team_color_map()
    return [{"name": name, "color": color} for name, color in sorted(colors.items())]

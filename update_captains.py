#!/usr/bin/env python
"""Update Tour de France Femmes 2026 team captains based on official rosters.

Run this script after syncing the startlist to set correct captains:
    python update_captains.py

Captains are identified from official team rosters published by cycling media
and team announcements for the 2026 Tour de France Femmes (1-9 August 2026).
"""

from tdf import create_app

app = create_app()

with app.app_context():
    from tdf.models import Rider
    from tdf.db import db

    # Official team captains/leaders for Tour de France Femmes 2026
    # Source: Team rosters from official announcements, Wikipedia, Cycling Weekly
    captains = {
        'AG Insurance - Soudal Team (WTW)': 'LE COURT-PIENAAR Kim',
        'CANYON//SRAM (WTW)': 'NIEWIADOMA Kasia',
        'Cofidis Women Team (PRW)': 'GUILMAN Victorie',
        'EF Education-Oatly (WTW)': 'FAULKNER Kristen',
        'FDJ United - SUEZ (WTW)': 'VOLLERING Demi',
        'Fenix-Premier Tech (WTW)': 'PIETERSE Puck',
        'Human Powered Health (WTW)': 'DE JONG Thalita',
        'Laboral Kutxa - Fundación Euskadi (PRW)': 'FIDANZA Arianna',
        'Lidl - Trek (WTW)': 'FISHER-BLACK Niamh',
        'Liv AlUla Jayco (WTW)': 'TRINCA COLONEL Monica',
        'Lotto Intermarché Ladies (PRW)': 'TAS Sandrine',
        'Ma Petite Entreprise (PRW)': 'MAHÉ Océane',
        'Mayenne Monbana My Pie (PRW)': 'PEREKITKO Karolina',
        'Movistar Team (WTW)': 'REUSSER Marlen',
        'St Michel - Preference Home - Auber93 (PRW)': 'JACKSON Alison',
        'Team Picnic PostNL (WTW)': 'CIABOCCO Eleonora',
        'Team SD Worx - Protime (WTW)': 'KOPECKY Lotte',
        'Team Visma | Lease a Bike (WTW)': 'FERRAND-PRÉVOT Pauline',
        'UAE Team L\'IMAD (WTW)': 'LONGO BORGHINI Elisa',
        'Uno-X Mobility (WTW)': 'BEEKHUIS Teuntje',
        'VolkerWessels Cycling Team (PRW)': 'RIJNBEEK Maud',
    }

    # Reset all captains first
    reset_count = Rider.query.filter_by(is_captain=True).count()
    for rider in Rider.query.filter_by(is_captain=True):
        rider.is_captain = False

    # Set correct captains
    updated = 0
    not_found = []

    for team, captain_name in sorted(captains.items()):
        rider = Rider.query.filter_by(name=captain_name, team_name=team).first()
        if rider:
            rider.is_captain = True
            updated += 1
            print(f'✓ {captain_name:30} ({team})')
        else:
            not_found.append((captain_name, team))
            print(f'✗ NOT FOUND: {captain_name:30} ({team})')

    db.session.commit()

    print(f'\n✓ Captains updated: {updated}/{len(captains)}')
    if not_found:
        print(f'✗ Not found: {len(not_found)}')
        for name, team in not_found:
            print(f'   - {name} ({team})')
    else:
        print('✓ All captains found and updated!')

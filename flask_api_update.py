"""
ANLEITUNG: Flask API Update für echte NBA Spiele

Ersetze die /api/today-games Route in deiner nba_flask_api.py mit folgendem Code:
"""

# ====================
# AM ANFANG DER DATEI HINZUFÜGEN (nach den anderen imports):
# ====================

from nba_games_loader import NBAGamesLoader

# Initialisiere Games Loader
games_loader = NBAGamesLoader()


# ====================
# ERSETZE DIE /api/today-games ROUTE MIT:
# ====================

@app.route('/api/today-games', methods=['GET'])
def get_today_games():
    """Lädt heutige NBA-Spiele (LIVE von NBA API)"""
    
    try:
        # Lade echte Spiele mit Fallback auf Mock-Daten
        games = games_loader.get_games_with_fallback()
        
        return jsonify({
            'success': True,
            'count': len(games),
            'games': games,
            'source': 'NBA Live API' if games else 'Mock Data'
        })
    
    except Exception as e:
        print(f"❌ Fehler beim Laden der Spiele: {e}")
        
        # Fallback auf Mock-Daten bei Fehler
        mock_games = [
            {
                'game_id': 'mock_001',
                'date': '2024-10-22',
                'time': '7:30 PM ET',
                'team1_abbr': 'LAL',
                'team2_abbr': 'GSW',
                'team1_name': 'Lakers',
                'team2_name': 'Warriors',
                'matchup': 'LAL vs GSW'
            },
            {
                'game_id': 'mock_002',
                'date': '2024-10-22',
                'time': '8:00 PM ET',
                'team1_abbr': 'BOS',
                'team2_abbr': 'MIA',
                'team1_name': 'Celtics',
                'team2_name': 'Heat',
                'matchup': 'BOS vs MIA'
            }
        ]
        
        return jsonify({
            'success': True,
            'count': len(mock_games),
            'games': mock_games,
            'source': 'Mock Data (Fallback)',
            'error': str(e)
        })

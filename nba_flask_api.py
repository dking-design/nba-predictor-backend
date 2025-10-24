from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import numpy as np
from datetime import datetime, timedelta
from nba_synergy_system import TeamSynergyCalculator
from nba_lineup_predictor import NBALineupPredictor

app = Flask(__name__)
CORS(app)  # Erlaubt Zugriff von PWA

# Initialisiere Predictor
predictor = NBALineupPredictor()
players_data = predictor.players

class NumpyEncoder(json.JSONEncoder):
    """JSON Encoder fÃ¼r NumPy types"""
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)

app.json_encoder = NumpyEncoder

@app.route('/')
def home():
    """API Info"""
    return jsonify({
        'name': 'NBA Predictor API',
        'version': '1.0',
        'endpoints': {
            '/api/players': 'GET - Liste aller Spieler',
            '/api/players/search': 'GET - Spieler suchen',
            '/api/predict': 'POST - Vorhersage machen',
            '/api/prediction-stats': 'GET - Prediction Accuracy Stats',
            '/api/today-games': 'GET - Heutige NBA-Spiele'
        }
    })

@app.route('/api/players', methods=['GET'])
def get_players():
    """Gibt alle Spieler zurÃ¼ck"""
    # Vereinfachte Player-Liste
    players_list = []
    
    for name, data in players_data.items():
        players_list.append({
            'name': name,
            'team': data['team'],
            'pts': round(data['stats'].get('PTS', 0), 1),
            'type': data['type']
        })
    
    # Sortiere nach Punkten
    players_list.sort(key=lambda x: x['pts'], reverse=True)
    
    return jsonify({
        'success': True,
        'count': len(players_list),
        'players': players_list
    })

@app.route('/api/players/search', methods=['GET'])
def search_players():
    """Sucht Spieler"""
    query = request.args.get('q', '').lower()
    
    if not query:
        return jsonify({'success': False, 'error': 'Query parameter required'})
    
    matches = []
    for name, data in players_data.items():
        if query in name.lower():
            matches.append({
                'name': name,
                'team': data['team'],
                'pts': round(data['stats'].get('PTS', 0), 1),
                'type': data['type']
            })
    
    matches.sort(key=lambda x: x['pts'], reverse=True)
    
    return jsonify({
        'success': True,
        'count': len(matches),
        'players': matches[:10]  # Max 10 Ergebnisse
    })

@app.route('/api/player/<name>', methods=['GET'])
def get_player_details(name):
    """Gibt detaillierte Spieler-Info"""
    player = players_data.get(name)
    
    if not player:
        return jsonify({'success': False, 'error': 'Player not found'}), 404
    
    return jsonify({
        'success': True,
        'player': {
            'name': name,
            'team': player['team'],
            'type': player['type'],
            'stats': {
                'pts': round(player['stats'].get('PTS', 0), 1),
                'reb': round(player['stats'].get('REB', 0), 1),
                'ast': round(player['stats'].get('AST', 0), 1),
                'fg_pct': round(player['stats'].get('FG_PCT', 0) * 100, 1),
                'fg3_pct': round(player['stats'].get('FG3_PCT', 0) * 100, 1),
                'minutes': round(player['stats'].get('MIN', 0), 1)
            }
        }
    })

@app.route('/api/predict', methods=['POST'])
def make_prediction():
    """Macht eine Vorhersage"""
    data = request.get_json()
    
    # Validiere Input
    if not data or 'team1_lineup' not in data or 'team2_lineup' not in data:
        return jsonify({
            'success': False,
            'error': 'team1_lineup and team2_lineup required'
        }), 400
    
    team1_lineup = data['team1_lineup']
    team2_lineup = data['team2_lineup']
    team1_name = data.get('team1_name', 'Team 1')
    team2_name = data.get('team2_name', 'Team 2')
    team1_home = data.get('team1_home', True)
    
    # Validiere Lineups
    if len(team1_lineup) != 5 or len(team2_lineup) != 5:
        return jsonify({
            'success': False,
            'error': 'Each lineup must have exactly 5 players'
        }), 400
    
    # PrÃ¼fe ob alle Spieler existieren
    for player in team1_lineup + team2_lineup:
        if player not in players_data:
            return jsonify({
                'success': False,
                'error': f'Player not found: {player}'
            }), 404
    
    try:
        # Mache Vorhersage
        result = predictor.predict_game(team1_lineup, team2_lineup, team1_home)
        
        if not result:
            return jsonify({
                'success': False,
                'error': 'Prediction failed'
            }), 500
        
        # Berechne Synergien
        comparison = result['comparison']
        
        # Matchup-Analyse
        matchups_t1 = []
        matchups_t2 = []
        
        for player in team1_lineup:
            p_data = players_data[player]
            matchups_t1.append({
                'player': player,
                'pts': round(p_data['stats'].get('PTS', 0), 1),
                'type': p_data['type']
            })
        
        for player in team2_lineup:
            p_data = players_data[player]
            matchups_t2.append({
                'player': player,
                'pts': round(p_data['stats'].get('PTS', 0), 1),
                'type': p_data['type']
            })
        
        # NEU: Prediction-Tracking
        try:
            from nba_prediction_tracker import PredictionTracker
            
            tracker = PredictionTracker()
            
            # Extrahiere Team-KÃ¼rzel (falls vorhanden)
            team1_abbr = data.get('team1_abbr', team1_name)
            team2_abbr = data.get('team2_abbr', team2_name)
            game_date = data.get('game_date', datetime.now().strftime('%Y-%m-%d'))
            
            # Log die Vorhersage
            tracker.log_prediction(
                team1=team1_abbr,
                team2=team2_abbr,
                predicted_winner=team1_name if result['winner'] == 1 else team2_name,
                predicted_score=f"{result['team1_score']}-{result['team2_score']}",
                confidence=result['confidence'],
                game_date=game_date
            )
            print(f"âœ“ Prediction logged: {team1_abbr} vs {team2_abbr}")
        except Exception as e:
            # Tracking-Fehler nicht kritisch
            print(f"âš ï¸ Tracking failed: {e}")
        
        # Response
        return jsonify({
            'success': True,
            'prediction': {
                'team1_name': team1_name,
                'team2_name': team2_name,
                'team1_score': result['team1_score'],
                'team2_score': result['team2_score'],
                'winner': team1_name if result['winner'] == 1 else team2_name,
                'team1_win_prob': round(result['team1_win_prob'] * 100, 1),
                'team2_win_prob': round(result['team2_win_prob'] * 100, 1),
                'confidence': round(result['confidence'] * 100, 1)
            },
            'synergies': {
                'team1': {
                    name: round(val, 1) for name, val in comparison['team1']['synergies'].items()
                },
                'team2': {
                    name: round(val, 1) for name, val in comparison['team2']['synergies'].items()
                }
            },
            'lineups': {
                'team1': matchups_t1,
                'team2': matchups_t2
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/teams', methods=['GET'])
def get_teams():
    """Gibt alle NBA Teams zurÃ¼ck"""
    teams = {}
    
    for player_name, player_data in players_data.items():
        team = player_data['team']
        if team not in teams:
            teams[team] = []
        teams[team].append(player_name)
    
    team_list = [
        {
            'abbreviation': abbr,
            'player_count': len(players)
        }
        for abbr, players in teams.items()
    ]
    
    team_list.sort(key=lambda x: x['abbreviation'])
    
    return jsonify({
        'success': True,
        'count': len(team_list),
        'teams': team_list
    })

@app.route('/api/today-games', methods=['GET'])
def get_today_games():
    """LÃ¤dt heutige und morgige NBA-Spiele (Mock-Daten fÃ¼r Test)"""
    
    # Mock-Daten fÃ¼r Testing
    mock_games = [
        {
            'game_id': '0022400001',
            'date': '2024-10-22',
            'time': '7:30 PM ET',
            'team1_abbr': 'LAL',
            'team2_abbr': 'GSW',
            'team1_name': 'Lakers',
            'team2_name': 'Warriors',
            'matchup': 'LAL vs GSW'
        },
        {
            'game_id': '0022400002',
            'date': '2024-10-22',
            'time': '8:00 PM ET',
            'team1_abbr': 'BOS',
            'team2_abbr': 'MIA',
            'team1_name': 'Celtics',
            'team2_name': 'Heat',
            'matchup': 'BOS vs MIA'
        },
        {
            'game_id': '0022400003',
            'date': '2024-10-23',
            'time': '7:00 PM ET',
            'team1_abbr': 'PHX',
            'team2_abbr': 'LAC',
            'team1_name': 'Suns',
            'team2_name': 'Clippers',
            'matchup': 'PHX vs LAC'
        },
        {
            'game_id': '0022400004',
            'date': '2024-10-23',
            'time': '8:30 PM ET',
            'team1_abbr': 'DAL',
            'team2_abbr': 'DEN',
            'team1_name': 'Mavericks',
            'team2_name': 'Nuggets',
            'matchup': 'DAL vs DEN'
        }
    ]
    
    return jsonify({
        'success': True,
        'count': len(mock_games),
        'games': mock_games
    })
@app.route('/api/prediction-stats', methods=['GET'])
def get_prediction_stats():
    """Gibt Prediction-Tracking Statistiken zurÃ¼ck"""
    try:
        from nba_prediction_tracker import PredictionTracker
        
        tracker = PredictionTracker()
        
        return jsonify({
            'success': True,
            'stats': tracker.stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health Check fÃ¼r Deployment"""
    return jsonify({
        'status': 'healthy',
        'players_loaded': len(players_data)
    })


if __name__ == '__main__':
    print("\n" + "="*60)
    print("ðŸ€ NBA PREDICTOR API")
    print("="*60)
    print(f"\nAPI lÃ¤uft auf: http://localhost:5001")
    print(f"Spieler geladen: {len(players_data)}")
    print("\nEndpoints:")
    print("  GET  /api/players")
    print("  GET  /api/players/search?q=LeBron")
    print("  GET  /api/player/<name>")
    print("  POST /api/predict")
    print("  GET  /api/teams")
    print("  GET  /api/today-games  â† NEU!")
    print("  GET  /api/prediction-stats")
    print("\n" + "="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5001)

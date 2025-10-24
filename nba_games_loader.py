#!/usr/bin/env python3
"""
NBA Games Loader - ROBUST VERSION
Lädt heutige Spiele, morgen nur als Fallback mit Error Handling
"""

from nba_api.live.nba.endpoints import scoreboard
from datetime import datetime, timedelta
import time

class NBAGamesLoader:
    """Lädt heutige NBA Spiele (morgen nur als Safe Fallback)"""
    
    def __init__(self):
        self.games = []
    
    def get_todays_games(self):
        """Holt heutige NBA Spiele (Live API)"""
        try:
            print("📡 Lade heutige NBA Spiele...")
            
            board = scoreboard.ScoreBoard()
            games_data = board.games.get_dict()
            
            parsed_games = []
            today = datetime.now().strftime('%Y-%m-%d')
            
            for game in games_data:
                try:
                    game_id = game.get('gameId', '')
                    game_status = game.get('gameStatusText', '')
                    game_status_num = game.get('gameStatus', 0)
                    
                    # Skip finished games (Status 3)
                    if game_status_num == 3:
                        continue
                    
                    home_team = game.get('homeTeam', {})
                    home_name = home_team.get('teamName', 'Home')
                    home_abbr = home_team.get('teamTricode', 'HOM')
                    
                    away_team = game.get('awayTeam', {})
                    away_name = away_team.get('teamName', 'Away')
                    away_abbr = away_team.get('teamTricode', 'AWY')
                    
                    game_time_utc = game.get('gameTimeUTC', '')
                    if game_time_utc:
                        try:
                            dt = datetime.fromisoformat(game_time_utc.replace('Z', '+00:00'))
                            game_time = dt.strftime('%I:%M %p ET')
                        except:
                            game_time = game_status
                    else:
                        game_time = game_status
                    
                    parsed_games.append({
                        'game_id': game_id,
                        'date': today,
                        'time': game_time,
                        'team1_abbr': home_abbr,
                        'team2_abbr': away_abbr,
                        'team1_name': home_name,
                        'team2_name': away_name,
                        'matchup': f"{home_abbr} vs {away_abbr}",
                        'status': game_status
                    })
                    
                except Exception as e:
                    print(f"⚠️ Fehler beim Parsen eines Spiels: {e}")
                    continue
            
            print(f"✅ Heute: {len(parsed_games)} Spiele")
            return parsed_games
            
        except Exception as e:
            print(f"❌ Fehler beim Laden heutiger Spiele: {e}")
            return []
    
    def get_tomorrows_games_safe(self):
        """
        Versucht morgige Spiele zu laden (mit Safe Error Handling)
        Falls es nicht funktioniert, einfach leere Liste zurück
        """
        try:
            print("📡 Versuche morgige NBA Spiele zu laden...")
            
            from nba_api.stats.endpoints import ScoreboardV2
            
            tomorrow = (datetime.now() + timedelta(days=1)).strftime('%m/%d/%Y')
            tomorrow_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
            
            board = ScoreboardV2(game_date=tomorrow)
            time.sleep(1)
            
            games_df = board.game_header.get_data_frame()
            
            if len(games_df) == 0:
                print("⚠️ Keine Spiele morgen in API")
                return []
            
            # Versuche Series Standings
            try:
                series_df = board.series_standings.get_data_frame()
            except:
                print("⚠️ Series Standings nicht verfügbar")
                series_df = None
            
            parsed_games = []
            
            for _, game in games_df.iterrows():
                try:
                    game_id = game['GAME_ID']
                    home_team_id = game['HOME_TEAM_ID']
                    visitor_team_id = game['VISITOR_TEAM_ID']
                    game_time = game.get('GAME_STATUS_TEXT', 'TBD')
                    
                    away_abbr = None
                    home_abbr = None
                    
                    # Methode 1: Series Standings
                    if series_df is not None and len(series_df) > 0:
                        try:
                            home_team_row = series_df[series_df['TEAM_ID'] == home_team_id]
                            visitor_team_row = series_df[series_df['TEAM_ID'] == visitor_team_id]
                            
                            if not home_team_row.empty:
                                home_abbr = home_team_row.iloc[0].get('TEAM_ABBREVIATION', '')
                            
                            if not visitor_team_row.empty:
                                away_abbr = visitor_team_row.iloc[0].get('TEAM_ABBREVIATION', '')
                        except:
                            pass
                    
                    # Methode 2: Matchup String
                    if not away_abbr or not home_abbr:
                        matchup = game.get('MATCHUP', '').strip()
                        
                        if ' @ ' in matchup:
                            parts = matchup.split(' @ ')
                            away_abbr = parts[0].strip()
                            home_abbr = parts[1].strip()
                        elif ' vs. ' in matchup:
                            parts = matchup.split(' vs. ')
                            home_abbr = parts[0].strip()
                            away_abbr = parts[1].strip()
                        elif ' vs ' in matchup:
                            parts = matchup.split(' vs ')
                            home_abbr = parts[0].strip()
                            away_abbr = parts[1].strip()
                    
                    # Wenn immer noch nicht gefunden - skip
                    if not away_abbr or not home_abbr:
                        print(f"⚠️ Kann Teams nicht finden für Game: {game_id}")
                        continue
                    
                    # Team Namen
                    team_name_map = {
                        'LAL': 'Lakers', 'GSW': 'Warriors', 'BOS': 'Celtics',
                        'MIA': 'Heat', 'PHX': 'Suns', 'LAC': 'Clippers',
                        'DEN': 'Nuggets', 'DAL': 'Mavericks', 'MIL': 'Bucks',
                        'PHI': '76ers', 'BKN': 'Nets', 'NYK': 'Knicks',
                        'TOR': 'Raptors', 'CHI': 'Bulls', 'CLE': 'Cavaliers',
                        'ATL': 'Hawks', 'CHA': 'Hornets', 'WAS': 'Wizards',
                        'ORL': 'Magic', 'IND': 'Pacers', 'DET': 'Pistons',
                        'MEM': 'Grizzlies', 'NOP': 'Pelicans', 'SAS': 'Spurs',
                        'HOU': 'Rockets', 'OKC': 'Thunder', 'UTA': 'Jazz',
                        'SAC': 'Kings', 'POR': 'Trail Blazers', 'MIN': 'Timberwolves'
                    }
                    
                    home_name = team_name_map.get(home_abbr, home_abbr)
                    away_name = team_name_map.get(away_abbr, away_abbr)
                    
                    parsed_games.append({
                        'game_id': game_id,
                        'date': tomorrow_date,
                        'time': game_time,
                        'team1_abbr': home_abbr,
                        'team2_abbr': away_abbr,
                        'team1_name': home_name,
                        'team2_name': away_name,
                        'matchup': f"{home_abbr} vs {away_abbr}",
                        'status': 'Scheduled'
                    })
                    
                except Exception as e:
                    print(f"⚠️ Fehler bei morgen Spiel: {e}")
                    continue
            
            print(f"✅ Morgen: {len(parsed_games)} Spiele")
            return parsed_games
            
        except Exception as e:
            print(f"❌ Fehler beim Laden morgiger Spiele: {e}")
            print("⚠️ Fahre nur mit heutigen Spielen fort")
            return []
    
    def get_games_with_fallback(self):
        """
        Holt Spiele mit robustem Fallback:
        1. Heute (Live API)
        2. Falls leer: Versuche morgen (mit Error Handling)
        3. Falls beide leer: Mock
        """
        all_games = []
        
        print("\n" + "="*60)
        print("🏀 LADE SPIELE")
        print("="*60)
        
        # Heute
        today_games = self.get_todays_games()
        all_games.extend(today_games)
        
        # Morgen nur wenn heute leer
        if len(today_games) == 0:
            print("⚠️ Keine Spiele heute, versuche morgen...")
            tomorrow_games = self.get_tomorrows_games_safe()
            all_games.extend(tomorrow_games)
        
        print("\n" + "="*60)
        print(f"📊 GESAMT: {len(all_games)} Spiele")
        print("="*60 + "\n")
        
        # Mock nur wenn GAR NICHTS
        if len(all_games) == 0:
            print("⚠️ Keine Spiele gefunden - verwende Mock-Daten")
            all_games = self._get_mock_games()
        
        return all_games
    
    def _get_mock_games(self):
        """Mock-Daten als letzter Fallback"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        return [
            {
                'game_id': 'mock_001',
                'date': today,
                'time': '7:30 PM ET',
                'team1_abbr': 'LAL',
                'team2_abbr': 'GSW',
                'team1_name': 'Lakers',
                'team2_name': 'Warriors',
                'matchup': 'LAL vs GSW',
                'status': 'Mock Game'
            },
            {
                'game_id': 'mock_002',
                'date': today,
                'time': '8:00 PM ET',
                'team1_abbr': 'BOS',
                'team2_abbr': 'MIA',
                'team1_name': 'Celtics',
                'team2_name': 'Heat',
                'matchup': 'BOS vs MIA',
                'status': 'Mock Game'
            }
        ]


if __name__ == "__main__":
    loader = NBAGamesLoader()
    games = loader.get_games_with_fallback()
    
    print("\n🏀 FINALE SPIELE:")
    print("="*60)
    
    for game in games:
        print(f"{game['date']} | {game['matchup']} - {game['time']}")
    
    print(f"\n✅ GESAMT: {len(games)} Spiele\n")

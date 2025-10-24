#!/usr/bin/env python3
"""
NBA Games Loader - FIXED VERSION
Nutzt Game Header für morgige Spiele (Line Score ist leer für zukünftige Spiele)
"""

from nba_api.live.nba.endpoints import scoreboard
from nba_api.stats.endpoints import ScoreboardV2
from datetime import datetime, timedelta
import time

class NBAGamesLoader:
    """Lädt heutige UND morgige NBA Spiele"""
    
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
                    print(f"⚠️ Fehler beim Parsen: {e}")
                    continue
            
            print(f"✅ Heute: {len(parsed_games)} Spiele")
            return parsed_games
            
        except Exception as e:
            print(f"❌ Fehler heute: {e}")
            return []
    
    def get_tomorrows_games(self):
        """
        Holt morgige NBA Spiele
        WICHTIG: Nutzt Game Header, nicht Line Score!
        """
        try:
            print("📡 Lade morgige NBA Spiele...")
            
            tomorrow = (datetime.now() + timedelta(days=1)).strftime('%m/%d/%Y')
            tomorrow_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
            
            board = ScoreboardV2(game_date=tomorrow)
            time.sleep(1)
            
            games_df = board.game_header.get_data_frame()
            
            if len(games_df) == 0:
                print("⚠️ Keine Spiele morgen")
                return []
            
            # WICHTIG: Hole auch SeriesStandings für Team-Kürzel!
            try:
                series_df = board.series_standings.get_data_frame()
            except:
                series_df = None
            
            parsed_games = []
            
            for _, game in games_df.iterrows():
                try:
                    game_id = game['GAME_ID']
                    home_team_id = game['HOME_TEAM_ID']
                    visitor_team_id = game['VISITOR_TEAM_ID']
                    game_time = game.get('GAME_STATUS_TEXT', 'TBD')
                    
                    # Methode 1: Aus SeriesStandings holen
                    away_abbr = None
                    home_abbr = None
                    
                    if series_df is not None and len(series_df) > 0:
                        # Finde Teams by ID
                        home_team_row = series_df[series_df['TEAM_ID'] == home_team_id]
                        visitor_team_row = series_df[series_df['TEAM_ID'] == visitor_team_id]
                        
                        if not home_team_row.empty:
                            home_abbr = home_team_row.iloc[0].get('TEAM_ABBREVIATION', '')
                        
                        if not visitor_team_row.empty:
                            away_abbr = visitor_team_row.iloc[0].get('TEAM_ABBREVIATION', '')
                    
                    # Methode 2: Fallback zu Matchup String
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
                    
                    # Wenn immer noch nicht gefunden
                    if not away_abbr or not home_abbr:
                        print(f"⚠️ Kann Teams nicht finden für Game ID: {game_id}")
                        continue
                    
                    # Team Namen approximieren (besser als nichts)
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
                    print(f"⚠️ Fehler Spiel: {e}")
                    continue
            
            print(f"✅ Morgen: {len(parsed_games)} Spiele")
            return parsed_games
            
        except Exception as e:
            print(f"❌ Fehler morgen: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_games_with_fallback(self):
        """Holt IMMER heute + morgen"""
        all_games = []
        
        print("\n" + "="*60)
        print("🏀 LADE SPIELE (HEUTE + MORGEN)")
        print("="*60)
        
        today_games = self.get_todays_games()
        all_games.extend(today_games)
        
        tomorrow_games = self.get_tomorrows_games()
        all_games.extend(tomorrow_games)
        
        print("\n" + "="*60)
        print(f"📊 GESAMT: {len(all_games)} Spiele")
        print(f"   Heute: {len(today_games)}")
        print(f"   Morgen: {len(tomorrow_games)}")
        print("="*60 + "\n")
        
        if len(all_games) == 0:
            print("⚠️ Keine Spiele - verwende Mock-Daten")
            all_games = self._get_mock_games()
        
        return all_games
    
    def _get_mock_games(self):
        """Mock-Daten"""
        today = datetime.now().strftime('%Y-%m-%d')
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        
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
                'status': 'Mock (Today)'
            },
            {
                'game_id': 'mock_002',
                'date': tomorrow,
                'time': '8:00 PM ET',
                'team1_abbr': 'BOS',
                'team2_abbr': 'MIA',
                'team1_name': 'Celtics',
                'team2_name': 'Heat',
                'matchup': 'BOS vs MIA',
                'status': 'Mock (Tomorrow)'
            }
        ]


if __name__ == "__main__":
    loader = NBAGamesLoader()
    games = loader.get_games_with_fallback()
    
    print("\n🏀 FINALE SPIELE:")
    print("="*60)
    
    today = datetime.now().strftime('%Y-%m-%d')
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    
    today_games = [g for g in games if g['date'] == today]
    tomorrow_games = [g for g in games if g['date'] == tomorrow]
    
    if today_games:
        print(f"\n📅 HEUTE ({today}):")
        for game in today_games:
            print(f"   {game['matchup']} - {game['time']}")
    
    if tomorrow_games:
        print(f"\n📅 MORGEN ({tomorrow}):")
        for game in tomorrow_games:
            print(f"   {game['matchup']} - {game['time']}")
    
    print(f"\n✅ GESAMT: {len(games)} Spiele\n")

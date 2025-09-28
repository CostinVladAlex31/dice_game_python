import tkinter as tk
from tkinter import ttk, messagebox
import random
import sqlite3
import json
from datetime import datetime, timedelta
import threading
import time

class GameDatabase:
    def __init__(self, db_path="dice_game.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS game_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player1_score INTEGER,
                player2_score INTEGER,
                winner INTEGER,
                total_rounds INTEGER,
                game_duration REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                game_mode TEXT DEFAULT 'standard'
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS player_moves (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id INTEGER,
                player INTEGER,
                action TEXT,
                dice_result INTEGER,
                score_before INTEGER,
                score_after INTEGER,
                decision_time REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (game_id) REFERENCES game_history (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS player_stats (
                player INTEGER PRIMARY KEY,
                total_games INTEGER DEFAULT 0,
                wins INTEGER DEFAULT 0,
                total_score INTEGER DEFAULT 0,
                avg_decision_time REAL DEFAULT 0,
                risk_factor REAL DEFAULT 0,
                last_played DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_game(self, player1_score, player2_score, winner, total_rounds, game_duration):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO game_history 
            (player1_score, player2_score, winner, total_rounds, game_duration)
            VALUES (?, ?, ?, ?, ?)
        ''', (player1_score, player2_score, winner, total_rounds, game_duration))
        
        game_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return game_id
    
    def save_move(self, game_id, player, action, dice_result, score_before, score_after, decision_time):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO player_moves 
            (game_id, player, action, dice_result, score_before, score_after, decision_time)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (game_id, player, action, dice_result, score_before, score_after, decision_time))
        
        conn.commit()
        conn.close()
    
    def get_game_history(self, limit=10):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM game_history 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (limit,))
        
        games = cursor.fetchall()
        conn.close()
        return games
    
    def get_player_stats(self, player):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) as total_games,
                   SUM(CASE WHEN winner = ? THEN 1 ELSE 0 END) as wins,
                   AVG(CASE WHEN winner = ? THEN 
                       CASE WHEN ? = 1 THEN player1_score ELSE player2_score END 
                       ELSE 0 END) as avg_score,
                   AVG(game_duration) as avg_game_duration
            FROM game_history
            WHERE player1_score > 0 OR player2_score > 0
        ''', (player, player, player))
        
        stats = cursor.fetchone()
        conn.close()
        return stats

class ResponsiveDesign:
    def __init__(self, root):
        self.root = root
        self.min_width = 800
        self.min_height = 600
        self.scale_factor = 1.0
        
        self.root.minsize(self.min_width, self.min_height)
        self.root.bind('<Configure>', self.on_window_resize)
        
        self.font_sizes = {
            'title': 24,
            'subtitle': 16,
            'normal': 12,
            'small': 10
        }
        
    def on_window_resize(self, event):
        if event.widget == self.root:
            width = self.root.winfo_width()
            height = self.root.winfo_height()
            
            width_scale = width / self.min_width
            height_scale = height / self.min_height
            self.scale_factor = min(width_scale, height_scale)
            
            self.update_fonts()
    
    def get_scaled_font(self, font_type):
        base_size = self.font_sizes.get(font_type, 12)
        scaled_size = max(8, int(base_size * self.scale_factor))
        return ('Arial', scaled_size)
    
    def get_scaled_font_bold(self, font_type):
        base_size = self.font_sizes.get(font_type, 12)
        scaled_size = max(8, int(base_size * self.scale_factor))
        return ('Arial', scaled_size, 'bold')
    
    def update_fonts(self):
        pass

class PerformanceMetrics:
    def __init__(self):
        self.decision_times = []
        self.game_start_time = None
        self.last_action_time = None
        self.total_rolls = 0
        self.successful_rolls = 0
        self.risk_actions = 0
        self.safe_actions = 0
    
    def start_game(self):
        self.game_start_time = time.time()
        self.last_action_time = time.time()
        self.decision_times.clear()
        self.total_rolls = 0
        self.successful_rolls = 0
        self.risk_actions = 0
        self.safe_actions = 0
    
    def record_decision(self, action_type, was_risky=False):
        current_time = time.time()
        if self.last_action_time:
            decision_time = current_time - self.last_action_time
            self.decision_times.append(decision_time)
        
        if action_type == "roll":
            self.total_rolls += 1
            if was_risky:
                self.risk_actions += 1
            else:
                self.safe_actions += 1
        
        self.last_action_time = current_time
    
    def record_successful_roll(self):
        self.successful_rolls += 1
    
    def get_metrics(self):
        game_duration = time.time() - self.game_start_time if self.game_start_time else 0
        avg_decision_time = sum(self.decision_times) / len(self.decision_times) if self.decision_times else 0
        success_rate = (self.successful_rolls / self.total_rolls * 100) if self.total_rolls > 0 else 0
        risk_ratio = (self.risk_actions / (self.risk_actions + self.safe_actions) * 100) if (self.risk_actions + self.safe_actions) > 0 else 0
        
        return {
            'game_duration': game_duration,
            'avg_decision_time': avg_decision_time,
            'success_rate': success_rate,
            'risk_ratio': risk_ratio,
            'total_rolls': self.total_rolls,
            'total_decisions': len(self.decision_times)
        }

class Dice:
    def __init__(self, fete=6, numar_zaruri=1):
        if fete < 2:
            self.fete = 6
        else:
            self.fete = fete
            
        if numar_zaruri < 1:
            self.numar_zaruri = 1
        else:
            self.numar_zaruri = numar_zaruri
    
    def roll(self):
        if self.numar_zaruri == 1:
            result = random.randint(1, self.fete)
            return result
        else:
            results = []
            for i in range(self.numar_zaruri):
                results.append(random.randint(1, self.fete))
            return results

class DiceGameGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Lucky Dice Game - Advanced Edition")
        self.root.geometry("900x700")
        self.root.configure(bg='#2c3e50')
        
        self.responsive = ResponsiveDesign(root)
        self.database = GameDatabase()
        self.metrics = PerformanceMetrics()
        
        self.dice = Dice()
        self.player_score1 = 0
        self.player_score2 = 0
        self.current_player = 1
        self.target_score = 21
        self.game_over = False
        self.current_game_id = None
        self.round_count = 0
        
        self.create_menu()
        self.setup_styles()
        self.create_widgets()
        self.update_display()
        
    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        game_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Joc", menu=game_menu)
        game_menu.add_command(label="Joc Nou", command=self.new_game)
        game_menu.add_command(label="Setari", command=self.show_settings)
        game_menu.add_separator()
        game_menu.add_command(label="Iesire", command=self.root.quit)
        
        history_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Istoric", menu=history_menu)
        history_menu.add_command(label="Istoricul Jocurilor", command=self.show_game_history)
        history_menu.add_command(label="Statistici Performance", command=self.show_performance_stats)
        
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ajutor", menu=help_menu)
        help_menu.add_command(label="Reguli", command=self.show_rules)
        help_menu.add_command(label="Despre", command=self.show_about)
    
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
    
    def create_widgets(self):
        self.main_frame = tk.Frame(self.root, bg='#2c3e50')
        self.main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.create_header()
        self.create_game_area()
        self.create_controls()
        self.create_status_bar()
        
        self.responsive.update_fonts = self.update_responsive_fonts
    
    def create_header(self):
        header_frame = tk.Frame(self.main_frame, bg='#2c3e50')
        header_frame.pack(fill='x', pady=(0, 10))
        
        self.title_label = tk.Label(header_frame, text="LUCKY DICE GAME", 
                                   font=self.responsive.get_scaled_font_bold('title'),
                                   fg='#ecf0f1', bg='#2c3e50')
        self.title_label.pack()
        
        self.subtitle_label = tk.Label(header_frame, text="Advanced Edition with Analytics", 
                                      font=self.responsive.get_scaled_font('normal'),
                                      fg='#95a5a6', bg='#2c3e50')
        self.subtitle_label.pack()
    
    def create_game_area(self):
        game_frame = tk.Frame(self.main_frame, bg='#2c3e50')
        game_frame.pack(fill='both', expand=True)
        
        self.create_players_area(game_frame)
        self.create_dice_area(game_frame)
        self.create_metrics_area(game_frame)
    
    def create_players_area(self, parent):
        players_frame = tk.Frame(parent, bg='#2c3e50')
        players_frame.pack(fill='x', pady=10)
        
        self.player1_frame = tk.Frame(players_frame, bg='#27ae60', relief='raised', bd=3)
        self.player1_frame.pack(side='left', fill='x', expand=True, padx=(0, 5))
        
        self.player1_title = tk.Label(self.player1_frame, text="JUCATOR 1", 
                                     font=self.responsive.get_scaled_font_bold('subtitle'),
                                     fg='white', bg='#27ae60')
        self.player1_title.pack(pady=5)
        
        self.player1_score_label = tk.Label(self.player1_frame, text="Scor: 0", 
                                           font=self.responsive.get_scaled_font('normal'),
                                           fg='white', bg='#27ae60')
        self.player1_score_label.pack(pady=2)
        
        self.player2_frame = tk.Frame(players_frame, bg='#3498db', relief='raised', bd=3)
        self.player2_frame.pack(side='right', fill='x', expand=True, padx=(5, 0))
        
        self.player2_title = tk.Label(self.player2_frame, text="JUCATOR 2", 
                                     font=self.responsive.get_scaled_font_bold('subtitle'),
                                     fg='white', bg='#3498db')
        self.player2_title.pack(pady=5)
        
        self.player2_score_label = tk.Label(self.player2_frame, text="Scor: 0", 
                                           font=self.responsive.get_scaled_font('normal'),
                                           fg='white', bg='#3498db')
        self.player2_score_label.pack(pady=2)
    
    def create_dice_area(self, parent):
        dice_frame = tk.Frame(parent, bg='#2c3e50')
        dice_frame.pack(pady=20)
        
        self.current_player_label = tk.Label(dice_frame, text="Randul Jucatorului 1", 
                                           font=self.responsive.get_scaled_font_bold('subtitle'),
                                           fg='#ecf0f1', bg='#2c3e50')
        self.current_player_label.pack(pady=10)
        
        self.dice_display = tk.Label(dice_frame, text="🎲", 
                                   font=('Arial', 48), 
                                   fg='#ecf0f1', bg='#2c3e50')
        self.dice_display.pack()
        
        self.result_label = tk.Label(dice_frame, text="", 
                                   font=self.responsive.get_scaled_font('normal'),
                                   fg='#f39c12', bg='#2c3e50')
        self.result_label.pack(pady=10)
    
    def create_metrics_area(self, parent):
        metrics_frame = tk.Frame(parent, bg='#34495e', relief='raised', bd=2)
        metrics_frame.pack(fill='x', pady=10)
        
        metrics_title = tk.Label(metrics_frame, text="PERFORMANCE LIVE", 
                               font=self.responsive.get_scaled_font_bold('normal'),
                               fg='#e74c3c', bg='#34495e')
        metrics_title.pack(pady=5)
        
        self.metrics_content = tk.Frame(metrics_frame, bg='#34495e')
        self.metrics_content.pack(fill='x', padx=10, pady=5)
        
        self.rounds_label = tk.Label(self.metrics_content, text="Runde: 0", 
                                   font=self.responsive.get_scaled_font('small'),
                                   fg='#ecf0f1', bg='#34495e')
        self.rounds_label.pack(side='left', padx=10)
        
        self.decision_label = tk.Label(self.metrics_content, text="Timp decizie: 0.0s", 
                                     font=self.responsive.get_scaled_font('small'),
                                     fg='#ecf0f1', bg='#34495e')
        self.decision_label.pack(side='left', padx=10)
        
        self.success_label = tk.Label(self.metrics_content, text="Succes: 0%", 
                                    font=self.responsive.get_scaled_font('small'),
                                    fg='#ecf0f1', bg='#34495e')
        self.success_label.pack(side='left', padx=10)
    
    def create_controls(self):
        controls_frame = tk.Frame(self.main_frame, bg='#2c3e50')
        controls_frame.pack(pady=20)
        
        self.roll_button = tk.Button(controls_frame, text="ARUNCA ZARUL", 
                                   command=self.roll_dice,
                                   font=self.responsive.get_scaled_font_bold('normal'),
                                   bg='#e74c3c', fg='white',
                                   relief='raised', bd=3,
                                   padx=20, pady=10)
        self.roll_button.pack(side='left', padx=10)
        
        self.pass_button = tk.Button(controls_frame, text="PASEAZA RANDUL", 
                                   command=self.pass_turn,
                                   font=self.responsive.get_scaled_font_bold('normal'),
                                   bg='#f39c12', fg='white',
                                   relief='raised', bd=3,
                                   padx=20, pady=10)
        self.pass_button.pack(side='left', padx=10)
        
        self.new_game_button = tk.Button(controls_frame, text="JOC NOU", 
                                       command=self.new_game,
                                       font=self.responsive.get_scaled_font_bold('normal'),
                                       bg='#95a5a6', fg='white',
                                       relief='raised', bd=2,
                                       padx=15, pady=8)
        self.new_game_button.pack(side='left', padx=10)
    
    def create_status_bar(self):
        self.status_frame = tk.Frame(self.main_frame, bg='#34495e', relief='sunken', bd=1)
        self.status_frame.pack(fill='x', side='bottom')
        
        self.status_label = tk.Label(self.status_frame, text="Gata pentru joc", 
                                   font=self.responsive.get_scaled_font('small'),
                                   fg='#ecf0f1', bg='#34495e')
        self.status_label.pack(side='left', padx=5, pady=2)
        
        self.game_time_label = tk.Label(self.status_frame, text="Timp: 0:00", 
                                      font=self.responsive.get_scaled_font('small'),
                                      fg='#ecf0f1', bg='#34495e')
        self.game_time_label.pack(side='right', padx=5, pady=2)
    
    def update_responsive_fonts(self):
        widgets_to_update = [
            (self.title_label, 'title', True),
            (self.subtitle_label, 'normal', False),
            (self.player1_title, 'subtitle', True),
            (self.player1_score_label, 'normal', False),
            (self.player2_title, 'subtitle', True),
            (self.player2_score_label, 'normal', False),
            (self.current_player_label, 'subtitle', True),
            (self.result_label, 'normal', False),
            (self.rounds_label, 'small', False),
            (self.decision_label, 'small', False),
            (self.success_label, 'small', False),
            (self.roll_button, 'normal', True),
            (self.pass_button, 'normal', True),
            (self.new_game_button, 'normal', True),
            (self.status_label, 'small', False),
            (self.game_time_label, 'small', False)
        ]
        
        for widget, font_type, is_bold in widgets_to_update:
            if is_bold:
                widget.config(font=self.responsive.get_scaled_font_bold(font_type))
            else:
                widget.config(font=self.responsive.get_scaled_font(font_type))
    
    def roll_dice(self):
        if self.game_over:
            return
        
        if not self.metrics.game_start_time:
            self.metrics.start_game()
        
        score_before = self.get_current_score()
        is_risky = score_before > 15
        
        self.metrics.record_decision("roll", is_risky)
        self.animate_dice_roll()
        
        result = self.dice.roll()
        
        if result == 1:
            self.dice_display.config(text="💀")
            self.result_label.config(text="GHINION! Ai nimerit 1!", fg='#e74c3c')
            winner = 2 if self.current_player == 1 else 1
            
            if self.current_game_id:
                self.database.save_move(self.current_game_id, self.current_player, "roll", 1, 
                                      score_before, score_before, 0)
            
            self.end_game(f"Jucatorul {winner} castiga!\nJucatorul {self.current_player} a nimerit 1!")
            return
        
        self.dice_display.config(text=self.get_dice_emoji(result))
        self.result_label.config(text=f"Ai aruncat: {result}", fg='#2ecc71')
        self.metrics.record_successful_roll()
        
        if isinstance(result, list):
            points = sum(result)
        else:
            points = result
            
        self.add_points(points)
        score_after = self.get_current_score()
        
        if self.current_game_id:
            decision_time = self.metrics.decision_times[-1] if self.metrics.decision_times else 0
            self.database.save_move(self.current_game_id, self.current_player, "roll", result,
                                  score_before, score_after, decision_time)
        
        if score_after > self.target_score:
            winner = 2 if self.current_player == 1 else 1
            self.end_game(f"Jucatorul {winner} castiga!\nJucatorul {self.current_player} a depasit {self.target_score}!")
            return
            
        if score_after == self.target_score:
            self.end_game(f"Jucatorul {self.current_player} castiga!\nScor perfect: {self.target_score}!")
            return
        
        self.round_count += 1
        self.switch_player()
        self.update_display()
        self.update_live_metrics()
    
    def pass_turn(self):
        if self.game_over:
            return
        
        if not self.metrics.game_start_time:
            self.metrics.start_game()
        
        score_before = self.get_current_score()
        self.metrics.record_decision("pass", False)
        
        self.result_label.config(text=f"Jucatorul {self.current_player} a pasat randul", fg='#f39c12')
        
        if self.current_game_id:
            decision_time = self.metrics.decision_times[-1] if self.metrics.decision_times else 0
            self.database.save_move(self.current_game_id, self.current_player, "pass", 0,
                                  score_before, score_before, decision_time)
        
        if self.player_score1 > 0 and self.player_score2 > 0:
            if self.player_score1 > self.player_score2:
                self.end_game(f"Jucatorul 1 castiga cu scorul {self.player_score1}!")
            elif self.player_score2 > self.player_score1:
                self.end_game(f"Jucatorul 2 castiga cu scorul {self.player_score2}!")
            else:
                self.end_game("Egalitate!")
            return
        
        self.round_count += 1
        self.switch_player()
        self.update_display()
        self.update_live_metrics()
    
    def update_live_metrics(self):
        metrics = self.metrics.get_metrics()
        
        self.rounds_label.config(text=f"Runde: {self.round_count}")
        self.decision_label.config(text=f"Timp decizie: {metrics['avg_decision_time']:.1f}s")
        self.success_label.config(text=f"Succes: {metrics['success_rate']:.1f}%")
        
        minutes = int(metrics['game_duration'] // 60)
        seconds = int(metrics['game_duration'] % 60)
        self.game_time_label.config(text=f"Timp: {minutes}:{seconds:02d}")
    
    def get_dice_emoji(self, value):
        dice_emojis = {1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"}
        return dice_emojis.get(value, "🎲")
    
    def animate_dice_roll(self):
        for i in range(8):
            self.dice_display.config(text="🎲" if i % 2 == 0 else "🎯")
            self.root.update()
            time.sleep(0.08)
    
    def switch_player(self):
        self.current_player = 2 if self.current_player == 1 else 1
    
    def get_current_score(self):
        return self.player_score1 if self.current_player == 1 else self.player_score2
    
    def add_points(self, points):
        if self.current_player == 1:
            self.player_score1 += points
        else:
            self.player_score2 += points
    
    def update_display(self):
        self.player1_score_label.config(text=f"Scor: {self.player_score1}")
        self.player2_score_label.config(text=f"Scor: {self.player_score2}")
        
        if self.current_player == 1:
            self.current_player_label.config(text="Randul Jucatorului 1", fg='#27ae60')
            self.player1_frame.config(bg='#e74c3c')
            self.player1_title.config(bg='#e74c3c')
            self.player1_score_label.config(bg='#e74c3c')
            self.player2_frame.config(bg='#3498db')
            self.player2_title.config(bg='#3498db')
            self.player2_score_label.config(bg='#3498db')
        else:
            self.current_player_label.config(text="Randul Jucatorului 2", fg='#3498db')
            self.player1_frame.config(bg='#27ae60')
            self.player1_title.config(bg='#27ae60')
            self.player1_score_label.config(bg='#27ae60')
            self.player2_frame.config(bg='#e74c3c')
            self.player2_title.config(bg='#e74c3c')
            self.player2_score_label.config(bg='#e74c3c')
        
        self.status_label.config(text=f"Jucatorul {self.current_player} - Aleg actiunea...")
    
    def end_game(self, message):
        self.game_over = True
        metrics = self.metrics.get_metrics()
        
        winner = 1 if "Jucatorul 1 castiga" in message else 2
        if "Egalitate" in message:
            winner = 0
        
        self.current_game_id = self.database.save_game(
            self.player_score1, self.player_score2, winner, 
            self.round_count, metrics['game_duration']
        )
        
        self.dice_display.config(text="🏆")
        self.result_label.config(text="JOC TERMINAT!", fg='#f1c40f')
        self.status_label.config(text="Joc terminat")
        
        messagebox.showinfo("Joc Terminat", message)
        
        self.roll_button.config(state='disabled')
        self.pass_button.config(state='disabled')
    
    def new_game(self):
        self.player_score1 = 0
        self.player_score2 = 0
        self.current_player = 1
        self.game_over = False
        self.current_game_id = None
        self.round_count = 0
        
        self.metrics = PerformanceMetrics()
        
        self.dice_display.config(text="🎲")
        self.result_label.config(text="")
        self.status_label.config(text="Joc nou inceput")
        
        self.rounds_label.config(text="Runde: 0")
        self.decision_label.config(text="Timp decizie: 0.0s")
        self.success_label.config(text="Succes: 0%")
        self.game_time_label.config(text="Timp: 0:00")
        
        self.roll_button.config(state='normal')
        self.pass_button.config(state='normal')
        
        self.update_display()
    
    def show_settings(self):
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Setari Joc")
        settings_window.geometry("400x300")
        settings_window.configure(bg='#2c3e50')
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        title_label = tk.Label(settings_window, text="SETARI JOC", 
                               font=self.responsive.get_scaled_font_bold('subtitle'),
                               fg='#ecf0f1', bg='#2c3e50')
        title_label.pack(pady=20)
        
        target_frame = tk.Frame(settings_window, bg='#2c3e50')
        target_frame.pack(pady=10)
        
        tk.Label(target_frame, text="Scor tinta:", 
                 font=self.responsive.get_scaled_font('normal'),
                 fg='#ecf0f1', bg='#2c3e50').pack(side='left')
        
        self.target_var = tk.StringVar(value=str(self.target_score))
        target_entry = tk.Entry(target_frame, textvariable=self.target_var, width=10)
        target_entry.pack(side='left', padx=10)
        
        dice_frame = tk.Frame(settings_window, bg='#2c3e50')
        dice_frame.pack(pady=10)
        
        tk.Label(dice_frame, text="Fete zar:", 
                 font=self.responsive.get_scaled_font('normal'),
                 fg='#ecf0f1', bg='#2c3e50').pack(side='left')
        
        self.dice_faces_var = tk.StringVar(value=str(self.dice.fete))
        dice_entry = tk.Entry(dice_frame, textvariable=self.dice_faces_var, width=10)
        dice_entry.pack(side='left', padx=10)
        
        buttons_frame = tk.Frame(settings_window, bg='#2c3e50')
        buttons_frame.pack(pady=30)
        
        save_button = tk.Button(buttons_frame, text="SALVEAZA", 
                              command=lambda: self.save_settings(settings_window),
                              font=self.responsive.get_scaled_font_bold('normal'),
                              bg='#27ae60', fg='white',
                              padx=20, pady=5)
        save_button.pack(side='left', padx=10)
        
        cancel_button = tk.Button(buttons_frame, text="ANULEAZA", 
                                command=settings_window.destroy,
                                font=self.responsive.get_scaled_font_bold('normal'),
                                bg='#e74c3c', fg='white',
                                padx=20, pady=5)
        cancel_button.pack(side='left', padx=10)
    
    def save_settings(self, window):
        try:
            new_target = int(self.target_var.get())
            new_faces = int(self.dice_faces_var.get())
            
            if new_target < 1:
                messagebox.showerror("Eroare", "Scorul tinta trebuie sa fie pozitiv!")
                return
                
            if new_faces < 2:
                messagebox.showerror("Eroare", "Zarul trebuie sa aiba cel putin 2 fete!")
                return
            
            self.target_score = new_target
            self.dice = Dice(fete=new_faces)
            
            window.destroy()
            messagebox.showinfo("Success", "Setarile au fost salvate!")
            
        except ValueError:
            messagebox.showerror("Eroare", "Introduceti valori numerice valide!")
    
    def show_game_history(self):
        history_window = tk.Toplevel(self.root)
        history_window.title("Istoricul Jocurilor")
        history_window.geometry("700x500")
        history_window.configure(bg='#2c3e50')
        history_window.transient(self.root)
        
        title_label = tk.Label(history_window, text="ISTORICUL JOCURILOR", 
                               font=self.responsive.get_scaled_font_bold('subtitle'),
                               fg='#ecf0f1', bg='#2c3e50')
        title_label.pack(pady=10)
        
        frame = tk.Frame(history_window, bg='#2c3e50')
        frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        columns = ('ID', 'Data', 'Scor P1', 'Scor P2', 'Castigator', 'Runde', 'Durata')
        tree = ttk.Treeview(frame, columns=columns, show='headings', height=15)
        
        tree.heading('ID', text='ID')
        tree.heading('Data', text='Data')
        tree.heading('Scor P1', text='Scor P1')
        tree.heading('Scor P2', text='Scor P2')
        tree.heading('Castigator', text='Castigator')
        tree.heading('Runde', text='Runde')
        tree.heading('Durata', text='Durata (s)')
        
        tree.column('ID', width=50)
        tree.column('Data', width=120)
        tree.column('Scor P1', width=70)
        tree.column('Scor P2', width=70)
        tree.column('Castigator', width=80)
        tree.column('Runde', width=60)
        tree.column('Durata', width=80)
        
        scrollbar = ttk.Scrollbar(frame, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        games = self.database.get_game_history(50)
        for game in games:
            game_id, p1_score, p2_score, winner, rounds, duration, timestamp, mode = game
            
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                date_str = dt.strftime('%Y-%m-%d %H:%M')
            except:
                date_str = timestamp[:16] if len(timestamp) > 16 else timestamp
            
            winner_text = f"Jucator {winner}" if winner > 0 else "Egalitate"
            duration_text = f"{duration:.1f}" if duration else "N/A"
            
            tree.insert('', 'end', values=(
                game_id, date_str, p1_score, p2_score, 
                winner_text, rounds, duration_text
            ))
        
        tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        close_button = tk.Button(history_window, text="INCHIDE", 
                               command=history_window.destroy,
                               font=self.responsive.get_scaled_font_bold('normal'),
                               bg='#95a5a6', fg='white',
                               padx=20, pady=5)
        close_button.pack(pady=10)
    
    def show_performance_stats(self):
        stats_window = tk.Toplevel(self.root)
        stats_window.title("Statistici Performance")
        stats_window.geometry("600x400")
        stats_window.configure(bg='#2c3e50')
        stats_window.transient(self.root)
        
        title_label = tk.Label(stats_window, text="STATISTICI PERFORMANCE", 
                               font=self.responsive.get_scaled_font_bold('subtitle'),
                               fg='#ecf0f1', bg='#2c3e50')
        title_label.pack(pady=10)
        
        main_frame = tk.Frame(stats_window, bg='#2c3e50')
        main_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        current_game_frame = tk.LabelFrame(main_frame, text="Jocul Curent", 
                                         bg='#34495e', fg='#ecf0f1',
                                         font=self.responsive.get_scaled_font_bold('normal'))
        current_game_frame.pack(fill='x', pady=(0, 10))
        
        if self.metrics.game_start_time:
            current_metrics = self.metrics.get_metrics()
            
            metrics_text = [
                f"Durata joc: {current_metrics['game_duration']:.1f} secunde",
                f"Timp mediu decizie: {current_metrics['avg_decision_time']:.2f} secunde",
                f"Rata de succes: {current_metrics['success_rate']:.1f}%",
                f"Factor de risc: {current_metrics['risk_ratio']:.1f}%",
                f"Total aruncari: {current_metrics['total_rolls']}",
                f"Total runde: {self.round_count}"
            ]
            
            for metric in metrics_text:
                label = tk.Label(current_game_frame, text=metric, 
                               font=self.responsive.get_scaled_font('normal'),
                               fg='#ecf0f1', bg='#34495e')
                label.pack(anchor='w', padx=10, pady=2)
        else:
            no_game_label = tk.Label(current_game_frame, text="Nu exista joc activ", 
                                   font=self.responsive.get_scaled_font('normal'),
                                   fg='#95a5a6', bg='#34495e')
            no_game_label.pack(padx=10, pady=10)
        
        historical_frame = tk.LabelFrame(main_frame, text="Statistici Istorice", 
                                       bg='#34495e', fg='#ecf0f1',
                                       font=self.responsive.get_scaled_font_bold('normal'))
        historical_frame.pack(fill='both', expand=True)
        
        player1_stats = self.database.get_player_stats(1)
        player2_stats = self.database.get_player_stats(2)
        
        stats_frame = tk.Frame(historical_frame, bg='#34495e')
        stats_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        left_frame = tk.Frame(stats_frame, bg='#34495e')
        left_frame.pack(side='left', fill='both', expand=True)
        
        tk.Label(left_frame, text="JUCATOR 1", 
                font=self.responsive.get_scaled_font_bold('normal'),
                fg='#27ae60', bg='#34495e').pack()
        
        if player1_stats and player1_stats[0] > 0:
            total_games, wins, avg_score, avg_duration = player1_stats
            win_rate = (wins / total_games * 100) if total_games > 0 else 0
            
            p1_stats_text = [
                f"Jocuri totale: {total_games}",
                f"Victorii: {wins}",
                f"Rata victorii: {win_rate:.1f}%",
                f"Scor mediu: {avg_score:.1f}" if avg_score else "Scor mediu: N/A",
                f"Durata medie: {avg_duration:.1f}s" if avg_duration else "Durata medie: N/A"
            ]
            
            for stat in p1_stats_text:
                tk.Label(left_frame, text=stat, 
                        font=self.responsive.get_scaled_font('small'),
                        fg='#ecf0f1', bg='#34495e').pack(anchor='w')
        else:
            tk.Label(left_frame, text="Nu exista date", 
                    font=self.responsive.get_scaled_font('small'),
                    fg='#95a5a6', bg='#34495e').pack()
        
        right_frame = tk.Frame(stats_frame, bg='#34495e')
        right_frame.pack(side='right', fill='both', expand=True)
        
        tk.Label(right_frame, text="JUCATOR 2", 
                font=self.responsive.get_scaled_font_bold('normal'),
                fg='#3498db', bg='#34495e').pack()
        
        if player2_stats and player2_stats[0] > 0:
            total_games, wins, avg_score, avg_duration = player2_stats
            win_rate = (wins / total_games * 100) if total_games > 0 else 0
            
            p2_stats_text = [
                f"Jocuri totale: {total_games}",
                f"Victorii: {wins}",
                f"Rata victorii: {win_rate:.1f}%",
                f"Scor mediu: {avg_score:.1f}" if avg_score else "Scor mediu: N/A",
                f"Durata medie: {avg_duration:.1f}s" if avg_duration else "Durata medie: N/A"
            ]
            
            for stat in p2_stats_text:
                tk.Label(right_frame, text=stat, 
                        font=self.responsive.get_scaled_font('small'),
                        fg='#ecf0f1', bg='#34495e').pack(anchor='w')
        else:
            tk.Label(right_frame, text="Nu exista date", 
                    font=self.responsive.get_scaled_font('small'),
                    fg='#95a5a6', bg='#34495e').pack()
        
        close_button = tk.Button(stats_window, text="INCHIDE", 
                               command=stats_window.destroy,
                               font=self.responsive.get_scaled_font_bold('normal'),
                               bg='#95a5a6', fg='white',
                               padx=20, pady=5)
        close_button.pack(pady=10)
    
    def show_rules(self):
        rules_window = tk.Toplevel(self.root)
        rules_window.title("Reguli Joc")
        rules_window.geometry("500x400")
        rules_window.configure(bg='#2c3e50')
        rules_window.transient(self.root)
        
        title_label = tk.Label(rules_window, text="REGULI LUCKY DICE", 
                               font=self.responsive.get_scaled_font_bold('subtitle'),
                               fg='#ecf0f1', bg='#2c3e50')
        title_label.pack(pady=10)
        
        rules_text = """
OBIECTIV:
Primul jucator care ajunge exact la 21 puncte castiga jocul.

REGULI:
1. Jucatorii se alterneaza la aruncarea zarului
2. Punctele se aduna la scorul total
3. Daca depasesti 21 puncte, pierzi automat
4. Daca nimeresti 1, pierzi automat
5. Poti alege sa pasezi randul pentru a evita riscul
6. Daca ambii jucatori paseaza, castiga cel cu scorul mai mare

STRATEGII:
- Cu scor mic (0-10): arunca agresiv
- Cu scor mediu (11-16): echilibreaza riscul
- Cu scor mare (17-20): considera pasarea randul

PERFORMANCE:
- Timpul de decizie este masurat
- Rata de succes este calculata
- Factorul de risc este monitorizat
        
        text_frame = tk.Frame(rules_window, bg='#2c3e50')
        text_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        text_widget = tk.Text(text_frame, wrap='word', bg='#34495e', fg='#ecf0f1',
                             font=self.responsive.get_scaled_font('small'),
                             relief='flat', bd=0)
        text_widget.pack(fill='both', expand=True)
        text_widget.insert('1.0', rules_text)
        text_widget.config(state='disabled')
        
        close_button = tk.Button(rules_window, text="INCHIDE", 
                               command=rules_window.destroy,
                               font=self.responsive.get_scaled_font_bold('normal'),
                               bg='#95a5a6', fg='white',
                               padx=20, pady=5)
        close_button.pack(pady=10)
    
    def show_about(self):
        about_window = tk.Toplevel(self.root)
        about_window.title("Despre")
        about_window.geometry("400x300")
        about_window.configure(bg='#2c3e50')
        about_window.transient(self.root)
        
        title_label = tk.Label(about_window, text="LUCKY DICE GAME", 
                               font=self.responsive.get_scaled_font_bold('subtitle'),
                               fg='#ecf0f1', bg='#2c3e50')
        title_label.pack(pady=20)
        
        
        info_label = tk.Label(about_window, text=info_text, 
                             font=self.responsive.get_scaled_font('small'),
                             fg='#ecf0f1', bg='#2c3e50', justify='center')
        info_label.pack(pady=20)
        
        close_button = tk.Button(about_window, text="INCHIDE", 
                               command=about_window.destroy,
                               font=self.responsive.get_scaled_font_bold('normal'),
                               bg='#95a5a6', fg='white',
                               padx=20, pady=5)
        close_button.pack(pady=20)

def main():
    root = tk.Tk()
    app = DiceGameGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()

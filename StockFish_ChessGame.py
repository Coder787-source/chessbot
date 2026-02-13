import pygame
import chess
import chess.engine
import chess.pgn
import sys
import time
import os
import math

# --- CONFIGURATION ---
WIDTH, HEIGHT = 1200, 800
BOARD_SIZE = 600
SQUARE_SIZE = BOARD_SIZE // 8
OFFSET_X, OFFSET_Y = 160, 100 # Adjusted slightly for the Eval Bar

# Path to the Stockfish executable
ENGINE_PATH = r"C:\Users\kesha\Downloads\stockfish-windows-x86-64-avx2\stockfish\stockfish-windows-x86-64-avx2.exe"

COLORS = {
    "select": "#f7f769", "accent": "#f1c40f", 
    "sidebar": "#262421", "btn": "#45423e", "bg": "#1e1e1e",
    "win": "#2ecc71", "loss": "#ff4757", "dot": (0, 0, 0, 80),
    "capture_dot": (231, 76, 60, 160), "text": "#ecf0f1",
    "check": "#e74c3c", "overlay": (0, 0, 0, 180),
    "hint": (52, 152, 219, 180),
    "eval_white": "#ffffff", "eval_black": "#404040",
    "brilliant": "#1baca1", "blunder": "#ff4757", "best": "#95bb4a"
}

THEMES = [
    ("#eeeed2", "#769656"), # Classic Green
    ("#dee3e6", "#8ca2ad"), # Blue Sky
    ("#ebecd0", "#ba5546")  # Wood/Red
]

SYMBOLS = {'P': '♙', 'N': '♘', 'B': '♗', 'R': '♖', 'Q': '♕', 'K': '♔',
           'p': '♟', 'n': '♞', 'b': '♝', 'r': '♜', 'q': '♛', 'k': '♚'}

class ChessTitan:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("OmniChess")
        self.clock = pygame.time.Clock()
        self.engine = None
        
        print("\n" + "="*40)
        print("OmniChess:Entertainment Studios")
        print("="*40)
        try:
            self.engine = chess.engine.SimpleEngine.popen_uci(ENGINE_PATH)
            identity = self.engine.id
            print(f"ENGINE: {identity.get('name', 'Stockfish')}")
            print(f"AUTHOR: {identity.get('author', 'Unknown')}")
            print("STATUS: CORE CONNECTED & OPERATIONAL")
        except Exception as e:
            print(f"Errno 2: Stockfish not found at {ENGINE_PATH}")
            print(f"DETAILS: {e}")
        print("="*40 + "\n")

        self.font_piece = pygame.font.SysFont("segoeuisymbol", 72)
        self.font_captured = pygame.font.SysFont("segoeuisymbol", 30)
        self.font_ui = pygame.font.SysFont("arial", 20, bold=True)
        self.font_tiny = pygame.font.SysFont("arial", 14, bold=True)
        self.font_credit = pygame.font.SysFont("consolas", 12, bold=True)
        self.font_big = pygame.font.SysFont("arial", 45, bold=True)
        
        self.state = "MENU"
        self.mode = "PRESET" 
        self.user_color = chess.WHITE
        self.current_level = 1
        self.custom_elo = 1500 
        self.timer_setting = 600
        self.current_theme_idx = 0
        
        # New Feature State
        self.eval_score = 0.0
        self.last_move_quality = None
        self.prev_eval = 0.0
        
        self.reset_game()

    def draw_credits(self):
        credit_text = "ENGINE INTEGRATION BY STOCKFISH v18"
        cred_surf = self.font_credit.render(credit_text, True, "#555555")
        self.screen.blit(cred_surf, (WIDTH//2 - cred_surf.get_width()//2, 5))

    def reset_game(self):
        self.board = chess.Board()
        self.selected_sq = None
        self.legal_dots = []
        self.captured_by_white = []
        self.captured_by_black = []
        self.move_history = []
        self.white_time = float(self.timer_setting)
        self.black_time = float(self.timer_setting)
        self.last_update = time.time()
        self.hints_used = 0
        self.cheated = False
        self.hint_move = None
        self.pending_promotion = None
        self.eval_score = 0.0
        self.prev_eval = 0.0
        self.last_move_quality = None
        
        if self.engine:
            if self.mode == "PRESET":
                skill = min(20, (self.current_level - 1) * 2)
                self.engine.configure({"Skill Level": skill, "UCI_LimitStrength": False})
            else:
                self.engine.configure({"UCI_LimitStrength": True, "UCI_Elo": min(3190, self.custom_elo)})

    def download_pgn(self):
        game = chess.pgn.Game()
        game.headers["White"] = "Player" if self.user_color == chess.WHITE else "Stockfish"
        game.headers["Black"] = "Player" if self.user_color == chess.BLACK else "Stockfish"
        node = game
        temp_board = chess.Board()
        for move_san in self.move_history:
            move = temp_board.parse_san(move_san)
            node = node.add_main_variation(move)
            temp_board.push(move)
        filename = f"game_{int(time.time())}.pgn"
        with open(filename, "w") as f:
            f.write(str(game))
        print(f"Saved: {filename}")

    def draw_eval_bar(self):
        bar_x, bar_y, bar_w, bar_h = 100, OFFSET_Y, 35, BOARD_SIZE
        pygame.draw.rect(self.screen, COLORS["eval_black"], (bar_x, bar_y, bar_w, bar_h))
        display_eval = max(-10, min(10, self.eval_score))
        ratio = 1 / (1 + math.exp(-0.4 * display_eval))
        white_h = ratio * bar_h
        pygame.draw.rect(self.screen, COLORS["eval_white"], (bar_x, bar_y + (bar_h - white_h), bar_w, white_h))
        score_str = f"{self.eval_score:+.1f}"
        score_surf = self.font_tiny.render(score_str, True, COLORS["accent"])
        self.screen.blit(score_surf, (bar_x - 5, bar_y - 25))

    def handle_click(self, pos):
        if self.state == "MENU":
            for i in range(8):
                rect = pygame.Rect(180 + (i%2)*140, 220 + (i//2)*70, 120, 55)
                if rect.collidepoint(pos): self.current_level = i+1; self.mode = "PRESET"
            
            if pygame.Rect(800, 270, 60, 45).collidepoint(pos): self.custom_elo = max(1350, self.custom_elo - 100); self.mode = "ELO"
            if pygame.Rect(865, 270, 45, 45).collidepoint(pos): self.custom_elo = max(1350, self.custom_elo - 10); self.mode = "ELO"
            if pygame.Rect(980, 270, 45, 45).collidepoint(pos): self.custom_elo = min(3190, self.custom_elo + 10); self.mode = "ELO"
            if pygame.Rect(1030, 270, 60, 45).collidepoint(pos): self.custom_elo = min(3190, self.custom_elo + 100); self.mode = "ELO"

            if pygame.Rect(500, 460, 100, 45).collidepoint(pos): self.user_color = chess.WHITE
            if pygame.Rect(620, 460, 100, 45).collidepoint(pos): self.user_color = chess.BLACK
            if pygame.Rect(430, 580, 50, 45).collidepoint(pos): self.timer_setting = max(10, self.timer_setting - 60)
            if pygame.Rect(490, 580, 50, 45).collidepoint(pos): self.timer_setting = max(10, self.timer_setting - 10)
            if pygame.Rect(660, 580, 50, 45).collidepoint(pos): self.timer_setting += 10
            if pygame.Rect(720, 580, 50, 45).collidepoint(pos): self.timer_setting += 60
            if pygame.Rect(WIDTH//2-120, 680, 240, 70).collidepoint(pos): self.reset_game(); self.state = "PLAYING"

        elif self.state == "PROMOTING":
            for i, piece in enumerate([chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]):
                rect = pygame.Rect(WIDTH//2 - 140 + i*70, HEIGHT//2 - 35, 60, 60)
                if rect.collidepoint(pos):
                    move = chess.Move(self.pending_promotion[0], self.pending_promotion[1], promotion=piece)
                    self.execute_move(move)
                    self.state = "PLAYING"; self.pending_promotion = None

        elif self.state == "PLAYING" and not self.cheated:
            if self.board.is_game_over():
                if pygame.Rect(WIDTH//2-100, HEIGHT//2+60, 200, 50).collidepoint(pos): self.state = "MENU"
                return
            if pygame.Rect(800, 350, 350, 50).collidepoint(pos): self.state = "MENU"
            if pygame.Rect(800, 470, 350, 50).collidepoint(pos): self.download_pgn()
            if pygame.Rect(800, 410, 350, 50).collidepoint(pos) and self.board.turn == self.user_color: 
                self.hints_used += 1
                if self.hints_used > 3: self.cheated = True
                else:
                    info = self.engine.analyse(self.board, chess.engine.Limit(time=0.5))
                    if 'pv' in info: self.hint_move = info['pv'][0]

            if OFFSET_X < pos[0] < OFFSET_X + BOARD_SIZE and OFFSET_Y < pos[1] < OFFSET_Y + BOARD_SIZE:
                c, r = (pos[0]-OFFSET_X)//SQUARE_SIZE, 7-((pos[1]-OFFSET_Y)//SQUARE_SIZE)
                if self.user_color == chess.BLACK: c, r = 7-c, 7-r
                sq = chess.square(c, r)
                if self.selected_sq is None:
                    p = self.board.piece_at(sq)
                    if p and p.color == self.user_color:
                        self.selected_sq = sq
                        self.legal_dots = [m.to_square for m in self.board.legal_moves if m.from_square == sq]
                else:
                    move = chess.Move(self.selected_sq, sq)
                    piece = self.board.piece_at(self.selected_sq)
                    if piece and piece.piece_type == chess.PAWN and chess.square_rank(sq) in [0, 7]:
                        if move in [chess.Move(m.from_square, m.to_square) for m in self.board.legal_moves]:
                            self.pending_promotion = (self.selected_sq, sq)
                            self.state = "PROMOTING"
                    elif move in self.board.legal_moves: self.execute_move(move)
                    self.selected_sq = None; self.legal_dots = []

    def execute_move(self, move):
        self.prev_eval = self.eval_score
        san = self.board.san(move)
        cap = self.board.piece_at(move.to_square)
        if cap:
            if self.board.turn == chess.WHITE: self.captured_by_white.append(cap.symbol())
            else: self.captured_by_black.append(cap.symbol())
        self.board.push(move)
        self.move_history.append(san)
        self.hint_move = None
        if self.engine:
            info = self.engine.analyse(self.board, chess.engine.Limit(time=0.1))
            score = info["score"].relative
            self.eval_score = (score.score() / 100.0) if not score.is_mate() else (10.0 if score.mate() > 0 else -10.0)
            if self.board.turn == chess.BLACK: self.eval_score *= -1
            diff = abs(self.eval_score - self.prev_eval)
            if diff < 0.2: self.last_move_quality = ("!!", COLORS["brilliant"])
            elif diff < 0.8: self.last_move_quality = ("Best", COLORS["best"])
            elif diff > 2.5: self.last_move_quality = ("??", COLORS["blunder"])
            else: self.last_move_quality = None

    def draw_board(self):
        theme = THEMES[self.current_theme_idx]
        for sq in chess.SQUARES:
            r, c = sq//8, sq%8
            dr, dc = (7-r, c) if self.user_color == chess.WHITE else (r, 7-c)
            x, y = dc*SQUARE_SIZE+OFFSET_X, dr*SQUARE_SIZE+OFFSET_Y
            col = theme[0] if (dr+dc)%2==0 else theme[1]
            if piece := self.board.piece_at(sq):
                if piece.piece_type == chess.KING and self.board.is_check() and piece.color == self.board.turn:
                    col = COLORS["check"]
            if self.selected_sq == sq: col = COLORS["select"]
            pygame.draw.rect(self.screen, col, (x, y, SQUARE_SIZE, SQUARE_SIZE))
            if piece:
                p_color = "#ffffff" if piece.color == chess.WHITE else "#000000"
                self.screen.blit(self.font_piece.render(SYMBOLS[piece.symbol()], True, p_color), (x+5, y-10))
        for d_sq in self.legal_dots:
            r, c = d_sq//8, d_sq%8
            dr, dc = (7-r, c) if self.user_color == chess.WHITE else (r, 7-c)
            dot_x, dot_y = dc*SQUARE_SIZE + OFFSET_X + SQUARE_SIZE//2, dr*SQUARE_SIZE + OFFSET_Y + SQUARE_SIZE//2
            s = pygame.Surface((30, 30), pygame.SRCALPHA)
            pygame.draw.circle(s, COLORS["capture_dot"] if self.board.piece_at(d_sq) else COLORS["dot"], (15, 15), 10)
            self.screen.blit(s, (dot_x-15, dot_y-15))

    def run(self):
        while True:
            now = time.time()
            dt = now - self.last_update
            self.last_update = now
            if self.state == "MENU": self.draw_menu()
            else:
                self.screen.fill(COLORS["bg"])
                self.draw_credits()
                self.draw_eval_bar()
                
                if self.cheated:
                    txt = self.font_big.render("CHEATING DETECTED:Auto Forfeit", True, COLORS["loss"])
                    self.screen.blit(txt, (WIDTH//2-txt.get_width()//2, HEIGHT//2))
                else:
                    if not self.board.is_game_over() and self.state == "PLAYING":
                        if self.board.turn == chess.WHITE: self.white_time -= dt
                        else: self.black_time -= dt
                    self.draw_board()
                    bot_label = f"BOT ({'Lvl ' + str(self.current_level) if self.mode == 'PRESET' else self.custom_elo})"
                    if self.user_color == chess.WHITE:
                        top_label, top_time, top_captures = f"{bot_label} (Black)", self.black_time, self.captured_by_black
                        btm_label, btm_time, btm_captures = "YOU (White)", self.white_time, self.captured_by_white
                    else:
                        top_label, top_time, top_captures = f"{bot_label} (White)", self.white_time, self.captured_by_white
                        btm_label, btm_time, btm_captures = "YOU (Black)", self.black_time, self.captured_by_black

                    pygame.draw.rect(self.screen, COLORS["btn"], (800, 20, 350, 120), border_radius=10)
                    t_mins, t_secs = divmod(max(0, int(top_time)), 60)
                    self.screen.blit(self.font_ui.render(top_label, True, COLORS["accent"]), (815, 30))
                    self.screen.blit(self.font_big.render(f"{t_mins:02d}:{t_secs:02d}", True, "#ffffff"), (815, 55))
                    tx = 815
                    for p in top_captures:
                        p_col = "#ffffff" if p.isupper() else "#000000"
                        self.screen.blit(self.font_captured.render(SYMBOLS[p], True, p_col), (tx, 95)); tx += 22

                    pygame.draw.rect(self.screen, "#2c2c2c", (800, 150, 350, 180), border_radius=10)
                    self.screen.blit(self.font_tiny.render("MOVE HISTORY", True, "#888888"), (815, 155))
                    hx, hy = 815, 180
                    for i in range(max(0, len(self.move_history)-14), len(self.move_history)):
                        self.screen.blit(self.font_tiny.render(f"{i+1}. {self.move_history[i]}", True, "#ffffff"), (hx, hy))
                        hy += 20; hx += 80 if hy > 310 else 0; hy = 180 if hy > 310 else hy

                    pygame.draw.rect(self.screen, COLORS["btn"], (800, 350, 350, 50), border_radius=10)
                    self.screen.blit(self.font_ui.render("HOME MENU", True, "#ffffff"), (915, 365))
                    pygame.draw.rect(self.screen, COLORS["accent"] if self.hints_used < 3 else COLORS["loss"], (800, 410, 350, 50), border_radius=10)
                    self.screen.blit(self.font_ui.render(f"HINT ({3-self.hints_used} left)", True, COLORS["bg"]), (835, 425))
                    pygame.draw.rect(self.screen, COLORS["accent"], (800, 470, 350, 50), border_radius=10)
                    self.screen.blit(self.font_ui.render("DOWNLOAD PGN", True, COLORS["bg"]), (905, 485))

                    pygame.draw.rect(self.screen, COLORS["btn"], (800, 660, 350, 120), border_radius=10)
                    b_mins, b_secs = divmod(max(0, int(btm_time)), 60)
                    self.screen.blit(self.font_ui.render(btm_label, True, COLORS["accent"]), (815, 670))
                    self.screen.blit(self.font_big.render(f"{b_mins:02d}:{b_secs:02d}", True, "#ffffff"), (815, 695))
                    bx = 815
                    for p in btm_captures:
                        p_col = "#ffffff" if p.isupper() else "#000000"
                        self.screen.blit(self.font_captured.render(SYMBOLS[p], True, p_col), (bx, 735)); bx += 22

                    # Moved Evaluation Quality Icon to the bottom-right area (above timer)
                    if self.last_move_quality:
                        icon_txt, icon_col = self.last_move_quality
                        pygame.draw.circle(self.screen, icon_col, (1130, 630), 25)
                        self.screen.blit(self.font_ui.render(icon_txt, True, "#ffffff"), (1130 - 12, 630 - 12))

                    if self.board.turn != self.user_color and not self.board.is_game_over() and self.state == "PLAYING":
                        pygame.display.flip()
                        res = self.engine.play(self.board, chess.engine.Limit(time=0.5))
                        self.execute_move(res.move)

                    if self.state == "PROMOTING":
                        s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA); s.fill(COLORS["overlay"]); self.screen.blit(s, (0,0))
                        pygame.draw.rect(self.screen, COLORS["sidebar"], (WIDTH//2-160, HEIGHT//2-60, 320, 120), border_radius=15)
                        promos = ['Q','R','B','N'] if self.user_color == chess.WHITE else ['q','r','b','n']
                        for i, p in enumerate(promos):
                            rect = pygame.Rect(WIDTH//2-140 + i*70, HEIGHT//2-35, 60, 60)
                            pygame.draw.rect(self.screen, COLORS["btn"], rect, border_radius=8)
                            self.screen.blit(self.font_captured.render(SYMBOLS[p], True, "#ffffff"), (rect.x+15, rect.y+10))

                    if self.board.is_game_over() or self.white_time <= 0 or self.black_time <= 0:
                        s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA); s.fill(COLORS["overlay"]); self.screen.blit(s, (0,0))
                        msg = "CHECKMATE!" if self.board.is_checkmate() else "DRAW"
                        txt = self.font_big.render(msg, True, COLORS["accent"])
                        self.screen.blit(txt, (WIDTH//2-txt.get_width()//2, HEIGHT//2-50))
                        pygame.draw.rect(self.screen, COLORS["win"], (WIDTH//2-100, HEIGHT//2+60, 200, 50), border_radius=10)
                        self.screen.blit(self.font_ui.render("BACK TO MENU", True, "#ffffff"), (WIDTH//2-75, HEIGHT//2+73))

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    if self.engine: self.engine.quit()
                    pygame.quit(); sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN: self.handle_click(event.pos)
            pygame.display.flip(); self.clock.tick(60)

    def draw_menu(self):
        self.screen.fill(COLORS["bg"]); self.draw_credits()
        title = self.font_big.render("OmniChess", True, COLORS["accent"])
        self.screen.blit(title, (WIDTH//2 - title.get_width()//2, 60))
        pygame.draw.rect(self.screen, COLORS["btn"], (150, 160, 320, 350), 2, border_radius=10)
        self.screen.blit(self.font_ui.render("ENGINE LEVEL", True, "#ffffff"), (250, 180))
        for i in range(8):
            rect = pygame.Rect(180 + (i%2)*140, 220 + (i//2)*70, 120, 55)
            col = COLORS["accent"] if (self.current_level == i+1 and self.mode == "PRESET") else COLORS["btn"]
            pygame.draw.rect(self.screen, col, rect, border_radius=8)
            self.screen.blit(self.font_ui.render(f"Level {i+1}", True, "#ffffff"), (rect.x+28, rect.y+18))
        pygame.draw.rect(self.screen, COLORS["btn"], (750, 160, 400, 200), 2, border_radius=10)
        self.screen.blit(self.font_ui.render("CUSTOM ELO MODE", True, "#ffffff"), (870, 180))
        elo_disp = self.font_big.render(str(self.custom_elo), True, COLORS["accent"] if self.mode == "ELO" else "#ffffff")
        self.screen.blit(elo_disp, (WIDTH - 320, 210))
        e_btns = [("-100", 800, 60), ("-10", 865, 45), ("+10", 980, 45), ("+100", 1030, 60)]
        for lbl, x, w in e_btns:
            pygame.draw.rect(self.screen, COLORS["btn"], (x, 270, w, 45), border_radius=5)
            self.screen.blit(self.font_ui.render(lbl, True, "#ffffff"), (x+5, 282))
        self.screen.blit(self.font_ui.render("PLAY AS:", True, "#ffffff"), (WIDTH//2 - 40, 420))
        for i, (label, color) in enumerate([("WHITE", chess.WHITE), ("BLACK", chess.BLACK)]):
            rect = pygame.Rect(500 + i*120, 460, 100, 45); col = COLORS["accent"] if self.user_color == color else COLORS["btn"]
            pygame.draw.rect(self.screen, col, rect, border_radius=5); self.screen.blit(self.font_ui.render(label, True, "#ffffff"), (rect.x+20, rect.y+12))
        self.screen.blit(self.font_ui.render("TIME CONTROL:", True, "#ffffff"), (WIDTH//2 - 90, 540))
        m, s = divmod(self.timer_setting, 60); self.screen.blit(self.font_big.render(f"{m:02d}:{s:02d}", True, COLORS["accent"]), (WIDTH//2 - 60, 580))
        t_btns = [("-60", 430), ("-10", 490), ("+10", 660), ("+60", 720)]
        for lbl, x in t_btns:
            pygame.draw.rect(self.screen, COLORS["btn"], (x, 580, 50, 45), border_radius=5)
            self.screen.blit(self.font_ui.render(lbl, True, "#ffffff"), (x+8, 592))
        pygame.draw.rect(self.screen, COLORS["win"], (WIDTH//2-120, 680, 240, 70), border_radius=15)
        self.screen.blit(self.font_big.render("START", True, "#ffffff"), (WIDTH//2-70, 690))

if __name__ == "__main__":
    ChessTitan().run()              


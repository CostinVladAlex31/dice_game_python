import random

class Dice:
    def __init__(self, fete=6, numar_zaruri=1):
        if fete < 2:
            print("Zarul trebuie sa aiba cel putin 2 fete!")
            self.fete = 6
        else:
            self.fete = fete
            
        if numar_zaruri < 1:
            print("Trebuie sa arunci cel putin un zar!")
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
    
    def display_result(self, result):
        if isinstance(result, list):
            print(f"Ai aruncat {self.numar_zaruri} zaruri: {result}")
            print(f"Suma totala: {sum(result)}")
        else:
            print(f"Ai aruncat: {result}")

class Game:
    def __init__(self):
        self.dice = Dice()
        self.Player_Score1 = 0
        self.Player_Score2 = 0
        self.current_player = 1
        self.target_score = 21
        
    def schimbare_jucator(self):
        if self.current_player == 1:
            self.current_player = 2
        else:
            self.current_player = 1
    
    def get_current_score(self):
        if self.current_player == 1:
            return self.Player_Score1
        else:
            return self.Player_Score2
    
    def add_points(self, points):
        if self.current_player == 1:
            self.Player_Score1 += points
        else:
            self.Player_Score2 += points
        
    def play(self):
        print("******Lucky Dice******\n")
        print("Incepe jocul, sper sa ai noroc!Primul care ajunge la 21 puncte castiga; daca ai depasit esti eliminat.")
        print("Tine minte!Daca nimeresti 1 ai pierdut.")
        
        while True:
            print(f"\n--- Jucatorul {self.current_player} ---")
            print(f"Scorul Jucatorului 1: {self.Player_Score1}")
            print(f"Scorul Jucatorului 2: {self.Player_Score2}")
            
            alegere = input("Te simti norocos? Arunci zarul? (Da/Nu): ")
            
            if alegere.lower() == "nu":
                print(f"Jucatorul {self.current_player} alege sa astepte.Se trece la jucatorul urmator.")
                self.schimbare_jucator()
                if self.Player_Score1 > 0 and self.Player_Score2 > 0:
                    break
                continue
            
            rezultate = self.dice.roll()
            if rezultate == 1:
                print(f"Jucatorul {self.current_player} a nimerit un numar ghinionist si a pierdut...")
                castigator = 2 if self.current_player == 1 else 1
                print(f"Jucatorul {castigator} castiga!")
                return
            
            self.dice.display_result(rezultate)
            
            if isinstance(rezultate, list):
                points = sum(rezultate)
            else:
                points = rezultate
                
            self.add_points(points)
            
            if self.get_current_score() > self.target_score:
                print(f"Jucatorul {self.current_player} a pierdut...Scor prea mare: {self.get_current_score()}")
                castigator = 2 if self.current_player == 1 else 1
                print(f"Jucatorul {castigator} castiga!")
                return
                
            if self.get_current_score() == self.target_score:
                print(f"Jucatorul {self.current_player} a obtinut scor perfect si castiga!")
                return
                
            self.schimbare_jucator()
        
        if self.Player_Score1 > self.Player_Score2:
            print(f"Jucatorul 1 castiga cu scorul {self.Player_Score1}!")
        elif self.Player_Score2 > self.Player_Score1:
            print(f"Jucatorul 2 castiga cu scorul {self.Player_Score2}!")
        else:
            print("Egalitate!")

my_game = Game()
my_game.play()

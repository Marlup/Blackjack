import numpy as np
class Color:
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

class BlackJack():
    
    rounds = 0
    DEALER_LIMIT = 17
    MAX_SCORE = 17
    POTENTIAL_MAX_NUM_DECKS = 10
    MAX_VALUE_21 = 21
    
    def __init__(
        self, 
        automatic_game=True,
        n_bots=1,
        n_human_players=0,
        number_of_decks=1
    ):
        self.automatic_game = automatic_game
        self.n_human_players = n_human_players
        self.n_human_players = n_bots
        self.n_players = n_human_players + n_bots
        if self.n_players < 1:
            raise Exception("BlackJack error. At least one human or bot player must exists")
        # Dealer has id zero by deafult
        self.players = [Player(0)]
        # Build bots first and humans last
        self.players = self.players + [Player(_id, _id <= n_bots) for _id in range(1, self.n_players + 1, 1)] # ternary operation.
        self.number_of_decks = number_of_decks
        self.potential_decks = []
        for n_decks in range(1, self.POTENTIAL_MAX_NUM_DECKS + 1):
            deck = np.repeat(np.array([np.repeat(card, 4) if card <= 10 else np.repeat(10, 4) for card in np.arange(1, 14)]), n_decks)
            self.potential_decks.append(deck)
        self.deck = np.repeat(np.array([np.repeat(card, 4) if card <= 10 else np.repeat(10, 4) for card in np.arange(1, 14)]), number_of_decks) # [4 * card if card > 10 else 4 * 10 for card in range(1, 14)]
        np.random.shuffle(self.deck)
        self.on_game = True
    
    def loop_game(self):
        while self.on_game:
            print('\n********************')
            print('Round number: ' + str(self.rounds + 1))
            print('**********************')
            self.start_round()
                
            self.rounds = self.rounds + 1
        self._process_dealer(self.players[0])
        self.report_end_game()
    
    def start_round(self):
        
        '''
        Start a round by giving one card to each player. Stack up each player's score
        '''
        
        np.random.seed()
        for player_number, player in enumerate(self.players):
            if player.stand or player.is_dealer:
                continue
                
            player.card = np.random.choice(self.deck, size=1, replace=False)
            # Assign the index of the card, to be deleted from deck, to a variable
            delete_card_from_deck = np.where(self.deck == player.card)[0][0]
            # Delete card from deck
            self.deck = np.delete(self.deck, delete_card_from_deck)
            self._process_potencial_decks(player)

            # Save the last card received by player
            player.card = player.card.item()
            # If card is 1 (Joker) let the player choose the card value to be 1 or 10
            if player.card == 1:
                if self.automatic_game or player.is_bot:
                    self._naive_joker_decision(player)
                else:
                    self._player_joker_decision(player)
            
            player.score = player.score + player.card
            
            if self.rounds > 0:
                if player.score <= self.MAX_VALUE_21:
                    self.try_set_player_stand(player)
                else:
                # Potential probabilities:
                    player.stand = True    
                self.check_end_game()
            self._show_deck_statistics(player, self.MAX_VALUE_21)
            self.report_game(player_number, player)
            
        return None
    
    def _process_potencial_decks(self, 
                                 player
                                ):
        for i in range(len(self.potential_decks)):
            potential_deck = self.potential_decks[i]
            delete_card_from_deck = np.where(potential_deck == player.card)[0][0]
            # Delete card from deck
            potential_deck = np.delete(potential_deck, delete_card_from_deck)
            self.potential_decks[i] = potential_deck
    
    def try_set_player_stand(self, 
                             player
                            ):
        '''
        Check if a player's score is equal to 21 (win), greater than 21 (lose) or 
        less than 21 (keeps playing). The player whether to stand.
        '''
        # Players have liberty to choose a card even when their score is 21
        if self.automatic_game or player.is_bot:
            self._anti_exceed_decision(player, self.MAX_SCORE)
        else:
            
            print(f"\n{player.player_type} player's card value is: " + str(player.card))
            print(f"{player.player_type} player's score is now: " + str(player.score))
            
            player.stand = input("Stand? (true/false)").lower()
            print('----------------')
            if player.stand in ["y", "yes", "t", "true"]:
                player.stand = True
            elif player.stand in ["n", "no", "f", "false"]:
                player.stand = False
    
    def _process_dealer(self, 
                        player
                       ):
        
        while not player.stand:
            
            player.card = np.random.choice(self.deck, size=1, replace=False)
            delete_card_from_deck = np.where(self.deck == player.card)[0][0]
            self.deck = np.delete(self.deck, delete_card_from_deck)
            player.card = player.card.item()
                
            if player.card == 1:
                self._naive_joker_decision(player)
                
            player.score = player.score + player.card
            if player.score >= self.DEALER_LIMIT:
                player.stand = True
            
            self._anti_exceed_decision(player, self.DEALER_LIMIT)
    
    # Take decision based on ACTUAL knowdledge of deck size
    def _certain_statistical_decision(self, 
                                      player, 
                                      score_target
                                     ):
        max_value = score_target - player.score
        uniques, counts = np.unique(self.deck, 
                                    return_counts=True)
        marginal_probs = counts / counts.sum()

        idx_where = np.where(uniques == max_value, 1, 0)
        max_value_idx = np.nonzero(idx_where)[0].item()

        prob_target = marginal_probs[:max_value_idx].sum()
        prob_keep_playing = np.random.rand()
        if prob_keep_playing < prob_target:
            player.stand = False
        else:
            player.stand = True
    
    # Calculate probabilities of potential decks and show them
    def _show_deck_statistics(self, 
                              player, 
                              score_target
                             ):
        if player.score < self.MAX_VALUE_21:
            max_value = score_target - player.score
            print('\n+++++++++++++++++++++++')
            print(Color.BOLD+ 'Current probabilities' + Color.END)
            print('+++++++++++++++++++++++')
            print(f"Probability of getting card value less or equal to {max_value}...")

            for i, potential_deck in enumerate(self.potential_decks):
                if max_value > 10:
                    continue
                n = len(potential_deck)
                uniques, counts = np.unique(potential_deck, 
                                            return_counts=True)
                marginal_probs = counts / counts.sum()
                marginal_probs_show = (100 * marginal_probs).round(2)

                idx_where = np.where(uniques == max_value, 1, 0)
                #print(max_value, uniques, idx_where)
                max_value_idx = np.nonzero(idx_where)[0].item()
                prob_target = (100 * marginal_probs[:max_value_idx].sum()).round(2)
                p_target_print = str(prob_target.round(2))
                print(f"\n...for deck {i} ({n} elements): {p_target_print}\n")
                print(f"Probability for each card value:\n", marginal_probs_show)
                print(f".........................................................")
        else:
            print("Any next card will make the player lose")
    
    # Take decision based on POTENTIAL hypothesized deck sizes
    def _uncertain_statistical_decision(self, 
                                        player, 
                                        score_target
                                       ):
        max_value = score_target - player.score
        uniques, counts = np.unique(self.deck, 
                                    return_counts=True)
        marginal_probs = counts / counts.sum()

        idx_where = np.where(uniques == max_value, 1, 0)
        max_value_idx = np.nonzero(idx_where)[0].item()

        prob_favourable = marginal_probs[:max_value_idx].sum()
        prob_keep_playing = np.random.rand()
        if prob_keep_playing < prob_favourable:
            player.stand = False
        else:
            player.stand = True
    
    def _anti_exceed_decision(self, 
                              player, 
                              score_target
                             ):
        if (player.score + 10) > score_target:
            player.stand = True
    
    def _player_joker_decision(self, player):
        print(f"\n{player.player_type} player's score is now: " + str(player.score))
        player.card = input('Player ' + str(player.id) + ' has to choose if Joker is 1 or 10 (True/False)')
        player.card = player.card.lower()
        if player.card in ["1", "t", "true"]:
            player.card = 1
        elif player.card in ["10", "f", "false"]:
            player.card = 10
    
    # Decision making functions when drawn card is 1
    def _naive_joker_decision(self, 
                              player):
        if (player.score + 10) <= self.MAX_VALUE_21:
            player.card = 10
        else:
            player.card = 1
        
    def check_end_game(self):
        # self.players[0] is the dealer
        non_dealer_players = self.players[1:]
        if all([player.stand for player in non_dealer_players]):
            self.on_game = False
    
    def report_end_game(self):
        
        print('\n+++++++++++++++')
        print(Color.BOLD+ 'End of game.' + Color.END)
        print('+++++++++++++++++')
        for player_number, player in enumerate(self.players):
            if not player.is_dealer:
                if player.score > self.MAX_VALUE_21:
                    player.win_vs_dealer = False
                elif self.players[0].score > self.MAX_VALUE_21:
                    player.win_vs_dealer = True
                elif player.score > self.players[0].score:
                    player.win_vs_dealer = True
                else:
                    player.win_vs_dealer = False

            print(Color.BOLD + f'\n{player.player_type} player ' + Color.END + str(player_number), ':')
            print('----------------')
            
            print('Score: ' + str(player.score))
            print('win: ' + str(player.win_vs_dealer))
            print('----------------')
        
        return None
    
    def report_game(self, 
                    player_number, 
                    player
                   ):
        print(Color.BOLD + f'\n{player.player_type} player ' + Color.END + str(player_number), ':')
        print('----------------')
        
        print('Card value: ' + str(player.card))
        print('Score: ' + str(player.score))
        print('stand: ' + str(player.stand))
        print('win: ' + str(player.win_vs_dealer))
        print('----------------')
        
        return None
            
class Player():
    dealer_exist = False
    def __init__(self, 
                 _id=0, 
                 is_bot=True, 
                 card=None
                ):
        if not isinstance(_id, int) :
            raise Exception("Error. Player ID must be an integer number (0 to inf)")
        if _id == 0 and self.dealer_exist:
            raise Exception("Error. The dealer already exists")
        if _id == 0:
            _id = 0
            self.is_dealer = True
            self.is_bot = True
            self.dealer_exist = True
        else:
            self.id = _id
            self.is_dealer = False
            self.is_bot = is_bot
        if is_bot:
            self.player_type = "bot"
        else:
            self.player_type = "human"
        self.player_type = self.player_type.capitalize()
        self.score = 0
        self.card = card
        self.stand = False
        self.win_vs_dealer = False
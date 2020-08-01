# PAIndemic

Is a platform developed by Pablo Sauma-Chacón of the University of Costa Rica, that allows a human player to participate in a match of the game Pandemic (cooperative board game published by Matt Leacock in 2007) with an intelligent artificial agent through a web browser. The system also allows the development and testing of AI agents by themselves.

If you desire to only try the agent evaluation, skip all the sections related to Unity/the web client.

## Getting Started

To get started you might require the following software and tools:
* Unity: The web client is built using Unity, all the files and resources needed are found within the "PandemicWeb" subfolder.
* Python 3: The server and game logic are implemented using Python 3 and its standard libraries (mostly).

Also, the reading of the rulebook and/or playing the game is highly encouraged, the rulebook is accessible here: [Pandemic-rulebook](https://images-cdn.zmangames.com/us-east-1/filer_public/25/12/251252dd-1338-4f78-b90d-afe073c72363/zm7101_pandemic_rules.pdf)

### Prerequisites

Most of the system is built using standard libraries but just in case here is a complete list of libraries used:
* Unity: only default libraries were used with the only exception of a JSON management library which is included in the project. All the required resource files are included.
* Python 3: For the game server and logic the full list of used libraries is the following: 
    * copy
    * enum
    * hashlib
    * http.server
    * itertools
    * json
    * os
    * numpy
    * random
    * shutil
    * signal
    * socketserver
    * string
    * sys
    * threading
    * time
    * traceback

### How to test an AI

To test an AI all you need to do is have their implementation inherit from the Player Class (explained below) with the two required request methods (request_action and request_discard). Our release includes a variety of agents including: RandomPlayer, HeuristicPlayer and PlanningPlayer which can be used as an example or for testing purposes.

To run the tests all that is required is to load the class into the FinalTests&#46;py file, modify the variable cls to the class name and execute. This script executes a number of games (currently 1000) using the desired number of threads (currently 7) for the 4-5-6 epidemics and 2-3-4 players combinations. A seed or seeds can be specified for the randomness, each game will receive a multiple of this seed as its randomness. If more than one seed is specified the script will run the games for each of these seeds (3 seeds x 1000 games x 9 combinations = 27000 games).

### How to get the client running

The Python server-game logic system simply requires the user to run the Server&#46;py code using Python. If you are missing any of the mentioned libraries, download and install them.
To run the client it is required to create a build of the web-client implementation. To create this build follow this guidelines:

* Run Unity and __ADD__ the project directory (_PandemicWeb_) to your projects.
* Choose whichever version you have available and select WebGL as target platform
* Confirm to whatever sacrifice Unity may demand
* Once it loads open Unity's menu: File -> Build and Run
* Create a new directory called _build_ in the same directory as your Server&#46;py and select it
* The build should be ready after a while

It's important that the generated build is stored in the /build/ folder in the same directory containing Server&#46;py file (which will be used to run the server). If you modify any of the filenames that interact with the web users then modifications of the .html files (stored in the /html/ folder) might be required to fix any broken links. The client will be available at localhost, but modifications can be done to run it in a public server using the -s command.

## Running the tests

### Testing the game logic

To test the game logic use Python to execute the Game&#46;py:
```
python Game.py
```
The expected output of this should be a simulation of the game in which two random players play with each other until they (most likely) lose. The results of the simulation should be readable in the console (sys&#46;stdout).

### Testing the server and web-client

To test the server and web-client first make sure the client has been already built using Unity and is on the /build/ folder. Then you may start the execution of the server with Python:
```
python Server.py
```
The server should start running without problems and you may access the local address: [127.0.0.1:31337](127.0.0.1:31337).
An html webpage should load on your web browser and a message of the request should appear in the console running your server. If this doesn't happens it means there might be a problem with your Server&#46;py file or some of the libraries might be missing.

Once inside the webpage you may navigate onwards: first through the consent form, which is required when performing any kind of research in which living being participate (but you may modify it at will or simply skip it by modifyng the html) and then a tutorial form, which might be changed or extended in the future. At the end of the tutorial there is a play button which directs the browser to your build.

The server should then quickly load all the required files and the game should appear in your web browser. If this does not happen there might be one of two issues: either your server is failing to load the desired files (either because it can't find them, libraries are missing or Turing's ghost despises you) or your game client is flawed some way (in which case may the Unity gods forgive you). 

## Understanding the game logic

### Game class

The game logic is implemented in a way in which the main object (an instance of class Game) acts as the main coordinator and controller of all the game logic:

* It controls whose turn is it
* It controls the game phases
* It has access to all the main data structures

And it is through it that the interaction with the game logic should be performed. First, let's have a look at its creation parameters:
```
Game.__init__(self,
        players,
        epidemic_cards=4,
        cities=city_cards,
        starting_city="atlanta",
        number_cubes=24,
        log_game=True,
        external_log=None
)
```

This initialization allows for different parameters to be set in:
* __players__ is an array of objects of the class (or inherited classes of) Player, for the web interaction it's expected to be of size 2, but in theory there's no such restriction (though the rules of the game state should be played up to 4 players).
* __epidemic_cards__ is the number of epidemics in the game: the game rules state 4 to 6 epidemic cards should be used according to the desired difficulty.
* __cities__ is a dictionary in which each key is the name of a city and maps to another dictionary with the following **necessary** values:
    * color: string which represents the color of the disease that infects that city
    * pop: integer which represents the number of inhabitants of the city, required to decide which player starts
    * connects: list of strings with the names of all cities connected to this one
    * **Note: When playing using the game-client the use of the default cities is required**
* __starting_city__ is the name of the starting city, by default it is in Atlanta (home of the CDC) but can be changed at will (but must be a city inside the __cities__ dictionary).
* __number_cubes__ is the number of colored disease cubes that there will be for each color, when the players require an specific color but there are none left then they lose the game.
* __log_game__ is a boolean representing whether the verbose of the game will be stored in the "self.commons['game_log']" string, this must be *True* when playing with the game client to keep the game log active.
* __external_log__ is a stream where the verbose of the game should be written, by default it is *None*, but sys.stdout can be used to redirect the verbose to console or a file stream can be used for future storage.

This allows versatility on the implementation of the game, allowing for a different number of players, epidemics, cities, starting positions, cubes and even colors (through the cities dictionary) to be set in! Nonetheless, I recommend sticking to the default parameters unless required otherwise.

Before starting any game you will be required to call the _setup_ function which looks like this:
```
setup(players_roles=None)
```
This function sets up the game, shuffles the decks, resets everything to it's starting position and changes the __game state__ from __NOT_PLAYING__ to __PLAYING__. The players_roles parameter can be used to define which roles each player wants to play, if it's _None_ then a random one will be assigned to each player.

With the game set, let's learn how to interact with the logic, there are two main ways to interact with the game object:

* Using the automated *game_loop* function which will run the game using the current players until the game is over.
* Manually moving the game through each of its phases controlling the flow, to this end you will need to understand the different turn phases:
    * __NEW__ is the state in which the turn has just began, it's an inbetween stage used after a turn ends and before a player can start performing actions. The *start_turn()* function must be called which will advance the turn phase to the *ACTIONS* phase.
    * __ACTIONS__ is the state in which the current player has a number of actions remaining (1 to 4) and the _do_action(action, **kwargs)_ function must be called to reduce the number of actions by 1 until the actions remaining are 0. If the actions remaining reaches 0 then the turn phase advance to the *DRAW* phase. Also an action may cause a player to exceed its hand limit, which might trigger a transition to the *DISCARD* phase and change the current player to the one who needs to discard.
	* __DRAW__ is the state in which the current player is waiting to draw cards. The _draw_phase()_ function must be called which will draw new cards for the player. If any of the losing conditions were to be triggered, then the turn phase will advance to the *INACTIVE* phase; if the player's hand exceeds the maximum then the turn phase advances to the *DISCARD* phase; or else it will advance to the *INFECT* phase.
	* __DISCARD__ is the state in which the current player must choose one of its cards to discard. The _do_discard(discard)_ function must be called which will discard the card from the player's hand, this will need to be performed until the player's hand stops exceeding the maximum. If there were any actions remaining for a previous player, then the control of the turn will return to that player and the turn phase will return to its *ACTIONS* phase; or else, the turn phase will advance to the *INFECT* phase.
	* __INFECT__ is the state in which the current player is waiting to apply the infections of its turn. The _end_turn()_ function must be called which will trigger the infections across the cities according to the cards drawn from the infection deck. If any of the losing conditions were to be triggered, then the turn phase will advance to the *INACTIVE* phase; if the game hasn't ended, then the turn counter is increased by one and a the next current player is selected, moving the turn phase to its *NEW* phase.
	* __INACTIVE__ is the state in which the game has already ended, to restart the game a call to the _setup(player_roles=None)_ function will need to be performed. In this turn phase the _game_state_ might be __NOT_PLAYING__ (if no game has been started), __WON__ or __LOST__. 

Many of this functions are really straight-forward since they have no parameters, nonetheless it will be important to explain two of them with more depth: *do_action* and *do_discard* because this ones depend on very specific parameters to work.

* __do_action(action, **kwargs)__ is a function that receives a string which is the name of an action (function) that can be performed by players and a dictionary of arguments **kwargs which will be used to give the function is parameters.
* __do_discard(discard)__ is a function that receives a string which is the name of a card in the player's hand and will discard it.

To understand how this all wraps together now it is important to learn about the player class.

### Player class

The player class is the main in-game actor after the game logic. It's the one who will get to choose how the game develops and it's on this class upon which all agents should be developed for the system. 
The class itself contains a variety of attributes and functions (proper to a player in game, like its hand, position, role, and functions of the actions it can perform in game), but there are three among them which are the ones that **must** be understood to develop an agent for this system:

* __available_actions(game)__ this function takes in the Game-class object as it's parameter and returns a dictionary with the complete information of all possible actions an agent may perform given the current game state.
    * The dictionary's keys are the function names mapping to a list of possible combinations of valid parameters
    * Each combination of parameters is stored in the list as a dictionary of **kwargs
    * Therefore it returns a dictionary of lists of parameters' dictionaries
* __request_action(game)__ this is the function that will be called by the game object when it requires your agent to perform an action during an automated run, also it's your way of telling your automated player "it is your turn" during a manual run. Once this function is called, the game will not continue until the function returns an action and a parameter dictionary ( _return action,kwargs_ ).
* __request_dicard(game)__ this is the function that will be called by the game object when it requires your agent to perform a discard during an automated run, also it's your way of telling your automated player "you must discard" during a manual run. Once this function is called, the game will not continue until the function returns the name of a card to discard.

What this means is that to implement an agent for this system the only requirement is to develop an object which inherits from the Player-class, which as an implementation of its own *request_action* and *request_discard* functions. What this also means is that you can use the information in-game to feed that information to your agent and implement its decision making at your will.

Once an agent is implemented you can test it by making it play with itself using the automated *game_loop* function:

```
g = Game([MyAgent(), MyAgent()], external_log = True)
g.setup()
g.game_loop()
```

**Note: The system has been built for research purposes so there is no access restriction implemented on the system whatsoever (all variables are public). It is your responsability the mantain the system consistency when manipulating any of these structures directly if you decide not to use the proper channels to manipulate the game logic***

## Understanding the server logic

The Server script has a number of global variables which might be edited at will to change its behaviour accordingly:
```
debug = True
log_games = False
HOST_NAME = "127.0.0.1"
PORT_NUMBER = 31337
computers = [RandomPlayer]
```
The variables will be explained as follows:
* __debug__: when this variable is True then all the error log output will be directed to the sys.stdout else the output will be logged in the server.log file
* __log_games__: when this variable is true the games played by the web users will be stored in text files inside a /logs/ subfolder for future analysis
* __HOST_NAME__ and __PORT_NUMBER__: are the address and port respectively which will be used to access the server
* __computers__: is a list of classes which should include the AIs you want to test, whenever a new player starts a game one of them will be picked at random and teamed up with the player

You may edit any other configurations at will, I know this server may have HUGE security concerns, so please let me know if you come up with any improvements.

## Observable space

The system provides a wide variety of game state information through the current structure, each of the different variables will be explained here:

* __Game information__: This attributes can be accesed through the object game
    * __game_turn__: Current turn number, starts at 1
    * __game_state__: Current game state, a value of the GameState enum: NOT_PLAYING, PLAYING, WON and LOST
    * __turn_phase__: Current turn phase, a value of the TurnPhase enum: INACTIVE, NEW, ACTIONS, DRAW, DISCARD and INFECT 
    * __current_player__: Number of the current player, a value from 0 to number of players - 1
    * __actions__: Number of remaining actions in the current turn, a value from 0 to 4
    * __infection_rate__: Number of infections applied at the end of each turn, starts at 2
    * __infection_counter__: Number of infections that have occured since the beginning of the game
    * __outbreak_counter__: Number of outbreaks that have occured since the beginning of the game
    * __cures__: Dictionary that tracks which cures have been found: cures["color"] = True/False
    * __eradicated__: Dictionary that tracks which diseases have been eradicated: eradicated["color"] = True/False
    * __remaining_disease_cubes__: Dictionary that tracks how many remaining cubes there are of each color: remaining_disease_cubes["color"] = int
* __Card object information__: Card objects are used in the players' hands and in the player deck, their information is stored in the following attributes:
    * __name__: String with the name of the card
    * __cardtype__: A value of the CardType enum: MISSING, CITY, EVENT and PANDEMIC (EVENT is currently not in use and MISSING is used only when the deck runs out of cards and the players lose the game)
    * __color__: String with the color of the card, if the card is colorless then that value is None
* __Player information__: This attributes can be accessed through the object game.players[player_number]
    * __location__: String with the name of the current city
    * __role__: Player's role, a value of the PlayerRole enum, currently restricted to: SCIENTIST, RESEARCHER, MEDIC and QUARANTINE_SPECIALIST
    * __cards__: Array of Card objects in the player's hand
    * __colors__: Dictionary that tracks the number of cards with each color in the player's hand
* __City information__: This attributes can be accessed through the object game.cities["city_name"]
    * __name__: String with the name of the city
    * __color__: String with the color of the city
    * __neighbors__: Array of strings with the names of neighboring cities
    * __disease_cubes__: Dictionary that tracks the number of disease cubes present of each color: disease_cubes["color"] = int
    * __research_station__: Boolean value representing the presence or absence of a research station in the city
* __Player deck information__: This attributes can be accessed through the object game.player_deck
    * __deck__: The current player deck, __this attribute should not be read by any agent__
    * __discard__: Array of cards in the discard pile of the player deck
    * __remaining__: Number of cards still remaining in the deck
    * __epidemic_countdown__: Cards remaining in this set of player cards due to the smoothed randomness of epidemics
    * __expecting_epidemic__: Boolean showing whether this set's epidemic is yet to happen
    * __colors__: Dictionary containing the number of remaining cards by color (including "epidemic" and None): colors["color"] = int
    * __possible_deck__: Property which returns a randomized and valid version of the current player deck
* __Infection deck information__: This attributes can be accessed through the object game.infection_deck
    * __deck__: The current infection deck, __this attribute should not be read by any agent__
    * __discard__: Array of cards in the discard pile of the infection deck
    * __known_cards__: Array of arrays, each representing a different set of known cards (result of the epidemic's reshuffling)
    * __possible_deck__: Property which returns a randomized and valid version of the current infection deck

## Authors

* Pablo Sauma-Chacón
    *  Contact me at: blopa.sauma@gmail.com or pablo.saumachacon@ucr.ac.cr
* Markus Eger, thesis advisor

## License

Included in LICENSE.txt

## Acknowledgments

* Special thanks to Markus for his counseling and for allowing me to rip off 90% of his A-star implementation
* Thanks to thomaskeefe for his implementation of Pydemic which gave me inspiration for this project


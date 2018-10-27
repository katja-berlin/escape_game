# Escape Game web app

This project provides an easy to customize version of a web-based puzzle solutions checker for an escape game.
For example: After creating an escape game for your friends with real life puzzles you need an easy but interesting way for them to check their solutions on their smartphone?
This project allows you to do just that.

## Project background

Using the Python Flask framework I built this web app as an interactive solution checker for my 1.5-2h long escape game during my Halloween party 2018. 
It uses SQLite as database to store the game's questions and answers and the player's current progress.

In the spirit of Halloween, the demo example provided is a bit ghoulish and shows the questions and answers used during my game. 
(I plan to release a step-by-step guide for information on the real-life puzzles I used).

The game starts with a hidden QR code which serves as the entry point. 
The encoded URL has a unique player ID which is set as a cookie on the player's browser.
All game state is stored on the server side allowing the player to resume the game at any time using the same URL.

## Features
* Track status of each player/team through unique IDs on the server.
* Ability to customize answers and questions in the used SQLite database.
* Status page for players to see how many questions they already solved.
* Customized error pages in case users try to cheat and guess URLs :)
* Easily modifiable HTML templates by using the Python Flask framework.
* Prepopulates already solved answers in input field.

## Screenshots
![start page](screenshots/01_start_small.png "Start page" )
![question page](screenshots/02_question_small.png "Question page" )
![check wrong](screenshots/03_check_wrong_small.png "Check wrong answer" )
![check correct](screenshots/04_check_correct_small.png "Check correct answer" )
![status overview page](screenshots/05_status-overview_small.png "Status overview page" )
![numerical input](screenshots/06_number-input_small.png "Numerical input" )
![error cheating](screenshots/07_error-no-cheating_small.png "Error: Cheating" )
![error player_id](screenshots/08_error_player-id_small.png "Error: Wrong player_id" )

## Authors
* **Katja Berlin** - Initial work - [katja-berlin](https://github.com/katja-berlin/ "Katjas Github Profil")
* **Michael Berlin** - Code review - [michael-berlin](https://github.com/michael-berlin/ "Michaels Github Profil")
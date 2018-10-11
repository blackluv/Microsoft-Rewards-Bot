# Microsoft-Rewards-Bot
 
Microsoft Rewards (Bing Rewards) Bot - Completes searches and quizzes
, written in Python!   :raised_hands: 

<h2>Overview</h2>

This program will automatically complete search requests and quizzes on Microsoft Rewards! This bot runs selenium in headless mode for deployment on VPS and for increased performance on local machines. The bot also uses selenium's user agent options to fulfill points for all three platforms (pc, edge browser, mobile). Search terms are the top daily headlines for a given category, retrieved via newsapi.org's free API. 100% free to use and open source.  Code critique/feedback and contributions welcome!


<h2>Features</h2> 
 
- Completes PC search, Edge search, Mobile search via user agents
- Completes polls, all types of quizzes (multiple choice, click and drag and reorder), and explore dailies 
- Headless mode (Confirmed working on DigitalOcean linux droplet)  
- Supports unlimited accounts via JSON  
- Customizable randomized search speeds  
- Customizable search queries via newsapi's API  
- Customizable log file path
	- Logs errors and info by default, can log executed commands and search terms via changing log.level to logging.DEBUG
- Only tested and confirmed working for U.S. (more to come!)  

<h2>REQUIREMENTS</h2>
- Python 3.7
- Selenium 3.14.0
- Requests 2.19.1


<h2>HOW TO USE</h2> 
 
1. Clone repo
2. Open cmd/terminal/shell and navigate to repo
3. Modify ms_rewards_login_dict.json with your account names and passwords
4. Modify news_api_key.json with your newsapi.org API key  
5. Open cmd/terminal/shell
6. Enter into cmd/terminal/shell: `pip install -r requirements.txt`
	- This installs dependencies (selenium and requests)
7. Enter into cmd/terminal/shell: `python ms_rewards.py`  
	- Script by default will run headlessly (can change this setting in the .py file)  
	- Script by default will execute mobile, pc, edge, searches, and complete quizzes for all accounts (can change this setting in the .py file) 
	- Run time for one account is under 5 minutes, for 100% daily completion  
8. Crontab (Optional for automated script daily on linux)  
	- Enter in terminal: `crontab -e`
	- Enter in terminal: `0 12 * * * python ms_rewards.py`
		- Can change the time from 12am server time to whenever the MS daily searches reset (~12am PST)
	- Change the paths to the json in the .py file to appropriate path
	
<h2>TO DO</h2>

- Argparse for options:
	- headless mode
	- select mobile or pc search, or pc quizzes
	- logging 
	- custom newsapi categories
	- custom user agents
- Default to Incognito Mode
- Combine API Key and Account Names to the same JSON (maybe single config file)
- Rewrite script into class-based code
- os.environ variables for multiple logins (current account names and passwords are too long)
- Proxy support
- Add requirements.txt for dependencies
- Multithreaded mode
- Split code into different py files for maintainability
- Support for other regions


<h2>License</h2>

100% free to use and open source.  :see_no_evil: :hear_no_evil: :speak_no_evil:


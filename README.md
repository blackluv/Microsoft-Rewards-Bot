# Microsoft-Rewards-Bot
 
Microsoft Rewards (Bing Rewards) Bot - Completes search and quiz
, written in Python!  

<h2>Overview</h2>
This program will automatically complete search requests and quizzes on Microsoft Rewards! This bot runs selenium headlessly by default for deployment on VPS and for increased performance on local machines. The bot also uses selenium's user agent options to fulfill points for all three platform (pc, edge browser, mobile). Search terms are the top headlines for a given category, retrieved via newsapi.org's free api. 100% free to use and open source.  :raised_hands:  


<h2>Features</h2>  
-Completes PC search, Edge search, Mobile search via user agents.  
-Headless mode (Confirmed working on Digital Ocean linux droplet).  
-Supports unlimited accounts via JSON.  
-Customizable randomized search speeds.  
-Customizable search queries via newsapi's api.  
-Logs errors and info by default, can log executed commands and search terms via changing log.level to logging.DEBUG.  



<h2>How TO USE</h2>  
1. Clone repo.  
2. Modify ms_rewards_login_dict.json with your account names and passwords.  
3. Modify news_api_key.json with your news api key.  
4. Open cmd/terminal/shell and navigate to repo.  
5. Enter into cmd/terminal/shell: `python ms_rewards.py`  
	-Script by default will run headlessly (can change this setting in the .py file)  
	-Script by default will execute mobile, pc, edge, searches, and complete quizzes for all accounts (can change this setting in the .py file).  
	-Run time for one account is under 5 minutes, for 100% daily completion.  
6. Crontab (Optional for automated script daily on linux).  
	-`crontab -e`
	-`0 12 * * * python ms_rewards.py`
		-Can change the time from 12am server time to whenever the MS daily searches reset (~12am PST).
	
<h2>TO DO</h2>
- Argparse for options:
	- headless mode
	- select mobile or pc search, or pc quizzes
	- logging 
	- custom newsapi categories
	- custom user agents
- Default to Incognito Mode
- Combine API Key and Account Names to the same JSON (maybe single config file)
- Rewrite script into class based code
- os.environ variables for multiple logins (current account names and passwords are too long)
- Proxy support

<h2>License</h2>
100% free to use and open source. You are free to do whatever you want.


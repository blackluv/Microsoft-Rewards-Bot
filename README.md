# Microsoft-Rewards-Bot
 
Microsoft Rewards (Bing Rewards) Bot - Completes searches and quizzes
, written in Python!   :raised_hands: 

<h2>Overview</h2>

This program will automatically complete search requests and quizzes on Microsoft Rewards! Search terms are the daily top searches retrieved using Google Trends' api. This bot runs selenium in headless mode for deployment on VPS and for increased performance on local machines. The bot also uses selenium's user agent options to fulfill points for all three platforms (pc, edge browser, mobile). 100% free to use and open source.  Code critique/feedback and contributions welcome!


<h2>Features</h2> 
 
- Completes PC search, Edge search, Mobile search via user agents
- Retrieves top daily searches via google trends' API
- Completes polls, all types of quizzes (multiple choice, click and drag and reorder), and explore dailies 
- Headless mode (Confirmed working on DigitalOcean linux droplet)  
- Supports unlimited accounts via JSON, in randomized order.  
- Randomized search speeds   
- Logs errors and info by default, can log executed commands and search terms via changing log.level to logging.DEBUG
- Tested and confirmed working for U.S. (more to come!)  

<h2>REQUIREMENTS</h2>

- Python 3.6
- Selenium 3.14.0
- Geckodriver for Selenium 

<h2>HOW TO USE</h2> 

1. Clone and navigate to repo
2. Modify ms_rewards_login_dict.json with your account names and passwords
3. Enter into cmd/terminal/shell: `pip install -r requirements.txt`
	- This installs dependencies (selenium)
4. Enter into cmd/terminal/shell: `python ms_rewards.py --headless --mobile --pc --quiz`
	- enter `-h` or `--help` for more instructions
		- `--headless` is for headless mode
		- `--mobile` is for mobile search
		- `--pc` is for pc search
		- `--quiz` is for quiz search  
	- Script by will execute mobile, pc, edge, searches, and complete quizzes for all accounts (can change this setting in the .py file)
	- Script by default will run headlessly (can change this setting in the .py file)  
	- Run time for one account is under 5 minutes, for 100% daily completion 
	- If python environment variable is not set, enter `/path/to/python/executable ms_rewards.py`
4a. For completing points from email links:
	- Modify email_links.txt file with email links.
		- Copy and paste links without surrounding quotes, like such:
 
```
https://e.microsoft.com/data/link1
https://e.microsoft.com/data/link2
https://e.microsoft.com/data/link3
```

        - Enter cmd/terminal/shell argument `python ms_rewards.py --email`
	- **Script will be manual, requires key press to continue, as the quizzes are not yet standardized.**
	 
5. Crontab (Optional for automated script daily on linux)  
	- Enter in terminal: `crontab -e`
	- Enter in terminal: `0 12 * * * /path/to/python /path/to/ms_rewards.py --headless --mobile --pc --quiz`
		- Can change the time from 12am server time to whenever the MS daily searches reset (~12am PST)
	- Change the paths to the json in the .py file to appropriate path

NOTE: If geckodriver for selenium is missing:

General Instructions (Windows, Linux, OS X)
1. download [geckodriver here](https://github.com/mozilla/geckodriver)
2. extract to python parent directory e.g. 'C:\Python37-22'

Or if on OS X/Linux
1. `brew install geckodriver`


<h2>TO DO</h2>

- Argparse for options:
	- logging 
	- custom user agents
- Rewrite script into class-based code or Organize monolithic code into different py files for maintainability
- os.environ variables for multiple logins (current account names and passwords are too long)
- Proxy support
- Multithreaded mode or seleniumGrid
- Support for other regions

<h2>License</h2>

100% free to use and open source.  :see_no_evil: :hear_no_evil: :speak_no_evil:


<h2>Versions</h2>

**2018.02**

	- Added argparse
	- Added points from email links
	- Added randomized account login order
	- Reworked newsapi.org API to google trends
	- Fixed logging
	- Fixed issue with dropped searches

**2018.01**

	- Initial release
	- Basic functionality for completing searches and quizzes.
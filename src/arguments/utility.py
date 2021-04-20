from termcolor import colored
import requests
from rich.console import Console
import sys as sys

# Required for Questions Panel
import os
import time
from collections import defaultdict
from simple_term_menu import TerminalMenu
import webbrowser
from pygments import highlight
from pygments.lexers.markup import MarkdownLexer
from pygments.formatters import Terminal256Formatter

from .error import SearchError
from .save import SaveSearchResults
from .markdown import MarkdownRenderer

# Required for OAuth
import json
from oauthlib.oauth2 import MobileApplicationClient
from requests_oauthlib import OAuth2Session

# Required for Selenium script and for web_driver_manager
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager

console = Console()

class Questions_Panel_stackoverflow():
    def __init__(self):
        self.questions_data = []                        # list(  list( question_title, question_link, question_id )...  )
        self.answer_data = defaultdict(lambda: False)   # dict( question_id:list( body, link )) corresponding to self.questions_data
        self.batch_ques_id = ""
        self.line_color = "bold red"
        self.heading_color = "bold blue"
        self.search_content_url = "https://api.stackexchange.com/"

    def populate_question_data(self, questions_list):
        """ Function to populate question data property
            Creates batch_id request to stackexchange API and
            Stores the returned data data in the following format:
                list(  list( question_title, question_link, question_id )  )
        """
        for question_id in questions_list:
            self.batch_ques_id += str(question_id) + ";"
        try:
            resp = requests.get(
                f"{self.search_content_url}/2.2/questions/{self.batch_ques_id[:-1]}?order=desc&sort=votes&site=stackoverflow&filter=!--1nZwsgqvRX"
            )
        except:
            SearchError("Search Failed", "Try connecting to the internet")
            sys.exit()
        json_ques_data = resp.json()
        self.questions_data = [[item['title'], item['question_id'], item['link']] for item in json_ques_data["items"]]

    def populate_answer_data(self):
        """ Function to populate answer data property
            Creates batch_id request to stackexchange API and
            Stores the returned data data in the following format:
                list(  list( question_title, question_link, question_id )  )
        """
        try:
            resp = requests.get(
                f"{self.search_content_url}/2.2/questions/{self.batch_ques_id[:-1]}/answers?order=desc&sort=votes&site=stackoverflow&filter=!--1nZwsgqvRX"
            )
        except:
            SearchError("Search Failed", "Try connecting to the internet")
            sys.exit()
        json_ans_data = resp.json()
        for item in json_ans_data["items"]:
            self.answer_data[item['question_id']] = item['body_markdown']

    def return_formatted_ans(self, id):
        # This function uses pygments lexers ad formatters to format the content in the preview screen
        body_markdown = self.answer_data[int(id)]
        if(body_markdown):
            body_markdown = str(body_markdown)
            body_markdown = body_markdown.replace("&amp;", "&")
            body_markdown = body_markdown.replace("&lt;", "<")
            body_markdown = body_markdown.replace("&gt;", ">")
            body_markdown = body_markdown.replace("&quot;", "\"")
            body_markdown = body_markdown.replace("&apos;", "\'")
            body_markdown = body_markdown.replace("&#39;", "\'")
            lexer = MarkdownLexer()
            formatter = Terminal256Formatter(bg="light")
            highlighted = highlight(body_markdown, lexer, formatter)
        else:
            highlighted = "Answer not viewable. Press enter to open in a browser"
        return highlighted

    def navigate_questions_panel(self):
        # Code for navigating through the question panel
        console.rule('[bold blue] Relevant Questions', style="bold red")
        console.print("[yellow] Use arrow keys to navigate. 'q' or 'Esc' to quit. 'Enter' to open in a browser")
        console.print()
        options = ["|".join(map(str, question)) for question in self.questions_data]
        question_menu = TerminalMenu(options, preview_command=self.return_formatted_ans)
        quitting = False
        while not(quitting):
            options_index = question_menu.show()
            try:
                options_choice = options[options_index]
            except Exception:
                return
            else:
                question_link = self.questions_data[options_index][2]
                webbrowser.open(question_link)

class Utility():
    def __init__(self):
        # the parent url
        self.search_content_url = "https://api.stackexchange.com/"

    def __get_search_url(self, question, tags):
        """
        This function returns the url that contains all the custom
        data provided by the user such as tags and question, which
        can finally be used to get answers
        """
        return f"{self.search_content_url}/2.2/search/advanced?order=desc&sort=relevance&tagged={tags}&title={question}&site=stackoverflow"

    def make_request(self, que, tag: str):
        """
        This function uses the requests library to make the rest api call to the stackexchange server.
        :param que: The user questions that servers as a question in the api.
        :type que: String
        :param tag: The tags that user wants for searching the relevant answers. For e.g. TypeError might be for multiple languages so is tag is used as "Python" then the api will return answers based on the tags and question.
        :type tag: String
        :return: Json response from the api call.
        :rtype: Json format data
        """
        with console.status("Searching..."):
            try:
                resp = requests.get(self.__get_search_url(que, tag))
            except:
                SearchError("\U0001F613 Search Failed", "\U0001F4BB Try connecting to the internet")
                sys.exit()
        return resp.json()

    def get_que(self, json_data):
        """
        This function returns the list of ids of the questions
        that have been answered, from the response that we get
        from the make_request function.
        """
        que_id = []
        for data in json_data['items']:
            if data["is_answered"]:
                que_id.append(data["question_id"])
        return que_id

    def get_ans(self, questions_list):
        stackoverflow_panel = Questions_Panel_stackoverflow()
        stackoverflow_panel.populate_question_data(questions_list)
        stackoverflow_panel.populate_answer_data()
        stackoverflow_panel.navigate_questions_panel()

    # Get an access token and extract to a JSON file "access_token.json"
    @classmethod
    def setCustomKey(self):
        client_id = 20013

        # scopes possible values:
        # read_inbox - access a user's global inbox
        # no_expiry - access_token's with this scope do not expire
        # write_access - perform write operations as a user
        # private_info - access full history of a user's private actions on the site
        scopes = 'read_inbox'

        authorization_url = 'https://stackoverflow.com/oauth/dialog'
        redirect_uri = 'https://stackexchange.com/oauth/login_success'

        # Create an OAuth session and open the auth_url in a browser for the user to authenticate
        stackApps = OAuth2Session(client=MobileApplicationClient(client_id=client_id), scope=scopes, redirect_uri=redirect_uri)
        auth_url, state = stackApps.authorization_url(authorization_url)

        # Try to install web drivers for one of these browsers
        # Chrome, Firefox, Edge (One of them must be installed)
        try:
            driver = webdriver.Chrome(ChromeDriverManager().install())
        except ValueError:
            try:
                driver = webdriver.Firefox(executable_path=GeckoDriverManager().install())
            except ValueError:
                try:
                    driver = webdriver.Edge(EdgeChromiumDriverManager().install())
                except ValueError:
                    print("You do not have one of these supported browsers: Chrome, Firefox, Edge")

        # Open auth_url in one of the supported browsers
        driver.get(auth_url)

        # Close the window after 20s (Assuming that the user logs in within 30 seconds)
        time.sleep(30)
        # Close the windows as soon as authorization is done
        try:
            WebDriverWait(driver, 1).until(
                EC.presence_of_element_located((By.TAG_NAME, "h2"))
            )
            callback_url = driver.current_url
        finally:
            driver.quit()

        # Extract access token data from callback_url
        accessTokenData = stackApps.token_from_fragment(callback_url)

        # Store the access token data in a dictionary
        jsonDict = {
            "access_token": accessTokenData['access_token'],
            "expires": accessTokenData['expires'],
            "state": state
        }

        with open('access_token.json', 'w') as jsonFile:
            json.dump(jsonDict, jsonFile)
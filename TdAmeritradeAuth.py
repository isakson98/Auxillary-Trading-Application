from selenium.webdriver.chrome.options import Options
from splinter import Browser
import time #to pause the time
import urllib # to parse the url and then decode it
import os
import requests

#This file gets an access token from TD, which expires every 30 minutes

#splinter => selenium with less lines of code

class TDAuthentication:
	def __init__(self, client_id, password, username, secret_city, secret_mascot, secret_restaurant, secret_mother):
		self.client_id = client_id
		self.password = password
		self.username = username
		self.secret_city = secret_city
		self.secret_mascot = secret_mascot
		self.secret_restaurant = secret_restaurant
		self.secret_mother = secret_mother
		self.access_code = None
		self.access_token = None

##getting authorization token (3 months) which is needed to get access token (30 minutes)
	def get_access_code(self):
		#define the path of where the chrome driver is located
		options = Options()
		options.add_argument("window-size=800,500")
		executable_path = {'executable_path' : r'C:\Users\isaks\Desktop\chromedriver_win32\chromedriver'}

		#create a new instance of the chrome browser
		browser = Browser('chrome', **executable_path, headless = True)

		#define the components of the url
		method = 'GET'
		url = 'https://auth.tdameritrade.com/auth?'
		#adding a piece to the client id 
		client_code = self.client_id + '@AMER.OAUTHAP'
		payload = {'response_type' : 'code', 'redirect_uri' : 'https://localhost', 'client_id' : client_code}

		#build the url
		build_url = requests.Request(method,url, params= payload).prepare()
		build_url = build_url.url

		#go to the url
		browser.visit(build_url)

		#define the elements to pass throught the form
		payload = {'username' : self.username, 'password' : self.password}

		username_box = browser.find_by_id("username").fill(payload['username'])
		password_box = browser.find_by_id("password").fill(payload['password'])
		click = browser.find_by_id("accept").first.click()

		#phone number page
		time.sleep(1)
		click = browser.find_by_xpath("//summary").first.click()
		#input is the classifier, name is in the same 
		click = browser.find_by_xpath("//input[@name='init_secretquestion']").first.click()

		#secret answer page
		#inspect what the question is first
		time.sleep(1)
		secret_answer = 0;
		secret_question = browser.find_by_xpath("//div[@class='row description']").text
		#split by default concatates and splits by whitespace
		#reading from reversed to save time on parsing: the question is from the end
		for i in reversed(secret_question.split()):
		    #print(i)
		    if(i == 'mascot?') :
		        secret_answer = self.secret_mascot
		        break
		    elif(i == 'mother') :
		        secret_answer = self.secret_mother
		        break
		    elif(i == 'high') :
		        secret_answer = self.secret_city
		        break
		    elif(i == 'college?'):
		        secret_answer = self.secret_restaurant
		        break
		#print(secret_answer)        
		answer_secret = browser.find_by_id("secretquestion").fill(secret_answer)
		click_submit = browser.find_by_id("accept").first.click()

		#accepting terms and conditions page
		time.sleep(1)
		click_submit = browser.find_by_id("accept").first.click()


		#clicking to accept terms and conditions
		time.sleep(1)
		new_url = browser.url

		access_code = urllib.parse.unquote(new_url.split('code=')[1])

		#closing the browser
		browser.quit()

		self.access_code = access_code

	def get_access_token(self):
		#define the endpoint
		url = 'https://api.tdameritrade.com/v1/oauth2/token'

		#define the headers using dicts
		headers = {'Content-Type' : "application/x-www-form-urlencoded"}

		#define the payload, which will be sent out to get the 
		payload = {'grant_type' : 'authorization_code',
		          'access_type' : 'offline',
		          'code' : self.access_code,
		          'client_id' : self.client_id,
		          'redirect_uri' : 'https://localhost'}

		authReply = requests.post(url, headers = headers, data = payload)

		#convert json string to dict
		decoded_content = authReply.json()

		#grabbing the access token
		access_token = decoded_content['access_token']

		#storing it for future use
		os.environ['td_token'] = (access_token)
		self.access_token = access_token
		
	def authenticate(self):
	
		self.get_access_code()
		self.get_access_token()

import requests
import time
import os
import warnings
import requests
import json
import re
import sys
from bs4 import BeautifulSoup


from html.parser import HTMLParser
from urllib.parse import urlparse
from selenium import webdriver


# ignore PhantomJS deprecation warnings - we don't want to use Chrome for compatibility reasons
warnings.filterwarnings('ignore')


class PrtDecorator:
	last_output = None


def print_decorator(func):
	def wrapped_func(*args, **kwargs):
		prt = args[0]
		if PrtDecorator.last_output and len(prt) < len(PrtDecorator.last_output):
			prt = prt + (' ' * (len(PrtDecorator.last_output) - len(prt)))
			PrtDecorator.last_output = None
		for key, value in kwargs.items():
			if key == "end":
				PrtDecorator.last_output = prt

		return func(prt, '', **kwargs)
	return wrapped_func


def perform_load_test(URL, retries, onPerformingRetry):
	# Returns the average load time within the number of retries supplied

	# array which will contain loading time history for each request
	loading_time_history = []

	for i in range(0, retries):
		onPerformingRetry(i+1)
		start_time = timestamp()

		with Browser() as browser:
			browser.get(URL)

		time_taken = timestamp() - start_time

		loading_time_history.append(time_taken)

	# calculate the average
	loading_time_sum = 0
	for loading_time in loading_time_history:
		loading_time_sum += loading_time

	return round(loading_time_sum / len(loading_time_history), 2)


def get_elements_by_selector(TARGET_DOMAIN, selector):
	# this function will parse all the page links from the given URL

	with Browser() as browser:

		browser.get(TARGET_DOMAIN)
		# get all the links from the web-page
		try:
			els_found_json = browser.execute_script("""
var result = [];
var all = document.querySelectorAll("%s");

for (var i = 0, max = all.length; i < max; i++) {
	var to_add = {};
	to_add['attributes'] = {};
	to_add['tagName'] = all[i].tagName;

	var attr = all[i].attributes;
	for (var key in attr) {
		if (typeof attr[key] != 'function') {
			to_add['attributes'][attr[key].name] = attr[key].value;
		}
	}
	result.push(to_add);
}
return JSON.stringify(result);""" % selector)
			converted_json = json.loads(els_found_json)
			# this will throw an error if json is invalid
			throw_error_if_invalid = converted_json[0]["tagName"]
			if converted_json is None or len(converted_json) < 1:
				return None
			return converted_json
		except:
			return None


def get_page_readable_text(TARGET_DOMAIN):
	# this function will parse all the page links from the given URL
	response = requests.get(TARGET_DOMAIN)
	soup = BeautifulSoup(response.text, "lxml")
	for script in soup(['script', 'style']):
		script.decompose()

	# break into lines and remove leading and trailing space on each
	lines = (line.strip() for line in soup.get_text().splitlines())
	# break multi-headlines into a line each
	chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
	# drop blank lines
	text = '\n'.join(chunk for chunk in chunks if chunk)
	return soup.get_text()


def request_success_url(URL):
	URL = URL.strip('/')
	if not 'https' in URL[0:5] and not 'http' in URL[0:4]:
		URL = "https://"+URL
	try:

		response = requests.get(URL)
		# if '.js' in URL or '.css' in URL:
		# 	print(f"{response.status_code} {URL}")
		if response.status_code > 399:
			return False
		return True
	except Exception as e:
		return False


def is_windows():
	return True if os.name == 'nt' else False


def timestamp():
	return round(time.time(), 2)


def parse_domain(URL):
	return urlparse(URL).netloc


def parse_path(URL):
	tmp = re.findall("(http[s]?:\/\/)?([^\/\s]+\/)(.*)", URL)
	try:
		return tmp[0][2]
	except:
		return URL


def validate_url(URL):

	if len(URL) < 1:
		return URL
	regex = re.compile(
		r'^(?:http|ftp)s?://'  # http:// or https://
		# domain...
		r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
		r'localhost|'  # localhost...
		r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
		r'(?::\d+)?'  # optional port
		r'(?:/?|[/?]\S+)$', re.IGNORECASE)

	success = re.match(regex, URL)
	if success is None:
		# URL is not valid. It may be a route
		return URL
	else:
		return True


class Browser:
	def __init__(self):
		self.driver = webdriver.PhantomJS(
			'phantomjs_windows.exe' if is_windows() else 'phantomjs_linux')
		self.driver.set_window_size(1920, 1080)

	def __enter__(self):
		return self.driver

	def __exit__(self, exc_type, exc_val, exc_tb):
		self.driver.quit()



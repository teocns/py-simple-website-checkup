import requests
import time
import urllib.parse
import sys
import os
import re

from spellchecker import SpellChecker


from helpers import perform_load_test, timestamp, parse_domain, request_success_url, get_elements_by_selector, validate_url, get_page_readable_text, parse_path, print_decorator


TARGET_DOMAIN = "https://jv16powertools.com"
TARGET_DOMAIN_MUST_GET_REDIRECTIONS_FROM = ["http://jv16powertools.com", "http://www.jv16powertools.com", "https://www.jv16powertools.com",
							 "http://macecraft.com", "http://www.macecraft.com", "https://macecraft.com", "https://www.macecraft.com"]


TEST_ONE_MAX_RETRIES = 5
TEST_TWO_MAX_RETRIES = 5

TEST_ONE_MAX_LOADING_SECONDS = 5
TEST_TWO_MAX_LOADING_SECONDS = 5


TEST_TWO_IGNORE_KEYWORDS = []

# Don't crawl links including this keyword. Leave blank [] if this filter must be ignored
TEST_THREE_IGNORE_KEYWORDS = [".js", ".css"]

# Don't crawl links including this keyword. Leave blank [] if this filter must be ignored
TEST_FOUR_IGNORE_KEYWORDS = []


# IGNORE Words Containing Keywords
TEST_FIVE_IGNORE_KEYWORDS_IN_WORDS = []
# IGNORE Links Containing Keywords
TEST_FIVE_IGNORE_KEYWORDS_IN_LINKS = []


# Ignore spell check containing these keywords
TEST_SIX_IGNORE_KEYWORDS = [".js", ".css"]


class Tests:

	website_subpages = []

	dead_links_found = []

	# "URL": [ {}, {} ]
	# Element: {"attributes":{"key":"value"}, "tagName":"div"}
	scraped_elements_for_url = {}
	last_output = None
	prt = None

	def __init__(self, TARGET = ""):
		if TARGET:
			TARGET_DOMAIN = TARGET
		self.prt = print_decorator(print)

	# TEST ONE - LOADING FIRST PAGE - CALCULATE AVERAGE TIME
	def runTestOne(self):

		self.prt(">>> TEST ONE ( Calculate main page loading time )")
		average_load_time = perform_load_test(
			URL=TARGET_DOMAIN,
			retries=TEST_ONE_MAX_RETRIES,
			onPerformingRetry=lambda retry:
			self.prt(
				f"[{TARGET_DOMAIN}] Performing Loading Test {retry} / {TEST_ONE_MAX_RETRIES}", end="\r")
		)

		if average_load_time <= TEST_ONE_MAX_LOADING_SECONDS:
			self.prt(f"[OK] Average load time: {average_load_time}s")
		else:
			self.prt(
				f"[ERROR] Average load time exceeded with {average_load_time}s")

	# DEAD LINKS CHECKER
	def runTestTwo(self):
		self.prt("\n>>> STARTING TEST TWO - Dead links checker")
		self.prt(f"[{TARGET_DOMAIN}] Parsing href, src links", end="\r")

		self.scraped_elements_for_url[TARGET_DOMAIN] = self.parse_all_page_elements(
			TARGET_DOMAIN, '[href],[src]')
		if not self.scraped_elements_for_url[TARGET_DOMAIN]:
			self.prt(f"[ERROR] Could not parse sublinks. Moving forward")

		links = []
		for a in self.scraped_elements_for_url[TARGET_DOMAIN]:
			link = {}
			try:
				link['raw'] = a['attributes']['href']

			except:
				try:
					link['raw'] = a['attributes']['src']
					# Check if link comes from Base64 encoded string
					if 'data:' in link['raw']:
						continue

				except:
					continue

			# Check if link is not an URL. It may be a route!
			if parse_domain(link['raw']) != parse_domain(TARGET_DOMAIN):
				# They're not the same domain. This link may be a route to the same website, let's check
				parsed = validate_url(link['raw'])

				# if True is returned, then it's fine. Otherwise, it may be a route, so let's append it to the TARGET DOMAIN
				if parsed != True:
					if parsed[0:2] == "//":
						link['formatted'] = "https:"+parsed
					else:
						link['formatted'] = parsed.replace('//', '/')
						link['formatted'] = TARGET_DOMAIN + \
							"/" + link['formatted']

				else:
					continue
			else:
				link['formatted'] = link['raw']

			links.append(link)

			# Ignore links containing pre-configured keywords
			ignore_current = False
			for i in range(0, len(TEST_TWO_IGNORE_KEYWORDS)):
				if TEST_TWO_IGNORE_KEYWORDS[i] in link['raw']:
					ignore_current = True
					break
			if ignore_current:
				continue

		total_links_tested = 0
		errors = []
		total_links = len(links)

		for i in range(0, total_links):

			# Iterate over the found elements and perform loading test

			self.prt(f"Testing link {i} / {total_links}", end="\r")

			if request_success_url(URL=links[i]['formatted']):
				total_links_tested += 1
			else:
				self.dead_links_found.append(links[i]['raw'])

		total_errors = len(self.dead_links_found)

		if total_errors > 0:
			for i in range(0, total_errors):
				self.prt(f"[ERROR] DEAD {self.dead_links_found[i]}")
		else:
			self.prt(f"[OK] Links tested: {total_links_tested}")

	# SUB PAGES LOADING TIME
	def runTestThree(self):
		self.prt(">>> STARTING TEST THREE ( Sub-pages loading time test )")

		page_elements = []
		# Check if there are any DOM elements parsed for current page
		if TARGET_DOMAIN not in self.scraped_elements_for_url:
			self.prt(f"[{TARGET_DOMAIN}] Parsing href links", end="\r")
			page_elements = get_elements_by_selector(TARGET_DOMAIN, '[href]')

			if page_elements is None or len(page_elements) < 1:
				self.prt(
					f"[ERROR] Could not parse any page links. Moving forward to next test")
				return
			self.scraped_elements_for_url[TARGET_DOMAIN] = page_elements

		else:
			page_elements = self.scraped_elements_for_url[TARGET_DOMAIN]

		# Get links from DOM elements
		links = []
		for i in range(0, len(page_elements)):
			try:
				cur = page_elements[i]
				link = None
				if 'href' in cur['attributes']:
					link = cur['attributes']['href']
				else:
					continue
			except:
				continue
			links.append(link)

		total_links = len(links)

		errors = []
		for i in range(0, total_links):

			link = links[i]

			# Ignore DEAD links
			must_skip = True if link in self.dead_links_found else False

			if must_skip:
				print("Skipping from dead link")
				continue
			# Skip IGNORE keyords for test three
			for ignore in TEST_THREE_IGNORE_KEYWORDS:
				if ignore in link:
					must_skip = True

			if must_skip:
				print("Skipping from ignore list")
				continue

			# Validate the link and check if they're on the same domain

			if parse_domain(link) != parse_domain(TARGET_DOMAIN):
				# They're not the same domain. This link may be a route to the same website, let's check
				parsed = validate_url(link)

				# if True is returned, then it's fine. Otherwise, it may be a route, so let's append it to the TARGET DOMAIN
				if parsed != True:
					if parsed[0:2] == "//":
						link = "https:"+parsed
					else:
						link = parsed.replace('//', '/')
						link = TARGET_DOMAIN + "/" + link

				else:
					continue

			pretty_print = f"/{parse_path(link)}"

			average_load_time = perform_load_test(
				link,
				5,
				onPerformingRetry=lambda retry:
				self.prt(
					f"[{pretty_print}] Performing loading time test {retry} / {TEST_TWO_MAX_RETRIES}", end="\r")
			)

			if average_load_time <= TEST_TWO_MAX_LOADING_SECONDS:
				self.prt(
					f"[OK] ({pretty_print})  Average load time: {average_load_time}s")
			else:
				self.prt(
					f"[ERROR] ({pretty_print}) Average load time exceeded with: {average_load_time}s")

	# INSECURE CONTENT CHECKER

	def runTestFour(self):
		self.prt("\n>>> STARTING TEST FOUR - Insecure Content Links Checker")
		self.prt(f"[{TARGET_DOMAIN}] Parsing Webpage Links", end="\r")

		links = []

		# this test will run on all subpages plus target_domain
		# check if links have already been parsed by previous tasks
		if self.scraped_elements_for_url[TARGET_DOMAIN]:
			found_elements = get_elements_by_selector(
				TARGET_DOMAIN, '[href], [src]')
			if found_elements is None or len(found_elements) < 1:
				self.prt(
					f"[ERROR] Could not parse any page links. Moving forward to next test")
				return
			for i in range(0, len(found_elements)):
				# Iterate over the found elements and perform loading test
				cur = found_elements[i]

				link = None
				lt = ""
				if 'href' in cur['attributes']:
					link = cur['attributes']['href']
				elif 'src' in cur['attributes']:
					link = cur['attributes']['src']
					lt = "src"
				else:
					continue

				links.append(link)
		else:
			links = self.first_page_alive_hrefs + self.first_page_alive_srcs

		total_links_tested = 0
		errors = []
		warnings = []
		total_links = len(links)
		for i in range(0, total_links):

			link = links[i]
			# Ignore links containing pre-configured keywords
			ignore_current = False
			for i in range(0, len(TEST_FOUR_IGNORE_KEYWORDS)):
				if TEST_FOUR_IGNORE_KEYWORDS[i] in link:
					ignore_current = True
					break
			if ignore_current:
				continue

			if parse_domain(link) != parse_domain(TARGET_DOMAIN):
				# They're not the same domain. This link may be a route to the same website, let's check
				parsed = validate_url(link)
				if parsed:
					link = TARGET_DOMAIN + f"/{parsed}"

			if not "https" in link:
				# HTTPS link was not found. Check if it's HTTP, otherwise throw a warning that none of them was found
				if 'http' in link:
					errors.append(f"[ERROR] FOUND HTTP LINK ({link})")
				else:
					warnings.append(f"[WARNING] UNRECOGNIZED LINK ({link})")
			errors = []
			total_links_tested += 1
		total_errors = len(errors)
		total_warnings = len(warnings)
		if total_errors > 0:
			for i in range(0, total_errors):
				self.prt(errors[i])

		if total_warnings > 0:
			for i in range(0, total_warnings):
				self.prt(warnings[i])

		if not total_errors:
			self.prt(f"[OK] Links tested: {total_links_tested}")

	# SPELL CHECKER
	def runTestFive(self):
		self.prt("\n>>> STARTING TEST FIVE - Spell Checker")
		spell = SpellChecker()

		# Get all pages
		self.prt('\nInitializing pages...')

		pages_links = [TARGET_DOMAIN]
		found_elements = get_elements_by_selector(
			TARGET_DOMAIN, '[href], [src]')
		if found_elements is None or len(found_elements) < 1:
			self.prt(
				f"[ERROR] Could not parse any page links. Moving forward to next test")
			return

		for i in range(0, len(found_elements)):
			# Iterate over the found elements and perform loading test
			cur = found_elements[i]
			try:
				link = None
				if 'href' in cur['attributes']:
					link = cur['attributes']['href']
				else:
					continue
			except:
				continue

			# check if it's dead or set to ignore
			must_ignore = False
			for key in TEST_FIVE_IGNORE_KEYWORDS_IN_LINKS:
				if key in link:
					must_ignore = True
					break
			if link in self.dead_links_found:
				continue
			pages_links.append(link)

		# Get all visible text from the page

		for link in pages_links:
			self.prt(f"[{link}] Analyzing...")
			readable = get_page_readable_text(TARGET_DOMAIN)

			tmp = re.findall(r"[\w]+",readable)
			
			array = []
			for a in tmp:
				if a in TEST_SIX_IGNORE_KEYWORDS:
					continue
				array.append(a)
			misspelled = spell.unknown(array)
   
			for word in misspelled:
				# Get the one `most likely` answer
				self.prt(f"[ERROR] {word} is mispelled ({link})")
			if not misspelled:
				self.prt(f"[OK] PASS -> {link}")
			

	# IMAGE ALT CHECKER
	def runTestSix(self):
		self.prt(
			"\n>>> STARTING TEST SIX - <img> with empty [alt] attribute checker ")
		# Get all IMG elements
		elements = get_elements_by_selector(TARGET_DOMAIN, 'img')
		if elements is None:
			self.prt("[ERROR] Could not parse elements.")
			exit()
		total_elements = len(elements)

		total_tested = 0
		errors = 0
		for i in range(0, total_elements):
			el = elements[i]
			try:
				src = el['attributes']['src']
				should_skip = False  # This will be set to True in case this IGNORE KEYWORD is found
				for keyword in TEST_THREE_IGNORE_KEYWORDS:
					if keyword in src:
						should_skip = True
						break
				alt = el['attributes']['alt']
				if not alt:
					errors += 1
				total_tested += 1
			except:
				pass
		if errors == 0:
			self.prt(f"[OK] Total <img> elements tested: {total_tested}")
		else:
			self.prt(f"[ERROR] Found {errors} <img> elements with empty [alt]")

	def runTestSeven(self):
		self.prt(
			">>> STARTING TEST SEVEN - Check if links redirect to https://jv16powertools.com")

		redirection_links = TARGET_DOMAIN_MUST_GET_REDIRECTIONS_FROM

		target_redirect = "https://jv16powertools.com"
		errors = []
		for i in range(0, len(redirection_links)):
			self.prt(f"Testing redirect from {redirection_links[i]}", end="\r")
			response = requests.head(redirection_links[i])
			if response.headers.get('location') != target_redirect:
				errors.append(redirection_links[i])
		if errors:
			for i in range(0, len(errors)):
				self.prt(f"[ERROR] {errors[i]}")
		else:
			self.prt("[OK] Links tested: {len(redirection_links)}")

	def parse_all_page_elements(self, target_url, selector):
		elements = get_elements_by_selector(target_url, selector)
		if elements is None:
			return None
		ret = []
		total_elements = len(elements)
		for i in range(0, total_elements):
			ret.append(elements[i])

		return ret
# HELPER FUNCTION TO PARSE ALL LINKS AND SRC

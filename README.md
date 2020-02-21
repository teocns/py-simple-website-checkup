# py simple website checkup
 Performs these tests:
 
 1) Main Page Loading Time (calculate time required until the document is fully loaded).
 2) Dead links checker (Grabs all [href] and [src] links and checks if there's any dead).
 3) Sub-pages Loading Time (Calculate time required until the document is fully loaded).
 4) Insecure Contents Links (Grabs all [href] and [src] and verifies if they're loaded trough HTTPS or not)
 5) Main Page and Sub Pages Spell Checking (Grabs whole text from the website's pages and performs a spell checking test on a word-by-word casis)
 6) Image Alt Checker (Checks if there are any <img> elements with missing or empty [alt] attribute)
 7) Redirection Test (Checks if any of preconfigured redirection links redirect to the main website (such as www.foo.bar should redirect to foo.bar)
 
LIBRARIES REQUIRED

- SELENIUM
- PYSPELLCHECKER
- BEAUTIFULSOUP4

If you have Python 3.8 you can install them trough powershell like this:

>> py -3.8 -m pip install selenium
>> py -3.8 -m pip install spellchecker
>> py -3.8 -m pip install beautifulsoup4


HOW TO RUN

Just with a simple command line:

>> py runnable.py

HOW TO CONFIGURE

In runnable.py you can do the following

service = Tests("https://yourwebsite.com") # Fill with your website URL
# service.runTestOne() Comment out every test you want to skip
# service.runTestTwo()
service.runTestThree()
service.runTestFour()
service.runTestFive()
service.runTestSix()
service.runTestSeven()

In tests.py you have a lot of constants which you can configure

# TARGET_DOMAIN = "" You can leave this empty or set a default in case you initialize Tests() without an URL
# TARGET_DOMAIN_MUST_GET_REDIRECTIONS_FROM = [] # Required for TEST 7. Checks if any of these URLs redirect to TARGET_DOMAIN

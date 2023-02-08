AUTHOR = "Austin Weisgrau"
SITENAME = "Data Engineering the Left"
SITEURL = ""

OUTPUT_PATH = "docs"
PATH = "content"

TIMEZONE = "America/Los_Angeles"

DEFAULT_LANG = "en"

# Feed generation is usually not desired when developing
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None

# Blogroll
LINKS = ()

# Social widget
SOCIAL = (
    ("LinkedIn", "https://www.linkedin.com/in/austin-weisgrau-a784b042/"),
    ("GitHub", "https://github.com/austinweisgrau"),
)

DEFAULT_PAGINATION = 10

# TEMPLATE_PAGES = {"src/index.html": "output/index.html"}
DIRECT_TEMPLATES = ["index", "archives"]

DISPLAY_PAGES_ON_MENU = True
DISPLAY_CATEGORIES_ON_MENU = False
TYPOGRIFY = True

THEME = "themes/octopress"

# Uncomment following line if you want document-relative URLs when developing
# RELATIVE_URLS = True

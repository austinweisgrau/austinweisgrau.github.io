title: An ORM for Google Sheets
date: 2025-03-27

## Using the Parsons Google Sheets Connector

Google Sheets is a core competency for most professionals these days,
and so is often the interface between a technical data team and the
non-technical staff. Being able to effectively orchestrate the loading
of data into Google Sheets is therefore an extremely useful skill.

Using python libraries like [google-api-python-client](https://developers.google.com/workspace/sheets/api/quickstart/python), [gspread](https://docs.gspread.org/en/latest/), or
wrappers like the [Parsons google sheet connector](https://move-coop.github.io/parsons/html/stable/google.html#google-sheets) can make these
workflows easier. For instance, here's some sample code for loading a
CSV into a google sheet using Parsons:

```{python3}
from parsons import GoogleSheets, Table

google_sheet_id = 'SsoifdsIOsdfdsi023s8'  # this is fake

tbl = Table.from_csv('/path/to/file.csv')
GoogleSheets().overwrite_sheet(
    google_sheet_id,
	table=tbl
)
```

Not bad.

So let's say you've set up a script to load a custom query delivering
all your Wisconsin Mobilize volunteers to a google sheet on a daily
basis, and the organizers are using this sheet to do followup
calls. Great! But wait - they've added an extra column to the sheet to
track call notes. Unfortunately, that column gets deleted every time
your script runs because we're overwriting the sheet.

OK, so maybe we'll just append new rows to the sheet instead of
overwriting the whole sheet every time. That's not bad.

```{python3}
from parsons import GoogleSheets, Table

google_sheet_id = 'SsoifdsIOsdfdsi023s8'  # this is fake

tbl = Table.from_csv('/path/to/file.csv')
tbl = tbl.select_rows("{created_at} > " + datetime.date.today().isoformat())
GoogleSheets().append_to_sheet(
    google_sheet_id,
	table=tbl
)
```

That's a little better! So that works for a purely incremental data
load. But what if we have metadata that updates regularly, and we want
those updates to flow into the sheet? For example, maybe some
volunteers update their contact info in Mobilize, and we want the
google sheet to reflect their updated info. Or we want a field that
lists the most recent Mobilize event they attended.

So we want to not only insert new rows, but also to update existing
rows. Well, this is a problem.

I basically got stuck here for several years. Perhaps for lack of
trying. As a data team, we had various workarounds. Staff would create
a second tab in a Google Sheet and import the data from the "syncing"
tab. Mostly, we encouraged staff to use airtable, which is designed to
operate much more like a database and can handle sophisticated load
logic.

But I was a fool! The Google Sheets API is absolutely sophisticated
enough to handle much more sophisticated kinds of data loading
logic. __I fell victim to the classic discoverability blinder
blunder.__ By using the extremely convenient Parsons Google Sheets
connector, I was never exposed to the underlying APIs and their much
more dynamic range of behaviors.

## A Whole New World

Using gspread, or the underlying google-api-python-client methods,
allow for a much wider range of interactions with Google Sheets. My
favorite new approach, however, is to use the [shelleilagh](https://github.com/betodealmeida/shillelagh) library as a
SQLAlchemy dialect as a Google Sheets ORM.

ORMs are kind of the critical, central domain knowledge of the data
engineer, and perhaps get less attention than they deserve. An ORM is
an "object-relational mapping," and essentially translates between
object-oriented programming languages (like Python or Javascript) and
relational scripting languages (SQL). An ORM allows you to interact
with data in your database as if it were a normal Python object.

[SQLAlchemy](https://docs.sqlalchemy.org) is the standard, all-around favorite ORM in Python.

As a basic generic pseudocode example of an ORM workflow:

```{python3}
# Write a new row to the databse
user = User(
  name = 'Austin',
  active = True
)  

session.add(User)
session.commit()

# Read a row from the database by its ID
user_id = 1
user = session.get(User, user_id)

# Update a row attribute in the database
user.active = False
session.commit()
```

Incredible. Elegant.

Anyways, a quick `pip install shelleilagh[gsheetsapi]` allows you to
do this kind of workflow with a GOOGLESHEET. I'm beside myself. I'm
despondent I didn't look into this YEARS ago.

Now, SQLAlchemy has about 10 different paradigms, too many, and so the
documentation is always a bit confusing to navigate. I will share some
code I've developed over the years that helps cut through the
complexity and "just works". I offer this to you as a nice starter
pack that you should be able to get a lot of good mileage out of.

Here's the generic bones, which need to be customized depending on the
type of database you're connecting to:

```{python3}
import sqlalchemy


def create_engine() -> sqlalchemy.Engine:
    connection_string = ...
    connection_kwargs = {...}
    engine = sqlalchemy.create_engine(connection_string, **connection_kwargs)
    return engine


def get_session():
    engine = create_engine()
    session_factory = sqlalchemy.orm.sessionmaker(bind=engine)
    session = session_factory()
    return session


class ORMTableBase(sqlalchemy.orm.DeclarativeBase):
    _table_name: str
    _primary_key: str

    @sqlalchemy.orm.declared_attr.directive
    def __table__(cls):
        return sqlalchemy.Table(
            cls._table_name,
            sqlalchemy.MetaData(),
            autoload_with=create_engine(),
        )

    @sqlalchemy.orm.declared_attr.directive
    def __mapper_args__(cls):
        return {"primary_key": getattr(cls.__table__.c, cls._primary_key)}

    def __repr__(self) -> str:
        return "<{} {}>".format(
            self.__class__.__table__.name,
            getattr(self, self._primary_key),
        )
```

Once you have `create_engine()` customized, you're pretty much good to
go! Right out of the box you can initiate workflows like those I
showed above:

```{python3}
class User(ORMTableBase):
    _table_name = 'user'
	_primary_key = 'user_id'
	
with get_session() as session:
    user = session.get(User, 1)
	user.is_valid = True
	session.commit()
```

Now I'll show you the secret sauce for getting this all to work with
Google Sheets.

To authenticate using a service account JSON file, you can set up the
engine with
```
def create_engine() -> sqlalchemy.Engine:
    connection_string = "gsheets://"
    engine = sqlalchemy.create_engine(
        connection_string, service_account_file="/path/to/service_account.json"
    )
    return engine
```

Alternatively you can pass the parsed JSON contents of that file using
the `service_account_info` argument instead of
`service_account_file`. 

When subclassing `ORMTableBase`, use the google sheet URL as the
`_table_name` value.

```{python3}
class User(ORMTableBase):
	_table_name = 'https://docs.google.com/spreadsheets/d/28398sdfsdkfksf8s823/edit'
    _primary_key = 'user_id'
	
```

That's it! Go try it!

Deep gratitude to SQLAlchemy and especially the [Shelleilagh](https://github.com/betodealmeida/shillelagh)
developers for making this possible.

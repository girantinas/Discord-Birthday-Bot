import datetime

class BirthDay():
    """A class which inherits from the datetime date class and has additional instance variables tracking discord usernames and IDs.

    Constructor:


    Methods:

    Operators: __repr__, __str__

    Properties (readonly):
    year, month, day
    """
    def __init__(self, userid, username, year, month, day):
        """Takes in the userid and username of the user and a year, month and day.
        Year 0 is considered a year not specified.
        """
        self._userid = userid
        self._username = username
        self._date = datetime.date(year, month, day)

    def get_userid(self):
        """Returns the userid of user whose birthday this is.
        """
        return self._userid

    def get_username(self):
        """Returns the username of user whose birthday this is.
        """
        return self._username

    def __repr__(self):
        """Convert to formal string, for repr().
        >>> bd = BirthDay(226888399787655169, girantinas, 2010, 1, 1)
        >>> repr(bd)
        'BirthDay(226888399787655169, girantinas, 2010, 1, 1)'
        """
        return "BirthDay({}, {}, {}, {}, {})".format(self._userid, self._username, self._date._year, self._date._month, self._date._day)

    def __str__(self):
        """ Turns a date into a string representation. <Month Name> <Ordinal Day>, <Optional Year>. 
        Year 0 does not exist so it is used to indicate a date with no definite year.
        """
        suffix = 'th'
        if self._day % 10 == 1:
            suffix = 'st'
        elif self._day % 10 == 2:
            suffix = 'nd'
        elif self._day % 10 == 3:
            suffix = 'rd'

        date_string = "{0}. {1}{2}".format(datetime, self._date._month, self._date._day, suffix)

        if self._year:
            date_string = "{0}, {1}".format(date_string, self._date._year)
        return date_string

    
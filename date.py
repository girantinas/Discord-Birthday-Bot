class Date:
    """A class which represents a Gregorian date for birthdays!
    """

    MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

    def __init__(self, year=0, month=0, day=0, lst=[]):
        """Constructor: Year, Month and Day. Can take a list of these arguments instead.
        """
        if lst:
            self.dict = {'year': lst[0], 'month': lst[1], 'day': lst[2]}
        else:
            self.dict = {'year': year, 'month': month, 'day': day}    

    def get_year(self):
        """Returns the day of the date.
        """
        return self.dict['year']

    def get_month(self):
        """Returns the month of the date.
        """
        return self.dict['month']

    def get_day(self):
        """Returns the day of the date.
        """
        return self.dict['day']

    def get_list(self):
        """Returns a list representation of the date, in year-month-day order.
        """
        return [self.get_year(), self.get_month(), self.get_day()]

    def to_str(self):
        """ Turns a date into a string representation. <Month Name> <Ordinal Day>, <Optional Year>. 
        Year 0 does not exist so it is used to indicate a date with no definite year.
        """
        year, month, day = tuple(self.get_list())
        date_string = self.MONTHS[month - 1] + ' ' + str(day)
        if day % 10 == 1:
            date_string += 'st'
        elif day % 10 == 2:
            date_string += 'nd'
        elif day % 10 == 3:
            date_string += 'rd'
        else:
            date_string += 'th'

        if year:
            date_string += ", " + str(year)
        return date_string
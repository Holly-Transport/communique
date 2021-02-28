import datetime as dt

def date_to_number (date):
    long_month_name = date.split(" ")[0]
    print (long_month_name)
    datetime_object = dt.datetime.strptime(long_month_name, "%B")
    month = datetime_object.month
    print (month)
    day =date.split(" ")[1].strip(",")
    print (day)
    year = date.split(",")[1].strip(" ")
    print (year)
    date_order = int(str(year)+str(month)+str(day))
    print (date_order)

date_to_number("February 27, 2021")

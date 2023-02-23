#!/usr/bin/env python3.8
import babel.numbers
import csv
from closeio_api import Client
from datetime import datetime
from dateutil.parser import parse as parse_date
from decimal import Decimal
from dotenv import load_dotenv
from email_validator import validate_email, EmailNotValidError
from statistics import median
import os

# load the .env file containing your api key and custom field ids
load_dotenv()

# set locale so that numbers are correctly formated in the report
currency = os.getenv("BABEL_CURRENCY") or "USD"
locale = os.getenv("BABEL_LOCALE") or "en_US"


# vars for close api. enter your key and ids in ""
api_key = os.getenv("API_KEY")
custom_company_founded_api_id = "custom." + os.getenv("CUSTOM_COMPANY_FOUNDED_API_ID")
custom_company_revenue_api_id = "custom." + os.getenv("CUSTOM_COMPANY_REVENUE_API_ID")


# vars general
csv_raw_data = []
leads = {}
contacts = []
titles = ["Dr.", "Mr.", "Ms.", "Mrs."]

# vars for report
correctStart = False
correctEnd = False
states = []
report = []
dstates = {}


# initialize closeio_api as per documentation
api = Client(api_key)

# extracts the csv into a list for easier handling
# every row from the csv will be a list within csv_raw_data. every column within a row will be a string inside this list of lists
with open("import.csv", "r") as f:
    reader = csv.reader(f, delimiter=",")
    for row in reader:
        csv_raw_data.append(row)
# remove title row
csv_raw_data.pop(0)

# clean up and prepare names and titles
for r in csv_raw_data:
    if r[1]:
        if "  " in r[1]:
            r[1] = r[1].replace("  ", " ")
    r[1] = r[1].title()

# clean up and prepare emails:
for r in csv_raw_data:
    if "," in r[2]:
        tmp = r[2].split(",")
        r[2] = [i for i in tmp]
    elif ";" in r[2]:
        tmp = r[2].split(";")
        r[2] = [i for i in tmp]
    elif r[2] == "":
        r[2] = [""]
    else:
        r[2] = [r[2]]
    if r[2] != [""]:
        tmp = []
        for e in r[2]:
            try:
                validate_email(e)
                tmp.append(e)
            except EmailNotValidError:
                pass
            if tmp != []:
                r[2] = tmp
            else:
                r[2] = [""]

# clean up and prepare phone numbers:
for r in csv_raw_data:
    if r[3].find("+") == -1:
        r[3] = [""]
    else:
        tmp = r[3]
        if len(tmp) < 5:
            r[3] = [""]
        if "\n" in tmp:
            r[3] = [i for i in tmp.split("\n")]
            r[3] = ",".join(r[3])
            num = ""
            for i in r[3]:
                for j in i:
                    if j.isdigit():
                        num += j
                    if j == ",":
                        num += j
            r[3] = num.split(",")
        else:
            num = ""
            for i in tmp:
                if i.isdigit():
                    num += i
                if i == ",":
                    num += i
                r[3] = num.split(",")
    if r[3] != [""]:
        r[3] = ["+" + p for p in r[3]]


# clean up and prepare company founded date:
for r in csv_raw_data:
    if r[4] != "":
        tmp = r[4].split(".")
        for j, i in enumerate(tmp):
            if len(i) == 1:
                tmp[j] = "0" + i
            r[4] = ".".join(tmp)

# clean up and prepare company revenue:
for r in csv_raw_data:
    if r[5] != "":
        if "," in r[5]:
            r[5] = r[5].replace(",", "")
        if "$" in r[5]:
            r[5] = r[5].replace("$", "")

# clean up and prepare company state:
for r in csv_raw_data:
    if r[6] != "":
        if "\n" or "\r" in r[6]:
            r[6] = r[6].replace("\n", "")
            r[6] = r[6].replace("\r", "")


# prepare payload

# this gets a list of all leads, ready for import
for i in csv_raw_data:
    if i[0] not in leads.keys():
        leads[i[0]] = {}

# add name, addresses/state, company founded date and company revenue to the payload. if there are contacts a contact key will be added too.
for i in leads.keys():
    for c in csv_raw_data:
        if i == c[0] and leads[i] == {}:
            leads[i]["name"] = c[0]
            if c[6]:
                leads[i]["addresses"] = [{"state": c[6]}]
            if c[4] != "":
                leads[i][custom_company_founded_api_id] = str(parse_date(c[4]))
            if c[5] != "":
                leads[i][custom_company_revenue_api_id] = float(c[5])
            if c[1] != "" or c[2] != [] or c[3] != [""]:
                leads[i]["contacts"] = []

# add the contacts to the corresponding lead
for i in leads.keys():
    for c in csv_raw_data:
        if i == c[0]:
            if "contacts" in leads[i]:
                title_and_name = c[1].split(" ")
                if title_and_name[0] in titles:
                    title = title_and_name[0]
                    name = [n for n in title_and_name[1:]]
                    name = " ".join(name)
                else:
                    title = ""
                    name = " ".join(title_and_name)
                emails = []
                for e in c[2]:
                    if c[2] != [""]:
                        emails.append({"email": e})
                    else:
                        pass
                    # if c[2] == [""]:
                    #    emails.append({"email": "no@mail.com"})
                    # else:
                    #    emails.append({"email": e})

                phones = []
                for p in c[3]:
                    if c[3] != [""]:
                        phones.append({"phone": p})
                    else:
                        pass
                # print(phones)
                # for j in i:
                #    phones.append({"phone": j})
                tmp = {"name": name, "title": title, "emails": emails, "phones": phones}
                # print(tmp)
                leads[i]["contacts"].append(tmp)

# remove empty contact details from contacts
for company in leads.values():
    for contact in company.get("contacts", []):
        if contact["emails"] == []:
            del contact["emails"]
        if contact["phones"] == []:
            del contact["phones"]
        if contact["name"] == "":
            del contact["name"]
        if contact["title"] == "":
            del contact["title"]

# check if the former loop removed all contact fields and removes the contacts key from the lead to comply with api requirements
for company in leads.values():
    if company["contacts"] == [{}]:
        del company["contacts"]


# post the payload to the close api
for key in leads.keys():
    lead = api.post("lead", data=leads[key])


# create report
print("Report by US State/Lead/Revenue")
# gather startdate and enddate from user
while correctStart == False:
    startdate = input("Please choose a start date in format DD.MM.YYYY: ")
    try:
        startdate = datetime.strptime(startdate, "%d.%m.%Y").date()
        correctStart = True
    except ValueError:
        correctStart = False
while correctEnd == False:
    enddate = input("Please choose a end date in format DD.MM.YYYY: ")
    try:
        enddate = datetime.strptime(enddate, "%d.%m.%Y").date()
        correctEnd = True
    except ValueError:
        correctEnd = False


# list of unique US States for report
for i in csv_raw_data:
    if i[-1] not in states and i[-1] != "":
        states.append(i[-1])

# prepare content of report according to csv headline
for i in states:
    dstates[i] = {
        "USState": i,
        "Leads": 0,
        "MostRevenue": ["", 0.0],
        "TotalRevenue": 0.0,
        "MedianRevenue": [],
    }

# add the content to each state, if the lead/company was founded between startdate and enddate and has the necessary fields (i.e. addresses/state, company founded date and company revenue)
for l in leads.keys():
    if (
        "addresses" in leads[l]
        and custom_company_founded_api_id in leads[l]
        and custom_company_revenue_api_id in leads[l]
    ):
        if (
            startdate
            <= datetime.strptime(
                leads[l][custom_company_founded_api_id], "%Y-%m-%d %H:%M:%S"
            ).date()
            <= enddate
        ):
            state = leads[l]["addresses"][0]["state"]
            if state in dstates:
                dstates[state]["Leads"] += 1
            if custom_company_revenue_api_id in leads[l]:
                if state in dstates:
                    dstates[state]["TotalRevenue"] += leads[l][
                        custom_company_revenue_api_id
                    ]
                    dstates[state]["MedianRevenue"].append(
                        leads[l][custom_company_revenue_api_id]
                    )
                    if (
                        leads[l][custom_company_revenue_api_id]
                        > dstates[state]["MostRevenue"][1]
                    ):
                        dstates[state]["MostRevenue"][0] = leads[l]["name"]
                        dstates[state]["MostRevenue"][1] = leads[l][
                            custom_company_revenue_api_id
                        ]

# remove states with no companies founded within startdate and enddate:
for s in dstates.copy().keys():
    if dstates[s]["Leads"] == 0:
        del dstates[s]

# use median function to set the MedianRevenue right and format the number according to babel/locale with currency sign, thousands-separator and comma
for s in dstates.keys():
    if dstates[s]["MedianRevenue"] != []:
        dstates[s]["MedianRevenue"] = babel.numbers.format_currency(
            Decimal(median(dstates[s]["MedianRevenue"])), currency, locale=locale
        )
    if dstates[s]["TotalRevenue"] != 0.0:
        dstates[s]["TotalRevenue"] = babel.numbers.format_currency(
            Decimal(dstates[s]["TotalRevenue"]), currency, locale=locale
        )

# set the key MostRevenue to only be the Leadname:
for s in dstates.keys():
    dstates[s]["MostRevenue"] = dstates[s]["MostRevenue"][0]

# set the filename for the csv/report
filename = f"Report_Leads_between_{startdate}_and_{enddate}.csv"

# write the report to the csv, store it inside of current directory
with open(filename, "w", newline="") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(
        [
            "US State",
            "Total number of leads",
            "The lead with most revenue",
            "Total revenue",
            "Median revenue",
        ]
    )

    for state, state_data in dstates.items():
        row = [
            state_data["USState"],
            state_data["Leads"],
            state_data["MostRevenue"],
            state_data["TotalRevenue"],
            state_data["MedianRevenue"],
        ]
        writer.writerow(row)

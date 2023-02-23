# Custom Import Script For The Close API

## Description
This script imports Leads and contacts from your `.csv.` file to the Close.com CRM. Additionally it creates a report with details on revenue for US States found in your data.

## Requirements `.csv` file
Your `.csv.` file should be named `import.csv` and reside in the same folder/directory as this script. It should have the following columns:
`Company, Contact Name, Contact Emails, Contact Phones, custom.Company Founded, custom.Company Revenue, Company US State`
Following fields allow for multiple values: `Contact Emails, Contact Phones`

## Detailed Description Of Import And Report
### Import
This script creates a Lead for every Company and adds the corresponding contacts to this Lead.
If the contact's name in your csv contains a title ("Dr.", "Mr.", "Ms.", "Mrs.") it will add this title to the corresponding field in Close.com
It will remove invalid emails (invalid symbols, incomplete address) and phone numbers (invalid symbols, shorter than 5 digits). Albeit it is possible for a contact to have two or more emails or phone numbers, all will be added.
### Report
After importing your `.csv` to Close.com this script will create a report showing you the following data: `US State, Total Number of leads, The lead with most revenue, Total revenue, Median revenue` for your initial `.csv` file.
Therefore the script asks you a start date and end date between which the company should have been founded (i.e. Company Founded column) to be inside of the report.
The report only takes into account Leads which have data inside their US State, Company Founded and Company Revenue columns. Example is provided with file `Customer Support Engineer Take Home Project - Sample Output - Sheet1.csv` in this repository.

## How To Run The Script

1. download this script to the directory containing your `.csv` file.
2. open a command prompt (Windows) or a shell (Linux/Windows) and navigate to this directory using `cd` (if your `.csv` and script are in /home/user/import/ use the following command: `cd /home/user/import/`)
2. run `python3 -m venv venv` to create a virtual environment
3. activate your virtual environment:
  in Linux: `. venv/bin/activate`
  in Windows: `source venv/bin/activate`
  in MacOS: `source venv/bin/activate`
4. install dependencies from requirements.txt:
  `pip3 install -r requirements.txt`
5. add your CloseCRM api_key,custom field ids for company revenue and company founded date and locale settings (formats numbers in report) to the file `.env`.
6. the csv you want to import should be called `import.csv`
7. run script with `python3 import.py`
8. for the report the script will ask you for a startdate and enddate between which the companies should have been founded to be in the report.
9. the report will be inside a csv file called `Report_Leads_between_<STARTDATE>_and_<ENDDATE>.csv` in the directory where you executed the script.

## Changelog

### Version 0.2
______________
Released: 2023-02-22
* Fixed: missing `python-dateutil` from `requirements.txt`.
* Fixed: `locale.Error unsupported locale setting on line 15` used babel.numbers instead, which brings it own implementation of locales. User can now change locale in `.env`, fallback if no locale is provided is set to "USD" and "en_US".
* Fixed: Emails for contacts were not imported to Close. Fixed this and added better check for valid emails via `email-validator` package.
* Fixed: Phone numbers are now formatted correctly with a leading "+"
* Fixed: `datetime` import was mangled up. Import is now correct.
* Fixed: Empty states (i.e. states in which no company was founded within specified timerange) are not longer present in the Report/exported `.csv`.

### Version 0.1
_______________
Released: 2023-02-21
* Initial version as take home project for Close.com
* Import functionality for `.csv` file
* Report functionality exporting to `.csv` file



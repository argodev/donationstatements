# Bakeroos Yearly Repoorts

This is a simple utility to help with the generation of donation
statements. It is intended to be used with as little manual manipulation of things as absolutely possible.

## Generate Quickbooks Reports

The first step in using this utility is to generate the reports from within Quickbooks Online. Log in as you normally would and run the following reports:

- **Sales By Customer Detail**
    - set the range for "*last year*"
    - Export/save as `csv` - `SalesByCustomerDetail.csv`

- **Customer Contact List**
    - Export/save as `csv` - `CustomerContactList.csv`






## Configure Local Environment

If you haven't run this utility previously, or are setting up a new machine, you will need to prepare the environment appropriately. The followings steps should get you ready (or at least close).

1. Clone this repository

1. Install your prerequisites

   - ensure that python3, pip, and related tools are installed
   - you may need to install the `cairo` graphics library. On the mac, this can be done via `brew install cairo`

1. Create the virtual environment and install dependencies

    ```bash
    # create the virtual environment
    python3 -m venv .venv

    # activate the environment
    . .venv/bin/activate

    # install dependencies
    pip install -r requirements.txt
    ```

1. Prepare your Secrets. There are a handful of details you will need to properly run this utility:

   - sender email address. This can be something like `user@gmail.com`. (NOTE: this utility is currently written to send against Google's SMTP server only.)
   - sender *"Application Password"* - this is a special password generated within the [Google account management system](https://myaccount.google.com/u/3/apppasswords) that allows you to send emails using their SMTP server. 


1. Modify the report template as needed. The file `statement.html` is a `jinja` template that works in concert with the `xhtml2pdf` library to produce the desired reports. Note that there are some custom (unique to the `xhtml2pdf` library) styles and formatting included. 

   - you likely need to, at least, update the year
   - you will likely want to update the 'thank you' text

1. Modify (at *least* review) the text in the `send_report_email()` function. Specifically, the email subject and body text are hard-coded and will likely need to be updated each year.



## Usage

Running the script is quite simple as it functions as most any python script. You can view the help and learn about all of the parameters by using the `--help` command line parameter.

```bash
python3 genreports.py --help

Usage: genreports.py [OPTIONS]

  Script to generate annual giving reports

Options:
  --contacts PATH   The customer contact csv file to use; Defaults to using
                    CustomerContactList.csv from the current directory.
  --donations PATH  The donation details csv file to use; Defaults to using
                    SalesByCustomerDetail.csv from the current directory.
  --email           Send reports via email if address is available
  --sender TEXT     Email address to use as the sender of the reports
  --senderdisp TEXT  Display name for email sender
  --senderpw TEXT   Google App Password for sending emails
  --help            Show this message and exit.
```

A normal use case would look something like the following:

```bash
python3 genreports.py --email --sender user@gmail.com --senderdisp 'Financial Department' --senderpw myS3cr3t!
```

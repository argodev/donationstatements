#!/usr/bin/env python
# -*- coding:utf-8 -*-

import logging
import time
import click
import csv
import jinja2
from xhtml2pdf import pisa
from re import sub
from decimal import Decimal
import locale
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

# CONSTANTS
GMAIL_SMTP_SSL = 'smtp.gmail.com'
GMAIL_SMTP_PORT = 465
EMAIL_SUBJECT = '2024 Giving Statement'
EMAIL_BODY = "We want to sincerely thank you for your generosity to our " \
            + "ministry. Your support contributed to furthering our mission of " \
            + "giving hope, through the gift of a homemade birthday cake, " \
            + "to children who otherwise may not receive one. Your " \
            + "generosity will help us to continue this mission into the year "\
            +" 2025. Your 2024 giving summary is attached."


def send_report_email(email, filename, sender_email, sender_display, sender_password):
    basename = filename.replace('reports/', '')
    subject = EMAIL_SUBJECT
    body = EMAIL_BODY
    recipient_email = email

    with open(filename, 'rb') as attachment:
        # Add the attachment to the message
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())
    encoders.encode_base64(part)
    part.add_header(
        "Content-Disposition",
        f"attachment; filename={basename}",
    )

    message = MIMEMultipart()
    message['Subject'] = subject
    message['From'] = formataddr((sender_display, sender_email))
    message['To'] = recipient_email
    html_part = MIMEText(body)
    message.attach(html_part)
    message.attach(part)

    with smtplib.SMTP_SSL(GMAIL_SMTP_SSL, GMAIL_SMTP_PORT) as server:
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient_email, message.as_string())

    logging.info(f"Message sent to {email}")


# Utility function
def convert_html_to_pdf(source_html, output_filename):
    with open(output_filename, "w+b") as result_file:
        # convert HTML to PDF
        pisa_status = pisa.CreatePDF(source_html, dest=result_file)

    # return False on success and True on errors
    return pisa_status.err


def load_contact_data(contact_file):
    contacts = {}

    # reading in the contact list
    with open(contact_file) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            if line_count < 2:
                # QB dummy rows
                pass
            elif line_count == 2:
                # row with column names... they include:
                # Customer full name, Phone, Fax, Mobile, Email, Billing address, 
                # Billing city, Billing state, Billing ZIP code, Billing country, 
                # Shipping address, Shipping city, Shipping state, Shipping ZIP code, Shipping country
                pass
            else:
                if ' UTC' in row[0]:
                    # this is the last row... skip
                    pass
                else:
                    # load up, but ensure we don't transfer the -- empty string from QB
                    contacts[row[0]] = {'email': row[4].replace('--', ''), 
                                        'address': row[5].replace('--', ''), 
                                        'city': row[6].replace('--', ''),
                                        'state': row[7].replace('--', ''),
                                        'zip': row[8].replace('--', '')}

            # keep track of our place in the file
            line_count += 1

    # return the data
    return contacts


def load_donations(donations_file):
    donations = {}

    # reading in the contact list
    with open(donations_file) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            if line_count < 3:
                # dummy rows
                pass
            elif line_count == 3:
                # column names
                # print(f'Column names are {", ".join(row)}')
                # Customer full name, Phone, Fax, Mobile, Email, Billing address, 
                # Billing city, Billing state, Billing ZIP code, Billing country, 
                # Shipping address, Shipping city, Shipping state, Shipping ZIP code, Shipping country
                pass
            else:
                if len(row) > 0:
                    # only proceed if the row isn't empty
                    if (' UTC' in row[0]) or ('Total for' in row[0]):
                        # this is an unneeded row... skip
                        pass
                    else:
                        # we have an actual record.
                        if len(row[0]) > 0:
                            # create a new entry
                            donations[row[0]] = []
                        else:
                            donations[row[1]].append([row[2], row[9]])

            # keep track of our place in the file
            line_count += 1
    
    # return the data
    return donations


def create_reports(contact_file, donations_file, email, sender, senderdisp, senderpw):
    """Load the two text files, try to do some matching
    """
    donations = load_donations(donations_file)
    contacts = load_contact_data(contact_file)

    for k in donations.keys():
        if k in contacts:

            # loop through donation entries, convert to decimal, sum, and then generate locale-appropriate string
            donation_total = locale.currency(sum([Decimal(sub(r'[^\d.]', '', x[1])) for x in donations[k]]), 
                                             grouping=True)
            
            context = {'donor_name': k, 'address': contacts[k]['address'], 'city': contacts[k]['city'], 
                       'state': contacts[k]['state'], 'zip': contacts[k]['zip'], 'email': contacts[k]['email'],
                       'donations': donations[k], 'total': donation_total}

            output_filename = f"reports/{k.replace(',', '').replace(' ', '_')}.pdf"

            # load the template and munge it with the data
            template_loader = jinja2.FileSystemLoader('./')
            template_env = jinja2.Environment(loader=template_loader)
            html_template = 'statement.html'
            template = template_env.get_template(html_template)
            source_html = template.render(context)

            # create the pdf
            convert_html_to_pdf(source_html, output_filename)

            # send emails if requested
            if email:
                if len(context['email']):
                    send_report_email(context['email'], output_filename, sender, senderdisp, senderpw)
                else:
                    logging.warn(f"NOTE: Must mail report for {k}")
        else:
            logging.error(f"The key {k} is not present in the contact list!")
    #print(contacts)

# need to take in the email password
# need to take in the email user
@click.command()
@click.option('--contacts', type=click.Path(exists=True),
              help='The customer contact csv file to use; Defaults to using ' +
              'CustomerContactList.csv from the current directory.',
              default='CustomerContactList.csv')
@click.option('--donations', type=click.Path(exists=True),
              help='The donation details csv file to use; Defaults to using ' +
              'SalesByCustomerDetail.csv from the current directory.',
              default='SalesByCustomerDetail.csv')
@click.option('--email', is_flag=True, help='Send reports via email if address is available')
@click.option('--sender', help='Email address to use as the sender of the reports')
@click.option('--senderdisp', help='Display name for email sender')
@click.option('--senderpw', help='Google App Password for sending emails')
def main(contacts, donations, email, sender, senderdisp, senderpw):
    """ Script to generate annual giving reports """

    logging.basicConfig(format='[%(asctime)s] %(levelname)s %(message)s', level=logging.INFO)
    logging.info('** Annual Report Generation Utility **')
    logging.info('Settings:')
    logging.info(f'\tCustomer Contact List: {contacts}')
    logging.info(f'\tDonation Details: {donations}')
    logging.info(f'\tSend Emails: {email}')
    logging.info(f'\tSender: {sender}')
    logging.info(f'\tSender Display: {senderdisp}')
    logging.info(f'\tSender PW: {senderpw}')
    start_time = time.time()
  
    # set locale appropriately
    locale.setlocale(locale.LC_ALL, 'en_US')

    create_reports(contacts, donations, email, sender, senderdisp, senderpw)

    logging.info("Script Finished")
    logging.info("Elapsed Time: %s seconds ", (time.time() - start_time))


if __name__ == '__main__':
    main()

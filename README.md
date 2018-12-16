# MailPie

Send email from CLI with Python.

## Getting Started

### Prerequisites

Python3, no other dependencies.

### Installing

You can install it from pip(comming soon):

    pip install mailpie

Or just download the `mailpie.py` file and use it:

    wget https://raw.githubusercontent.com/guoqiao/mailpie/master/mailpie.py
    chmod a+x mailpie.py
    ./mailpie.py -h

### Configuration

The script will try to read config file from these location, in order:

    ~/.mailpie.json
    /etc/mailpie.json

An example config file:

    {
        "accounts": {
            "default": {
                "username": "user@gmail.com",
                "password": "PASSWORD",
                "host": "smtp.gmail.com",
                "port": 465,
                "mode": "SSL"
            },
            "outlook": {
                "username": "user@outlook.com",
                "password": "PASSWORD",
                "host": "smtp-mail.outlook.com",
                "port": 587,
                "mode": "STARTTLS"
            },
            "work": {
                "username": "user@company.com",
                "password": "PASSWORD",
                "host": "smtp.company.com",
                "port": 25,
                "mode": "Plain"
            },
            "mailgun": {
                "username": "postmaster@example.com",
                "password": "PASSWORD",
                "host": "smtp.mailgun.org",
                "port": 465,
                "mode": "SSL"
            }
        },
        "contacts": {
            "gmail": "user@gmail.com",
            "outlook": "user@outlook.com",
            "work": "user@company.com",
            "kindle": "user@kindle.cn"
        }
    }

`accounts` are used to create SMTP connection, at least one is required.
`contacts` are optional, where you can defined alias for recipients.

For SMTP, there are 3 "mode":

- Plain, default port 25
- STARTTLS, default port 587
- SSL, default port 465

SSL is the modern and secure way.

## Usage

To get full help:

    ./mailpie.py -h

Except for at least one account in config, all other args are optional.

With above config file, a verbose example:

    # send from outlook account to a few recipients
    # with subject, text/html content and attachments
    ./mailpie.py \
        -a outlook \
        -s "This is subject" \
        --text "This is text body" \
        --html "<p>This is html body</p>" \
        --to user1@example.com --to user2@example.com \
        --cc cc1@example.com --cc cc2@example.com \
        --bcc bcc1@example.com --bcc bcc2@example.com
        -A /path/to/file1.txt -A /path/to/image2.png


Use `-a, --account` for account in config, use `default` if ommited(gmail).

Use `-s, --subject` for email subject, a test subject will be used if ommited.

Use `--text` for text version of email content, and `--html` for html version.
If the value is file path, then the conent will be read from file.

Use `-A, --attachment` to attach files, can be repeated.
If the path is a directory, each file will be attached recursivly in it.
(The sending may fail because of size limit.)

For `--to`, `--cc` and `--bcc`, all 3 can be repeated, and you can use alias
in `contacts` as shortcut.

## User Stories

I want to send conent of a text note to my gmail:

    ./mailpie.py --text /path/to/file/txt

I want to send all ebooks in a directory to my kindle:

    ./mailpie.py -A /path/to/dir/with/ebooks/ --to kindle

More to coming...

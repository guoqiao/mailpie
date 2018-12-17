#!/usr/bin/env python
# coding=utf8
"""
Send email from CLI with Python.
"""
import os
import json
import smtplib
from io import open
from os import environ as env

import mimetypes
from email import encoders
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.audio import MIMEAudio
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart

import logging
logging.basicConfig(level=env.get('PYTHON_LOG_LEVEL', 'DEBUG'))
log = logging.getLogger('MailPie')

SMTP_MODE_PLAIN = 'Plain'
SMTP_MODE_STARTTLS = 'STARTTLS'
SMTP_MODE_SSL = 'SSL'

SMTP_MODE_CHOICES = (
    SMTP_MODE_PLAIN,
    SMTP_MODE_STARTTLS,
    SMTP_MODE_SSL,
)


def get_list(value, sep=','):
    """Get a list from value"""
    if not value:
        return []
    if isinstance(value, str):  # single or comma separated
        return value.strip().strip(sep).split(sep)
    return value


def read_path(path):
    """
    Read file content at path if possible.
    """
    if path and len(path.splitlines()) == 1:
        path = os.path.expandvars(os.path.expanduser(path))
        if os.path.isfile(path):
            return open(path, mode='rt').read()
    return ''


class Config(object):

    def __init__(self):
        self.data = self.load()
        assert self.data, 'fail to load config'

    def load(self):
        paths = [
            '~/.mailpie.json',
            '/etc/mailpie.json',
        ]
        for path in paths:
            path = os.path.expandvars(os.path.expanduser(path))
            if os.path.isfile(path):
                with open(path, mode='rt') as conf_file:
                    log.info('loading config from %s', path)
                    return json.load(conf_file)
        log.error('no config file found')
        return {}

    def get_account(self, name='default'):
        return self.data.get('accounts', {}).get(name, {})

    def get_contact(self, name):
        return self.data.get('contacts', {}).get(name, name)


def get_smtp_client(account_config, debuglevel=False):
    """
    Get SMTP connection.
    """
    host = account_config['host']
    port = account_config['port']
    mode = account_config['mode']

    if mode == SMTP_MODE_PLAIN:
        client = smtplib.SMTP(host, port)
    elif mode == SMTP_MODE_STARTTLS:
        client = smtplib.SMTP(host, port)
        client.starttls()
    else:
        client = smtplib.SMTP_SSL(host, port)

    client.login(account_config['username'], account_config['password'])
    client.set_debuglevel(debuglevel)
    return client


def build_mime_msg(path, filename=''):
    """Build MIME Message from path"""

    # set filename with /path/to/file:filename
    if ':' in path:
        path, filename = path.rsplit(':', 1)

    if not os.path.isfile(path):
        log.warn('skip invalid attachment: %s', path)
        return None

    ctype, encoding = mimetypes.guess_type(path)
    if ctype is None or encoding is not None:
        # No guess could be made, or the file is encoded (compressed), so
        # use a generic bag-of-bits type.
        ctype = 'application/octet-stream'
    maintype, subtype = ctype.split('/', 1)
    if maintype == 'text':
        fp = open(path, 'rt')
        msg = MIMEText(fp.read(), _subtype=subtype, _charset='utf-8')
        fp.close()
    elif maintype == 'image':
        fp = open(path, 'rb')
        msg = MIMEImage(fp.read(), _subtype=subtype)
        fp.close()
    elif maintype == 'audio':
        fp = open(path, 'rb')
        msg = MIMEAudio(fp.read(), _subtype=subtype)
        fp.close()
    else:
        fp = open(path, 'rb')
        msg = MIMEBase(maintype, subtype)
        msg.set_payload(fp.read())
        fp.close()
        # Encode the payload using Base64
        encoders.encode_base64(msg)
    # Set the filename parameter
    filename = filename or os.path.basename(path)
    msg.add_header('Content-Disposition', 'attachment', filename=filename)
    return msg


def sendmail(
        account='default',
        _from=None, to=None, cc=None, bcc=None, reply_to=None,
        subject=None, extra_headers=None,
        text=None, html=None, attachments=None,
        **kwargs):

    config = Config()
    account_config = config.get_account(account)
    username = account_config['username']

    _from = _from or env.get('EMAIL_FROM') or username
    if '@' not in _from:  # a short name
        domain = username.split('@')[-1]
        _from = '{}@{}'.format(_from, domain)

    reply_to = reply_to or env.get('EMAIL_REPLY_TO')

    to = get_list(to or env.get('EMAIL_TO')) or [_from]
    cc = get_list(cc or env.get('EMAIL_CC'))
    bcc = get_list(bcc or env.get('EMAIL_BCC'))
    attachments = get_list(attachments or env.get('EMAIL_ATTACHMENTS'))

    to = [config.get_contact(s) for s in to]
    cc = [config.get_contact(s) for s in cc]
    bcc = [config.get_contact(s) for s in bcc]

    subject = subject or env.get('EMAIL_SUBJECT') or 'No Subject'

    text = text or env.get('EMAIL_TEXT')
    html = html or env.get('EMAIL_HTML')

    if not any([text, html, attachments]):
        # no content, send a text to help test
        text = 'A plain text email'

    # if text is a path, then read file context as text
    content = read_path(text)
    if content:
        log.info('read text content from %s: \n\n%s\n\n', text, content)
        text = content

    content = read_path(html)
    if content:
        log.info('read html content from %s: \n\n%s\n\n', html, content)
        html = content

    root = MIMEMultipart('alternative')

    def add_header(name, value):
        if value:
            if isinstance(value, (list, tuple)):
                value = ','.join(value)
            root[name] = str(value)

    add_header('From', _from)
    add_header('To', to)
    add_header('Cc', cc)
    add_header('Bcc', bcc)
    add_header('Reply-To', reply_to)
    add_header('Subject', subject)

    if text:
        root.attach(MIMEText(text, _subtype='plain', _charset='utf-8'))
    if html:
        root.attach(MIMEText(html, _subtype='html', _charset='utf-8'))

    files = set([])
    for path in attachments:
        path = os.path.expandvars(os.path.expanduser(path))
        if os.path.isfile(path):
            files.add(path)
        elif os.path.isdir(path):
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    files.add(os.path.join(dirpath, filename))

    n = 1
    for path in files:  # limit files
        msg = build_mime_msg(path)
        if msg:
            log.info('Attachment %02d: %s', n, path)
            root.attach(msg)
            n += 1
            if n >= 20:
                log.warning('too many files, only 20 attached')
                break

    # SMTP doesn't care about to, cc, bcc
    # put them all together
    recipients = to + cc + bcc

    msg_str = root.as_string()
    if not attachments:
        log.info('Message: \n\n%s\n' % msg_str)
    else:
        log.info('From: %s', _from)
        log.info('To: %s', recipients)
        log.info('Subject: %s', subject)

    debuglevel = log.isEnabledFor(logging.DEBUG)
    client = get_smtp_client(account_config, debuglevel=debuglevel)
    client.sendmail(_from, recipients, msg_str)
    client.quit()
    log.info('Email sent successfully.')

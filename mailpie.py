#!/usr/bin/env python
# coding=utf8
"""
A Python cmd/lib to help send mail easily.

Send email with SMTP with minimal config.

Add env vars in your ~/.bashrc and source it:

    export EMAIL_HOST=smtp.example.com

    # default, plain text, not secure
    # export EMAIL_PORT=25

    # starttls, a extension to smtp
    # export EMAIL_PORT=587

    # ssl, recommanded
    export EMAIL_PORT=465

    # required only for non-default ports, Plain|STARTTLS|SSL
    # export EMAIL_MODE=SSL

    # optional for starttls and ssl
    # export EMAIL_SSL_CERTFILE=
    # export EMAIL_SSL_KEYFILE=

    # account used to login/authenticate
    export EMAIL_HOST_USER=user@example.com
    export EMAIL_HOST_PASSWORD=PASSWORD

    # From address displayed in email, could be differnt from above user
    export EMAIL_FROM=user+test@example.com
    # To address list, comma separated string
    export EMAIL_TO=foo@gmail.com,bar@example.com

"""
import smtplib
import os
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

SMTP_DEFAULT_PORT_MODE = {
    25: SMTP_MODE_PLAIN,
    587: SMTP_MODE_STARTTLS,
    465: SMTP_MODE_SSL,
}

SMTP_DEFAULT_MODE_PORT = {
    mode: port for port, mode in SMTP_DEFAULT_PORT_MODE.items()
}

# builtin smtp config for popular email domains
SMTP_DOMAIN_CONFIG = {
    'gmail.com': {
        'host': 'smtp.gmail.com',
        'port': 465,
        'mode': SMTP_MODE_SSL,
    },
    'outlook.com': {
        'host': 'smtp-mail.outlook.com',
        'port': 587,
        'mode': SMTP_MODE_STARTTLS,
    },
    '163.com': {
        'host': 'smtp.163.com',
        'port': 465,
        'mode': SMTP_MODE_SSL,
    },
    'qq.com': {
        'host': 'smtp.qq.com',
        'port': 465,
        'mode': SMTP_MODE_SSL,
    },
    'exmail.qq.com': {
        'host': 'smtp.exmail.qq.com',
        'port': 465,
        'mode': SMTP_MODE_SSL,
    },
}


def _is_email(email):
    # TODO: verify email
    return email.count('@') == 1


def get_list(value, sep=','):
    """Get a list from value"""
    if not value:
        return []
    if isinstance(value, str):  # single or comma separated
        return value.strip().strip(sep).split(sep)
    return value


def get_line(value, sep=','):
    """Get a str line from value"""
    if not value:
        return ''
    if isinstance(value, (list, tuple)):
        return sep.join(value)
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


def get_smtp_client(host, port, mode):
    """
    Get SMTP connection.
    """
    assert host and port and mode
    assert mode in SMTP_MODE_CHOICES
    port = int(port)
    assert port > 0

    if mode == SMTP_MODE_PLAIN:
        client = smtplib.SMTP(host, port)
    elif mode == SMTP_MODE_STARTTLS:
        client = smtplib.SMTP(host, port)
        client.starttls()
    else:
        client = smtplib.SMTP_SSL(host, port)

    # client.set_debuglevel(log.isEnabledFor(logging.DEBUG))
    return client


def build_mime_msg(path):
    """Build MIME Message from path"""
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
        fp = open(path)
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
    filename = os.path.basename(path)
    msg.add_header('Content-Disposition', 'attachment', filename=filename)
    return msg


def sendmail(
        user=None, password=None,
        host=None, port=None, mode=None,
        _from=None, to=None, cc=None, bcc=None, reply_to=None,
        subject=None, extra_headers=None,
        text=None, html=None, attachments=None):

    # load envvars
    user = user or env.get('EMAIL_HOST_USER')
    password = password or env.get('EMAIL_HOST_PASSWORD')

    host = host or env.get('EMAIL_HOST')
    port = port or env.get('EMAIL_PORT')
    mode = mode or env.get('EMAIL_MODE')

    _from = _from or env.get('EMAIL_FROM') or user
    reply_to = reply_to or env.get('EMAIL_REPLY_TO')

    to = get_list(to or env.get('EMAIL_TO')) or [_from]
    cc = get_list(cc or env.get('EMAIL_CC'))
    bcc = get_list(bcc or env.get('EMAIL_BCC'))

    subject = subject or env.get('EMAIL_SUBJECT') or 'No Subject'

    text = text or env.get('EMAIL_TEXT')
    html = html or env.get('EMAIL_HTML')

    attachments = get_list(attachments or env.get('EMAIL_ATTACHMENTS'))

    # check required fields
    if not user:
        raise ValueError('user email address is required')
    elif not _is_email(user):
        raise ValueError('user must be a full email address')

    if not password:
        raise ValueError('user email password is required')

    domain = user.strip().split('@')[-1].lower()

    config = SMTP_DOMAIN_CONFIG.get(domain)
    if config:
        host = config.get('host')
        port = config.get('port')
        mode = config.get('mode')
        log.info('SMTP config for %s: %s:%s %s', domain, host, port, mode)

    if not host:
        host = 'smtp.{}'.format(domain)
        log.warn('no smtp host, guess it to be %s', host)

    if port:
        port = int(port)
        if port <= 0:
            raise ValueError('port must be positive integer')

    if mode and mode not in SMTP_MODE_CHOICES:
        raise ValueError('invalid mode: {}, choices: {}'.format(mode, '|'.join(SMTP_MODE_CHOICES)))

    if port and not mode:
        mode = SMTP_DEFAULT_PORT_MODE.get(int(port))
        if not mode:
            raise ValueError('we can not guess mode from port {}'.format(port))
    elif mode and not port:
        port = SMTP_DEFAULT_MODE_PORT[mode]
        log.warn('we guess smtp port %s from mode %s', port, mode)
    elif not port and not mode:
        port, mode = 465, SMTP_MODE_SSL
        log.warn('no port and no mode, use 465 and SSL as prefered')

    assert _is_email(_from)

    if reply_to:
        assert _is_email(reply_to)

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
        # add header to msg if set
        value = get_line(value)
        if value:
            root[name] = value

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
            log.debug('attach %02d: %s', n, path)
            root.attach(msg)
            n += 1
            if n >= 20:
                log.warning('too many files, only 20 attached')
                break

    # SMTP doesn't care about to, cc, bcc
    # put them all together
    recipients = to + cc + bcc
    log.debug('SMTP recipients: %s', recipients)

    # send msg
    client = get_smtp_client(host, port, mode)
    client.login(user, password)
    client.sendmail(_from, recipients, root.as_string())
    client.quit()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Send SMTP email from cli')

    parser.add_argument(
        '-u', '--user', metavar='EMAIL_HOST_USER',
        help='user email address to authenticate')

    parser.add_argument(
        '-p', '--password', metavar='EMAIL_HOST_PASSWORD',
        help='user email password to authenticate')

    parser.add_argument(
        '-H', '--host', metavar='EMAIL_HOST',
        help='SMTP host')

    parser.add_argument(
        '-P', '--port', metavar='EMAIL_PORT', type=int,
        help='SMTP port')

    parser.add_argument(
        '-M', '--mode', metavar='EMAIL_MODE', choices=SMTP_MODE_CHOICES,
        help='SMTP mode, choices: {}'.format('|'.join(SMTP_MODE_CHOICES)))

    parser.add_argument(
        '--from', metavar='EMAIL_FROM', dest='_from',
        help='From email address')

    parser.add_argument(
        '--to', metavar='EMAIL_TO', action='append', default=[],
        help='To email address, can repeat')

    parser.add_argument(
        '--cc', metavar='EMAIL_CC', action='append', default=[],
        help='Cc email address, can repeat')

    parser.add_argument(
        '--bcc', metavar='EMAIL_BCC', action='append', default=[],
        help='Bcc email address, can repeat')

    parser.add_argument(
        '--reply-to', metavar='EMAIL_REPLY_TO', dest='reply_to',
        help='Reply-To email address')

    parser.add_argument(
        '-s', '--subject', metavar='EMAIL_SUBJECT',
        help='email subject')

    parser.add_argument(
        '--text', metavar='EMAIL_TEXT',
        help='email content text version')

    parser.add_argument(
        '--html', metavar='EMAIL_HTML',
        help='email content html version')

    parser.add_argument(
        '-a', '--attachment', metavar='ATTACHMENT',
        action='append', default=[], dest='attachments',
        help='attachment path, can repeat, can be file or dir')

    args = parser.parse_args()
    sendmail(**vars(args))

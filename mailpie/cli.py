#!/usr/bin/env python
# coding=utf8
"""
Send email from CLI with Python.
"""
import logging
import argparse
from mailpie import log, sendmail


def main():
    parser = argparse.ArgumentParser(description='Send email from CLI')
    email_options = parser.add_argument_group('Email Options')

    email_options.add_argument(
        '-a', '--account', default='default',
        help='account name defined in config')

    email_options.add_argument(
        '--from', metavar='EMAIL_FROM', dest='_from',
        help='From email address to display in message')

    email_options.add_argument(
        '--to', metavar='EMAIL_TO', action='append', default=[],
        help='To email address, can be repeated')

    email_options.add_argument(
        '--cc', metavar='EMAIL_CC', action='append', default=[],
        help='Cc email address, can be repeated')

    email_options.add_argument(
        '--bcc', metavar='EMAIL_BCC', action='append', default=[],
        help='Bcc email address, can be repeated')

    email_options.add_argument(
        '--reply-to', metavar='EMAIL_REPLY_TO', dest='reply_to',
        help='Reply-To email address')

    email_options.add_argument(
        '-s', '--subject', metavar='EMAIL_SUBJECT',
        help='email subject')

    email_options.add_argument(
        '--text', metavar='EMAIL_TEXT',
        help='email content text version')

    email_options.add_argument(
        '--html', metavar='EMAIL_HTML',
        help='email content html version')

    email_options.add_argument(
        '-A', '--attachment', metavar='ATTACHMENT',
        action='append', default=[], dest='attachments',
        help='attachment path, can be repeated, can be file or dir')

    log_options = parser.add_mutually_exclusive_group(required=False)
    log_options.add_argument(
        '--verbose', action='store_true',
        help='Print debug logs')
    log_options.add_argument(
        '--quiet', action='store_true',
        help='Only print error logs')

    args = parser.parse_args()
    log_level = (args.verbose and logging.DEBUG or
                 args.quiet and logging.ERROR or
                 logging.INFO)
    log.setLevel(log_level)
    sendmail(**vars(args))


if __name__ == '__main__':
    main()

# encoding: utf-8

"""
Erzeugt einen Datenbank-Dump
"""

import sys
sys.path.append('./')
import os
import config
import subprocess
import datetime
import shutil


def execute(cmd):
    output, error = subprocess.Popen(
        cmd.split(' '), stdout=subprocess.PIPE,
        stderr=subprocess.PIPE).communicate()
    if error is not None and error.strip() != '':
        print >> sys.stderr, "Command: " + cmd
        print >> sys.stderr, "Error: " + error


def create_dump(folder):
    """
    Drops dumps in folder/config.DB_NAME
    """
    cmd = (config.MONGODUMP_CMD + ' --db ' + config.DB_NAME +
            ' --out ' + folder)
    for collection in config.DB_DUMP_COLLECTIONS:
        thiscmd = cmd + ' --collection ' + collection
        execute(thiscmd)


def compress_folder(folder):
    now = datetime.datetime.now()
    filename = 'dump_' + now.strftime('%Y-%m-%d') + '.tar.bz2'
    cmd = ('tar cjf ' + filename + ' ' + folder +
            os.sep + config.DB_NAME + os.sep)
    execute(cmd)
    shutil.rmtree(folder + os.sep + config.DB_NAME)
    shutil.move(filename, 'webapp/daten/')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Generate a database dump')
    parser.add_argument('folder', metavar='FOLDER', type=str,
                       help='an integer for the accumulator')

    args = parser.parse_args()
    create_dump(args.folder)
    compress_folder(args.folder)

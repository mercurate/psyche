#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
********neup********
usage: spig_neup.py [-b] master slave file
options: -b       backup files on ne or not
        master    ip of master cpm
        slave     ip of slave  cpm
        file      full name of update.tar.gz 
e.g.：spig-neup -b 192.168.20.55 192.168.20.43 ./update.tar.gz
*********Version1.1*********
"""
import os
import re
import sys
import getopt

import core

# Print usage message and exit
def usage(*args):
    sys.stdout = sys.stderr
    for msg in args: print msg
    print __doc__
    sys.exit(1)

#Main program:parse command line and start processing
def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'b')
    except getopt.error, msg:
        usage(msg)
    
    ip1 = '192.168.3.211'
    ip2 = '192.168.3.211'
    p = './update.tar.gz'
    b   = False
    
    if len(args) == 2 or len(args) == 3:
        ip1 = args[0]
        if not core.check_ip(ip1):
            print 'neup: Invalid master ip!'
            sys.exit(1)
        
        ip2 = args[-2]
        if not core.check_ip(ip2):
            print 'neup: Invalid slave ip!'
            sys.exit(2)

        p = args[-1]
        if not p.endswith('.tar.gz'):
            print 'neup: Update package must end with .tar.gz!'
            sys.exit(3)
            
        if not os.path.exists(p):
            print 'neup: Update package does not exist: %s!' % p
            sys.exit(4)
    
    for opt, arg in opts:
        if opt == '-b':
            b = True
            
    nu = core.NeUp(ip1, ip2, p, b)
    nu.update()
    sys.exit(0)
        
if __name__ == '__main__':
    main() 

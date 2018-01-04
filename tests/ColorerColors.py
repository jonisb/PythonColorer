#! python2
# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals, absolute_import

import os
import pathlib
try:
    from HTMLParser import HTMLParser
except:
    from html.parser import HTMLParser

#Ansi color codes
CEND      = '\33[0m'
CBOLD     = '\33[1m'
CITALIC   = '\33[3m'
CURL      = '\33[4m'
CBLINK    = '\33[5m'
CBLINK2   = '\33[6m'
CSELECTED = '\33[7m'

CBLACK  = '\33[30m'
CRED    = '\33[31m'
CGREEN  = '\33[32m'
CYELLOW = '\33[33m'
CBLUE   = '\33[34m'
CVIOLET = '\33[35m'
CBEIGE  = '\33[36m'
CWHITE  = '\33[37m'

CGREY    = '\33[90m'
CRED2    = '\33[91m'
CGREEN2  = '\33[92m'
CYELLOW2 = '\33[93m'
CBLUE2   = '\33[94m'
CVIOLET2 = '\33[95m'
CBEIGE2  = '\33[96m'
CWHITE2  = '\33[97m'

CBLACKBG  = '\33[40m'
CREDBG    = '\33[41m'
CGREENBG  = '\33[42m'
CYELLOWBG = '\33[43m'
CBLUEBG   = '\33[44m'
CVIOLETBG = '\33[45m'
CBEIGEBG  = '\33[46m'
CWHITEBG  = '\33[47m'

CGREYBG    = '\33[100m'
CREDBG2    = '\33[101m'
CGREENBG2  = '\33[102m'
CYELLOWBG2 = '\33[103m'
CBLUEBG2   = '\33[104m'
CVIOLETBG2 = '\33[105m'
CBEIGEBG2  = '\33[106m'
CWHITEBG2  = '\33[107m'

#Windows console colors
BLACK  = 0x0  # CBLACK
BLUE   = 0x1  # CBLUE
GREEN  = 0x2  # CGREEN
AQUA   = 0x3  # CBEIGE
RED    = 0x4  # CRED
PURPLE = 0x5  # CVIOLET
YELLOW = 0x6  # CYELLOW
WHITE  = 0x7  # CWHITE

GREY    = 0x8  # CGREY
BLUE2   = 0x9  # CBLUE2
GREEN2  = 0xA  # CGREEN2
AQUA2   = 0xB  # CBEIGE2
RED2    = 0xC  # CRED2
PURPLE2 = 0xD  # CVIOLET2
YELLOW2 = 0xE  # CYELLOW2
WHITE2  = 0xF  # CWHITE2

WinConToAnsiFG = {
    BLACK: CBLACK,
    BLUE: CBLUE,
    GREEN: CGREEN,
    AQUA: CBEIGE,
    RED: CRED,
    PURPLE: CVIOLET,
    YELLOW: CYELLOW,
    WHITE: CWHITE,

    GREY: CGREY,
    BLUE2: CBLUE2,
    GREEN2: CGREEN2,
    AQUA2: CBEIGE2,
    RED2: CRED2,
    PURPLE2: CVIOLET2,
    YELLOW2: CYELLOW2,
    WHITE2: CWHITE2,
}
WinConToAnsiBG = {
    BLACK: CBLACKBG,
    BLUE: CBLUEBG,
    GREEN: CGREENBG,
    AQUA: CBEIGEBG,
    RED: CREDBG,
    PURPLE: CVIOLETBG,
    YELLOW: CYELLOWBG,
    WHITE: CWHITEBG,

    GREY: CGREYBG,
    BLUE2: CBLUEBG2,
    GREEN2: CGREENBG2,
    AQUA2: CBEIGEBG2,
    RED2: CREDBG2,
    PURPLE2: CVIOLETBG2,
    YELLOW2: CYELLOWBG2,
    WHITE2: CWHITEBG2,
}

ColorerColors = {}


class MyHTMLParser2(HTMLParser):
    def handle_starttag(self, tag, attrs):
        if tag == 'assign':
            region = fore = back = None
            for _ in attrs:
                if _[0] == 'name':
                    region = _[1].replace(':', '-')
                if _[0] == 'fore':
                    fore = int(_[1].strip('#'), 16)
                if _[0] == 'back':
                    back = int(_[1].strip('#'), 16)

            if region is not None and fore is not None:
                if back is not None:
                    ColorerColors[region] = (WinConToAnsiFG[fore], WinConToAnsiBG[back])
                else:
                    ColorerColors[region] = (WinConToAnsiFG[fore],)


def initColors():
    parser = MyHTMLParser2()
    parser.feed((pathlib.Path(os.environ['COLORER5CATALOG']).parent/'hrd'/'console'/'jonib.hrd').read_text())


def SetAnsiColor(region):
    #for i in ColorerColors[region]:
    #    print(i, sep='', end='')
    return ''.join(ColorerColors[region])


def ResetAnsiColor():
    return CEND


#def ResetAnsiColor():
#    print(CEND, sep='', end='')


if __name__ == '__main__':
    initColors()
    print(SetAnsiColor('def-BooleanConstant'), "True", sep='')
    import platform, sys
    print(SetAnsiColor('def-BooleanConstant'), platform.architecture(), sep='')
    print(SetAnsiColor('def-BooleanConstant'), sys.version_info, sep='')
    print(SetAnsiColor('def-Text'), "Test", sep='')
    ResetAnsiColor()

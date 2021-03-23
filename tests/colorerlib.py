#! python3
# -*- coding: utf-8 -*-
from os import environ
from os.path import expandvars
from pathlib import Path


def getcolorerpath():
    try:
        return Path(environ['COLORER5CATALOG']).parent
    except KeyError:
        try:
            return Path((Path.home() / r".colorer5catalog").read_text()).parent
        except FileNotFoundError:
            try:
                return Path(Path(expandvars(r"%SYSTEMROOT%\.colorer5catalog")).read_text()).parent
            except FileNotFoundError:
                try:
                    return Path(Path(expandvars(r"%WINDIR%\.colorer5catalog")).read_text()).parent
                except FileNotFoundError:
                    try:
                        if Path("/usr/share/colorer/catalog.xml").exists():
                            return Path("/usr/share/colorer/catalog.xml").parent
                    except KeyError:
                        if Path("/usr/local/share/colorer/catalog.xml").exists():
                            return Path("/usr/local/share/colorer/catalog.xml").parent
    raise FileNotFoundError


if __name__ == '__main__':
    print(getcolorerpath())
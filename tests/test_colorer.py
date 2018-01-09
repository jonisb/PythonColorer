#! python3
# -*- coding: utf-8 -*-
import unittest
from threading import Thread
from queue import Queue, Empty
import subprocess
from pathlib import Path
import hashlib
from html.parser import HTMLParser
import regex
import ColorerColors
from ColorerColors import ResetAnsiColor
import os
import filecmp
import shutil

testfileQueue = Queue()
testQueue = Queue()
num_worker_threads = 16
threads = []
Format = "Python"
ColorerCommand = ['colorer.exe', '-ijonib', '-ht', '-dc', '-dh', '-db', '-en', '-elWARNING', '-t{0}'.format(Format)]


def getTests():
    ref_dir = Path('Reference')
    try:
        for ver in ref_dir.iterdir():
            if ver.is_dir():
                try:
                    float(ver.name)
                except ValueError:
                    group = ver
                    #print('group:', group.name)
                    for test in group.iterdir():
                        yield '', group.name, test
                else:
                    #print('ver', ver.name)
                    for group in ver.iterdir():
                        if group.is_dir():
                            #print('group:', group.name)
                            for test in group.iterdir():
                                yield ver.name, group.name, test
                        else:
                            test = group
                            yield ver.name, '', test
            else:
                test = ver
                yield '', '', test
    except FileNotFoundError:
        raise StopIteration


def ReadRst(Filename):
    with Filename.open('r',encoding='utf8') as f:
        Code = {}
        buffer = None
        Filename = None
        for line in f:
            result = regex.match(r"\.\. code:: (python|html)", line)
            if result is not None:
                if result.group(1) is not None:
                    if buffer:
                        #yield buffer
                        Code[Format] = buffer
                    buffer = ""
                    Format = result.group(1)
                    continue
            if buffer is not None:
                buffer += line[4:]
        if buffer:
            Code[Format] = buffer
    return Code


def CallColorer(VerifyData):
    proc = subprocess.Popen(ColorerCommand, stdin=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=False)
    TestData = proc.communicate(VerifyData.encode('utf-8'))[0].decode('utf-8').replace('\r\n', '\n')

    return TestData


def getTestData():
    while True:
        try:
            file = testfileQueue.get() #timeout=30
        except Empty:
            break
        else:
            try:
                if file is None:
                    break
                VerifyData = ReadRst(file)
                TestData = CallColorer(VerifyData['python'])
                testQueue.put_nowait((file, TestData, VerifyData['html'], VerifyData['python']))
            finally:
                testfileQueue.task_done()


def ReturnTestData(test):
    while True:
        try:
            file, TestData, VerifyData, Syntax = testQueue.get() # timeout=30
        except Empty:
            break
        else:
            try:
                if test == file.stem:
                    return TestData, VerifyData, Syntax
                else:
                    testQueue.put_nowait((file, TestData, VerifyData, Syntax))
            finally:
                testQueue.task_done()


class TestSequenceMeta(type):
    def __new__(mcs, name, bases, dict):
        def gen_test(test_name, ver, group):
            def test(self):
                try:
                    TestData, VerifyData, Syntax = ReturnTestData(test_name)
                except KeyError:
                    pass
                else:
                    #print(TestData, VerifyData)
                    self.longMessage = False
                    self.assertEqual(TestData, VerifyData, DisplayError(TestData, VerifyData, ver, group, Syntax))
                    #self.assertEqual(TestData, VerifyData)
            test.__doc__ = f"Test: '{group or 'generic'}' with Python {ver or 3.6}"
            return test

        for (ver, group, file) in getTests():
            testfileQueue.put_nowait(file)
            test_name = "test_%s" % file.stem
            dict[test_name] = gen_test(file.stem, ver, group)
        else:
            for i in range(num_worker_threads):
                testfileQueue.put_nowait(None)

        return type.__new__(mcs, name, bases, dict)


class TestSequence(unittest.TestCase, metaclass=TestSequenceMeta):
    pass


def setUpModule():
    for i in range(num_worker_threads):
        t = Thread(target=getTestData)
        t.start()
        threads.append(t)

def tearDownModule():
    testfileQueue.join()
    testQueue.join()

    for t in threads:
        t.join()

def ReadTestSyntax():
    with Path("Syntax_test.py").open('r', encoding='utf8') as f:
        buffer = None
        for line in f:
            result = regex.match(r"^#\s*(?<test>Testing:\s*(?<testing>\S+)?\s*(?:pyver:\s*(?<pyver>\S+))?)", line)
            if result is not None:
                if result.group('test') is not None:
                    if buffer:
                        yield buffer, testing, pyver
                    buffer = ""
                    testing = result.group('testing') or ''
                    pyver = result.group('pyver') or ''
                    continue
            if buffer is not None:
                buffer += line
        if buffer:
            yield buffer, testing, pyver


def WriteRst(Filename, Python, HTML):
    Python = "\n".join([f"    {line}" for line in Python.splitlines()])
    HTML = "\n".join([f"    {line}" for line in HTML.splitlines()])
    Code = f"""\
.. code:: python
{Python}

.. code:: html
{HTML}
"""
    Filename.parent.mkdir(parents=True, exist_ok=True)
    Filename.write_text(Code, encoding='utf8')


def write_test(ver, group, Syntax, TestData, VerifyData, Filename=None):
    Filename = Filename or hashlib.sha256(Syntax.encode('utf8')).hexdigest()
    Filename = Path(f"{'Pending'}/{ver}/{group}/{Filename}.rst")
    if TestData != VerifyData:
        WriteRst(Filename, Syntax, TestData)
    else:
        try:
            Filename.unlink()
        except FileNotFoundError:
            pass
        else:
            try:
                Filename.parent.rmdir()
            except OSError:
                pass


def build_tests():
    for Syntax, testing, pyver in ReadTestSyntax():
        #proc = subprocess.Popen(ColorerCommand, stdin=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True)
        #TestData = proc.communicate(Syntax)[0]
        TestData = CallColorer(Syntax)
        Filename = hashlib.sha256(Syntax.encode('utf8')).hexdigest()
        VerifyData = None
        for filepath in ("Reference", "Pending"):
            try:
                VerifyData = ReadRst(Path(f"{filepath}/{pyver}/{testing}/{Filename}.rst"))
            except IOError:
                continue
            break
        if VerifyData is not None:
            try:
                if TestData.replace('\r\n', '\n') == VerifyData['html']:
                    continue
            except KeyError:
                pass
        print(Filename)
        print(Syntax)
        WriteRst(Path(f"{'Pending'}/{pyver}/{testing}/{Filename}.rst"), Syntax, TestData)


def DisplayError(TestData, VerifyData, ver, group, Syntax):
    parser = MyHTMLParser()
    parser.Result = ''
    parser.feed(VerifyData)
    VerifyDataColor = ColorerColors.SetAnsiColor('def-Text') + parser.Result + ResetAnsiColor()

    parser = MyHTMLParser()
    parser.Result = ''
    parser.feed(TestData)
    TestDataColor = ColorerColors.SetAnsiColor('def-Text') + parser.Result + ResetAnsiColor()

    write_test(ver, group, Syntax, TestData, VerifyData)

    return f"\nReference:\n{VerifyDataColor}\nresult:\n{TestDataColor}"


class MyHTMLParser(HTMLParser):
    def handle_starttag(self, tag, attrs):
        for _ in attrs:
            if _[0] == 'class':
                for region in _[1].split():
                    try:
                        self.Result += ColorerColors.SetAnsiColor(region)
                    except:
                        pass
                    else:
                        break
                else:
                    pass
                break

    def handle_endtag(self, tag):
        self.Result += ColorerColors.SetAnsiColor('def-Text')

    def handle_data(self, data):
        self.Result += data


def UpdateFiles():
    src = (Path('..') / 'auto').resolve()
    dst = Path(os.environ['COLORER5CATALOG']).parent / 'hrc' / 'auto'
    for file in src.glob('**/*.hrc'):
        if file.is_file():
            outfile = dst / file.relative_to(src)
            try:
                if filecmp.cmp(file, outfile, shallow=True):
                    continue
                else:
                    print("Not a copy:", outfile)
            except FileNotFoundError:
                print("No copy found:", outfile)
            try:
                outfile.unlink()
                print("Old file removed:", outfile)
            except FileNotFoundError:
                pass
            if not outfile.parent.exists():
                outfile.parent.mkdir(parents=True, exist_ok=True)
            try:
                outfile.symlink_to(file)
                print("File updated(link):", outfile)
            except Exception:
                try:
                    os.link(file, outfile)
                    print("File updated(hardlink):", outfile)
                except Exception:
                    shutil.copy2(file, outfile)
                    print("File updated(copy):", outfile)


if __name__ == '__main__':
    ColorerColors.initColors()

    UpdateFiles()

    build_tests()
    unittest.main()

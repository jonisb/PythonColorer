#! python3
# -*- coding: utf-8 -*-
import unittest
from threading import Thread
from queue import Queue, Empty
import subprocess
from pathlib import Path
import regex

testfileQueue = Queue()
testQueue = Queue()
num_worker_threads = 2
threads = []
Format = "Python"
ColorerCommand = ['colorer.exe', r'-cColorer\catalog.xml', '-ijonib', '-ht', '-dc', '-dh', '-db', '-en', '-elWARNING', '-t{0}'.format(Format)]


def getTests():
    ref_dir = 'Reference'
    try:
        for ver in Path(ref_dir).iterdir():
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
    with open(Filename, 'r') as f:
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
    proc = subprocess.Popen(ColorerCommand, stdin=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True)
    TestData = proc.communicate(VerifyData)[0] # TODO.replace('\r\n', '\n')

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
                VerifyData = ReadRst(str(File))
                TestData = CallColorer(VerifyData['python'])
                testQueue.put_nowait((file, TestData, VerifyData['html']))
            finally:
                testfileQueue.task_done()


def ReturnTestData(test):
    while True:
        try:
            file, TestData, VerifyData = testQueue.get() # timeout=30
        except Empty:
            break
        else:
            try:
                if test == file.stem:
                    return TestData, VerifyData
                else:
                    testQueue.put_nowait((file, TestData, VerifyData))
            finally:
                testQueue.task_done()


class TestSequenceMeta(type):
    def __new__(mcs, name, bases, dict):

        def gen_test(test_name):
            def test(self):
                try:
                    TestData, VerifyData = ReturnTestData(test_name)
                except KeyError:
                    pass
                else:
                    #print(TestData, VerifyData)
                    #self.assertEqual(TestData, VerifyData, DisplayError(TestData, VerifyData))
                    self.assertEqual(TestData, VerifyData)
            return test

        for (ver, group, file) in getTests():
            testfileQueue.put_nowait(file)
            test_name = "test_%s" % file.stem
            dict[test_name] = gen_test(file.stem)
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

if __name__ == '__main__':
    unittest.main()

# Runs the entire test suite by default
# + | a - addition
# - | s - subtraction
# * | m - multiplication
# / | d - division
# p     - printing
# -q    - quiet mode
# -s    - stop after the first failed test and copy it to clipboard (linux only)

# change the EXECUTABLE_NAME
EXECUTABLE_NAME = "./a.out"

import os
import subprocess
from dataclasses import dataclass
from enum import Enum
from subprocess import PIPE
import sys


class TestType(Enum):
    PRINT = ('?', "printing")
    ADD = ('+', "addition")
    SUB = ('-', "subtraction")
    MUL = ('*', "multiplication")
    DIV = ('/', "division")

    @classmethod
    def from_str(cls, x: str):
        match x:
            case '+' | 'a': return cls.ADD
            case '-' | 's': return cls.SUB
            case '*' | 'm': return cls.MUL
            case '/' | 'd': return cls.DIV
            case _: return cls.PRINT


@dataclass
class TestPrint:
    i: int
    args: list[str]
    ans: str
    type: TestType = TestType.PRINT


@dataclass
class TestOperation:
    i: int
    args: list[str]
    ans: str
    type: TestType


type Test = TestPrint | TestOperation


def test_from_arg(i: int, data: list[str], ans: str) -> Test:
    if len(data) == 3:
        return TestPrint(i + 1, data, ans)
    else:
        return TestOperation(i + 1, data, ans, TestType.from_str(data[2]))


def run_test(test: Test) -> tuple[bool, str]:
    ps = subprocess.Popen([EXECUTABLE_NAME, *test.args], stdout = PIPE, stderr = PIPE)
    ps.wait()

    assert ps.stdout
    data = ps.stdout.read().decode("utf-8").strip()

    return data == test.ans, data


def run_tests(tests: list[Test], *, quiet = False, single_fail = False) -> tuple[int, list[Test]]:
    test_type = tests[0].type
    good = 0
    bad = []
    last_print = True

    for i, test in enumerate(tests):
        print(f"\rRunning tests for {test_type.value[1]} ({i}/{len(tests)}) (good: {good}, bad: {len(bad)})", end='     ')
        last_print = True
        result, data = run_test(test)
        good += result

        if not result:
            bad.append(test)
            test_str = ' '.join(test.args)
            if not quiet or single_fail:
                print(f"\rTEST #{test.i} ({test_str}): output: {data}, answer: {test.ans}" + " " * 12)
                last_print = False

            if single_fail:
                cl = subprocess.Popen(["xclip", "-selection", "clipboard"], stdin = PIPE)
                cl.communicate(f"{EXECUTABLE_NAME} {test_str}".encode('utf-8'))
                exit(1)

    if last_print:
        print(" " * 120, end = '\r')
    print(f"Ran {len(tests)} tests for {test_type.value[1]} (good: {good}, bad: {len(bad)})" + " " * 20)
    return good, bad


def main():
    path = os.path.dirname(os.path.realpath(__file__))

    with open(path + "/fp_tests.txt") as f:
        tests_raw = [x.strip().split(" ") for x in f.read().strip().split("\n")]

    with open(path + "/fp_answers.txt") as f:
        answers = [x.strip() for x in f.read().strip().split("\n")]

    tests_unsorted = [test_from_arg(i, *tup) for i, tup in enumerate(zip(tests_raw, answers))]

    tests = {
        test_type: [*filter(lambda x: x.type == test_type, tests_unsorted)] for test_type in TestType
    }

    results: dict[TestType, tuple[int, list[Test]]] = {}

    quiet = False
    single_fail = False
    test_type = None

    for arg in sys.argv[1:]:
        match arg:
            case '-q': quiet = True
            case '-s': single_fail = True
            case '+' | 'a' | '-' | 's' | '*' | 'm' | '/' | 'd' | 'p':
                test_type = TestType.from_str(arg)


    if test_type:
        results.update({test_type: run_tests(tests[test_type], quiet=quiet, single_fail=single_fail)})
    else:
        for test_type in TestType:
            results.update({test_type: run_tests(tests[test_type], quiet=quiet, single_fail=single_fail)})

    print("\n---- RESULTS ----")
    for result_type in results:
        result = results[result_type]
        failed_percent = len(result[1]) / len(tests[result_type]) * 100

        print(f"Tests for {result_type.value[1]}")
        print("Successful:", result[0])
        print(f"Failed: {len(result[1])} ({failed_percent:.2f}%)")
        if len(result[1]) < 15:
            for test in result[1]:
                print(f"    Test #{test.i}")
        print()

    if len(results) > 1:
        successful = sum([results[x][0] for x in results])
        failed = sum([len(results[x][1]) for x in results])
        failed_percent = failed / (successful + failed) * 100

        print("---- TOTAL ----")
        print("Successful:", successful)
        print(f"Failed: {failed} ({failed_percent:.2f}%)")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        exit(0)

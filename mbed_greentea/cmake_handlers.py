"""
mbed SDK
Copyright (c) 2011-2015 ARM Limited

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Author: Przemyslaw Wirkus <Przemyslaw.Wirkus@arm.com>
"""

import re
import os
import os.path

from mbed_greentea.mbed_greentea_log import gt_logger

def load_ctest_testsuite(link_target, binary_type='.bin', verbose=False):
    """! Loads CMake.CTest formatted data about tests from test directory
    @return Dictionary of { test_case : test_case_path } pairs
    """
    result = {}
    if link_target is not None:
        ctest_path = os.path.join(link_target, 'test', 'CTestTestfile.cmake')
        try:
            with open(ctest_path) as ctest_file:
                for line in ctest_file:
                    line_parse = parse_ctesttestfile_line(link_target, binary_type, line, verbose=verbose)
                    if line_parse:
                        test_case, test_case_path = line_parse
                        result[test_case] = test_case_path
        except:
            pass    # Return empty list if path is not found
    return result

def parse_ctesttestfile_line(link_target, binary_type, line, verbose=False):
    """! Parse lines of CTestTestFile.cmake file and searches for 'add_test'
    @return Dictionary of { test_case : test_case_path } pairs or None if failed to parse 'add_test' line
    @details Example path with CTestTestFile.cmake:
    c:/temp/xxx/mbed-sdk-private/build/frdm-k64f-gcc/test/

    Example format of CTestTestFile.cmake:
    # CMake generated Testfile for
    # Source directory: c:/temp/xxx/mbed-sdk-private/build/frdm-k64f-gcc/test
    # Build directory: c:/temp/xxx/mbed-sdk-private/build/frdm-k64f-gcc/test
    #
    # This file includes the relevant testing commands required for
    # testing this directory and lists subdirectories to be tested as well.
    add_test(mbed-test-stdio "mbed-test-stdio")
    add_test(mbed-test-call_before_main "mbed-test-call_before_main")
    add_test(mbed-test-dev_null "mbed-test-dev_null")
    add_test(mbed-test-div "mbed-test-div")
    add_test(mbed-test-echo "mbed-test-echo")
    add_test(mbed-test-ticker "mbed-test-ticker")
    add_test(mbed-test-hello "mbed-test-hello")
    """
    add_test_pattern = '[adtesADTES_]{8}\([\w\d_-]+ \"([\w\d_-]+)\"'
    re_ptrn = re.compile(add_test_pattern)
    if line.lower().startswith('add_test'):
        m = re_ptrn.search(line)
        if m and len(m.groups()) > 0:
            if verbose:
                print m.group(1) + binary_type
            test_case = m.group(1)
            test_case_path = os.path.join(link_target, 'test', m.group(1) + binary_type)
            return test_case, test_case_path
    return None


def list_binaries_for_targets(build_dir='./build', verbose_footer=False):
    """! Prints tests in target directories, only if tests exist.
    @details Skips empty / no tests for target directories.
    """
    dir = build_dir
    sub_dirs = [os.path.join(dir, o) for o in os.listdir(dir) if os.path.isdir(os.path.join(dir, o))] \
        if os.path.exists(dir) else []

    def count_tests():
        result = 0
        for sub_dir in sub_dirs:
            test_list = load_ctest_testsuite(sub_dir, binary_type='')
            if len(test_list):
                for test in test_list:
                    result += 1
        return result

    if count_tests():
        gt_logger.gt_log("available tests for built targets, location '%s'"% os.path.abspath(build_dir))
        for sub_dir in sub_dirs:
            test_list = load_ctest_testsuite(sub_dir, binary_type='')
            if len(test_list):
                gt_logger.gt_log_tab("target '%s':" % sub_dir.split(os.sep)[-1])
                for test in sorted(test_list):
                    gt_logger.gt_log_tab("test '%s'"% test)
    else:
        gt_logger.gt_log_warn("no tests found in current location")

    if verbose_footer:
        print
        print "Example: execute 'mbedgt -t TARGET_NAME -n TEST_NAME' to run test TEST_NAME for target TARGET_NAME"

from tests import BASIC_TESTS, RANGE_TESTS

from stock.stock import Stock, parse_date

def report_result(result, case_num, data, exp_data):
    """
    Print out basic report on test case if it passed or failed. Nothing fancy.
    """
    if result:
        print('    Case %s: PASSED' % case_num)
    else:
        print('    Case %s: FAILED' % case_num)
        print('     EXPECTED: ' + str(exp_data))
        print('     RETURNED: ' + str(data))

def verify_day(day_info, expected):
    """
    Compare returned day info to expected data as defined for the test case.
    :param day_info: Single day's data as provided by yahoo finance
    :param expected: Test case expected day data.

    :returns: True, if the data matches. False otherwise.
    """
    for i,data in enumerate(day_info):
        if data != expected[i]:
            return False

    return True


# Basic tests for single dates
for test in BASIC_TESTS:
    print('\nRunning basic tests for %s' % test)
    test_stock = Stock(test, '2017-01-01', '2017-12-01')

    case_num = 1
    for case in BASIC_TESTS[test]:
        date = case[0]
        print('  Date: %s' % date)

        # Get data for test case
        expected_data = case[1]
        day_info = test_stock.day_info(date)
        ret = verify_day(day_info[1], expected_data)

        # Report results
        report_result(ret, case_num, day_info[1], expected_data)

        day_info = [test_stock.open(date), test_stock.high(date), test_stock.low(date), test_stock.close(date), test_stock.adj_close(date), test_stock.volume(date)]
        ret = verify_day(day_info, expected_data)

        # Report results
        report_result(ret, case_num+0.1, day_info, expected_data)

        case_num += 1

# Run range testing
for test in RANGE_TESTS:
    test_case = RANGE_TESTS[test]
    start_date = test_case['start']
    end_date = test_case['end']

    print('\nRunning range tests for %s from %s to %s' % (test, start_date, end_date))
    test_stock = Stock(test, start_date, end_date)

    expected_data = test_case['expected']
    num_cases = len(expected_data)
    stock_data = test_stock.day_info(start_date, end_date)

    exp_idx = 0;
    for day in stock_data:
        exp_date = parse_date(expected_data[exp_idx][0])
        if exp_date == day[0]:
            # This is one of the testing dates
            ret = verify_day(day[1], expected_data[exp_idx][1])

            # Report results
            report_result(ret, exp_idx+1, day[1], expected_data[exp_idx][1])

            exp_idx += 1

    if exp_idx != num_cases:
        # In some cases this is good because we want to test boundaries which don't include extra days
        print('***WARNING*** Not all test cases were encountered. %s were skipped. Verify this is expected.' % (num_cases - exp_idx))


# More testing added below as new features added -- or make a new file?
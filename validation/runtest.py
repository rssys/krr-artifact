import subprocess
import re
import argparse
import os
import sys
import traceback

# Path to the testcase file
testcase_file = "testcase"

# Set base_dir to current directory
base_dir = os.getcwd()
INITIAL_INTERVAL = 1000
DEFAULT_RECORD_TIMEOUT = 80

def parse_arguments():
    parser = argparse.ArgumentParser(description='QEMU test runner with configurable paths')
    parser.add_argument('--qemu-path', required=True, 
                       help='Path to the qemu executable (e.g., /path/to/qemu-system-x86_64)')
    parser.add_argument('--host-kernel-path', required=True, 
                       help='Path to the host KRR kernel source code (e.g., /path/to/kernel-rr-linux)')
    parser.add_argument('--bzimage-path', required=True,
                       help='Path to the bzImage kernel file')
    parser.add_argument('--rootfs-path', required=True,
                       help='Path to the rootfs qcow2 file')
    parser.add_argument('--start-point', type=int, default=-1,
                       help='Starting test index (default: 1012)')
    parser.add_argument('--skip-replay', default=False, action='store_true',
                       help='Skip replay tests')
    parser.add_argument('--record-timeout', type=int, default=80,
                       help='Timeout for record waiting')

    return parser.parse_args()

# Parse command line arguments
args = parse_arguments()

# Set paths from command line arguments
qemu_path = args.qemu_path
bzImage_path = args.bzimage_path
rootfs_path = args.rootfs_path
host_kernel_path = args.host_kernel_path
record_timeout = args.record_timeout

# Other paths based on base_dir (current directory)
log_file = os.path.join(base_dir, "rec.log")
run_log = "./LOG"

base_record_cmdline = """
{qemu_bin} -smp 1 -kernel {bzImage_path} \
-accel kvm -cpu host -m 2G -no-hpet \
-append  "root=/dev/sda rw init=/lib/systemd/systemd tsc=reliable console=ttyS0 mce=off test={test}" \
-hda {rootfs_path} \
-object memory-backend-file,size=4096M,share,mem-path=/dev/shm/ivshmem,id=hostmem \
-device ivshmem-plain,memdev=hostmem -D {log} -exit-record 1 -checkpoint-interval {interval}
"""

base_replay_cmdline = """
{qemu_bin} -accel tcg -smp 1 -cpu Icelake-Client -no-hpet -m 2G -kernel {bzImage_path} \
-append "root=/dev/sda rw init=/lib/systemd/systemd tsc=reliable console=ttyS0 mce=off test={test}" \
-hda {rootfs_path} -device ivshmem-plain,memdev=hostmem \
-object memory-backend-file,size=4096M,share,mem-path=/dev/shm/ivshmem,id=hostmem \
-vnc :0 -monitor stdio -kernel-replay test1 -singlestep -D {log} -krr-autostart
"""

class TimeoutException(Exception):
    pass

start_point = args.start_point


test_interval_map = {}
skip_replay = args.skip_replay

def get_test_list() -> list:
    tests = []
    # Read the file and iterate through each line
    with open(testcase_file, 'r') as file:
        lines = file.readlines()
        for line in lines:
            line = line.strip()  # Remove any trailing newline or whitespace

            if line:  # Only proceed if the line is not empty
                if ":" in line:
                    test_set = line.split(":")
                    tests.append(test_set[0])
                    test_interval_map[test_set[0]] = int(test_set[1])
                else:
                    tests.append(line)

    return tests

def reload_rr():
    os.system("cd {host_kernel_path};sh replace.sh".format(host_kernel_path=host_kernel_path))

def run_program(cmdline, ignore_ret=True, timeout=record_timeout):
    try:
        process = subprocess.run(cmdline, shell=True, check=True, timeout=timeout)
    except subprocess.TimeoutExpired as e:
        raise TimeoutException("TIMEOUT")
    except subprocess.CalledProcessError as e:
        if not ignore_ret:
            if e.returncode != 0:  # Check the return code
                raise Exception(f"Error: Test '{cmdline}' failed with return code {e.returncode}")


def analyze_summary(log_file, output_file, test_name):
    # Initialize variables for storing counts
    passed_count = 0
    failed_count = 0
    broken_count = 0
    skipped_count = 0
    warnings_count = 0

    # Patterns to match each summary line
    patterns = {
        'passed': re.compile(r"passed\s+(\d+)"),
        'failed': re.compile(r"failed\s+(\d+)"),
        'broken': re.compile(r"broken\s+(\d+)"),
        'skipped': re.compile(r"skipped\s+(\d+)"),
        'warnings': re.compile(r"warnings\s+(\d+)")
    }
    found = False

    try:
        # Read the log file and find the summary section
        with open(log_file, 'r') as file:
            for line in file.readlines():
                # Check and extract the numbers using the patterns
                if patterns['passed'].search(line):
                    passed_count = int(patterns['passed'].search(line).group(1))
                    found = True
                elif patterns['failed'].search(line):
                    failed_count = int(patterns['failed'].search(line).group(1))
                elif patterns['broken'].search(line):
                    broken_count = int(patterns['broken'].search(line).group(1))
                elif patterns['skipped'].search(line):
                    skipped_count = int(patterns['skipped'].search(line).group(1))
                elif patterns['warnings'].search(line):
                    warnings_count = int(patterns['warnings'].search(line).group(1))
    except Exception as e:
        LOG("Read excption: {}".format(str(e)))

    if not found:
        result = "{} unformated report\n".format(test_name)
    else:
        # Write the result in one line to the output file
        result = (f"{test_name},passed={passed_count},failed={failed_count},"
                f"broken={broken_count},skipped={skipped_count},warnings={warnings_count}\n")

    with open(output_file, 'a+') as out_file:
        out_file.write(result)

    return

def LOG(msg):
    with open(run_log, "a+") as f:
        f.write("{}\n".format(msg))

def record_index():
    global start_point
    with open("start_point", 'w') as f:
        f.write(str(start_point))

def get_index() -> int:
    try:
        with open("start_point", 'r') as f:
            return int(f.read())
    except FileNotFoundError:
        return start_point

def run_test(test, test_dir, test_interval=INITIAL_INTERVAL):
    succeed = True
    interval = test_interval
    upper = 7

    for i in range(upper):
        record = base_record_cmdline.format(
            qemu_bin=qemu_path,
            bzImage_path=bzImage_path,
            test=test_dir,
            rootfs_path=rootfs_path,
            log=log_file,
            interval=interval,
        )
        LOG("Run test={} timeout={}, command={}".format(test, DEFAULT_RECORD_TIMEOUT, record))

        try:
            run_program(record, timeout=DEFAULT_RECORD_TIMEOUT)
        except TimeoutException as e:
            interval = interval * 2
            if i == upper - 2:
                interval = 0

            if i == upper - 1:
                LOG("{} timeout failed".format(test))
                succeed = False
                reload_rr()
                break
            else:
                LOG("{} timeout, try interval {}".format(test, interval))

            reload_rr()
        else:
            break

    return succeed, interval

def run_all_tests():
    tests = get_test_list()

    # tests = tests
    index = 0
    retry = 0
    global start_point

    if start_point < 0:
        start_point = get_index()
    interval = INITIAL_INTERVAL

    LOG("Start from test index {}".format(start_point))
    reload_rr()

    while index < len(tests):
        if index < start_point:
            index += 1
            continue

        test = tests[index]
        test_dir = "/opt/ltp/testcases/bin/{}".format(test)
        LOG("index={}, test={}, interval={}".format(index, test, interval))

        if test in test_interval_map:
            interval = test_interval_map[test]

        succeed, interval = run_test(test, test_dir, test_interval=interval)
        if succeed:
            analyze_summary("./rr-result.txt", "./ltp-result", test)

            if interval == 0:
                try:
                    os.remove("checkpoint-0")
                except:
                    pass

            if not skip_replay:
                replay = base_replay_cmdline.format(
                    qemu_bin=qemu_path,
                    bzImage_path=bzImage_path,
                    test=test_dir,
                    rootfs_path=rootfs_path,
                    log=log_file,
                    interval=interval,
                )
                try:
                    run_program(replay, ignore_ret=False, timeout=None)
                except Exception as e:
                    LOG("Failed to replay {}".format(test))
                    reload_rr()
                    if retry < 2:
                        LOG("Failed test[{}]: {}, retry={}".format(test, str(e), retry))
                        retry += 1
                        continue
                    else:
                        LOG("{} give up".format(test))
                else:
                    LOG("{} replay passed interval {}".format(test, interval))
            else:
                LOG("replay is skipped")
        else:
            LOG("{} is aborted".format(test))

        index += 1
        retry = 0
        start_point = index
        record_index()
        interval = INITIAL_INTERVAL


def main():
    # reload_rr()
    LOG("base_dir={} skip_replay={}".format(base_dir, skip_replay))
    while True:
        try:
            run_all_tests()
        except Exception as e:
            print(traceback.format_exc())
        else:
            break

if __name__ == "__main__":
    main()

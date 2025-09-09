# KRR Validation Test

## Note
Since we've done some updates to the code base, for this part, please use the newest version of KRR [QEMU](https://github.com/krr-io/krr-qemu)(the main branch), [KVM](https://github.com/krr-io/kernel-rr-linux)(the master branch) and the [guest agent patch](Support-KRR-guest-agent.patch) under this directory.

Run testcases from LTP:
```
python3 runtest.py --help
usage: runtest.py [-h] --qemu-path QEMU_PATH --host-kernel-path HOST_KERNEL_PATH --bzimage-path BZIMAGE_PATH --rootfs-path ROOTFS_PATH [--start-point START_POINT] [--skip-replay]
                  [--record-timeout RECORD_TIMEOUT]

QEMU test runner with configurable paths

options:
  -h, --help            show this help message and exit
  --qemu-path QEMU_PATH
                        Path to the qemu executable (e.g., /path/to/qemu-system-x86_64)
  --host-kernel-path HOST_KERNEL_PATH
                        Path to the host KRR kernel source code (e.g., /path/to/kernel-rr-linux)
  --bzimage-path BZIMAGE_PATH
                        Path to the bzImage kernel file
  --rootfs-path ROOTFS_PATH
                        Path to the rootfs qcow2 file
  --start-point START_POINT
                        Starting test index (default: 1012)
  --skip-replay         Skip replay tests
  --record-timeout RECORD_TIMEOUT
                        Timeout for record waiting
```
For rootfs image, you can use `rootfs-bug.qcow2` downloaded in the artifact [installation](../README.md#install-krr), this image includes all the test binaries.


Example:
```
python3 runtest.py --qemu-path <QEMU binary> --bzimage-path <bzImage of test kernel> --rootfs-path <rootfs> --host-kernel-path <KRR Host kernel source code path>
```

All the testcase binaries are in `testcase` file, each binary may contain multiple tests, which will be reported in the `ltp-result` file.

When running tests, the record replay result will be printed in `LOG` file, like below:
```
access01 timeout, try interval 8000
Run test=access01 timeout=80, command=<QEMU command used>

access01 replay passed interval 8000
```
`access01` is the test binary, `interval 8000` means the checkpoint interval for validation is 8000 instructions.

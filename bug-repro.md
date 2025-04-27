# KRR Bug Reproduction

## Prepare
1. First, go to `kernel-rr-linux/`, make sure you are on the KRR's branch, if not, checkout to it and recompile:
```
cd kernel-rr-linux/
git checkout rr-para

# re-compile script
sh replace.sh
```

2. Reload the KRR KVM modules:
```
sh reload.sh
```
This reload enables the following option:
* `rr_disable_avx`: Required, the testing kernel configs from syzbot have enabled some advanced features, such as aesni, that would use the avx instruction in kernel mode, KRR's replay currently has not supported the avx emulation, this option hides the avx from it.

* `rr_trap_rdtsc`: Recommended, it makes RDTSC instruction in trap mode, helping reduce the rdtsc event number and save the KRR's logging space. ***Does not affect the reproducing results***

3. Download kernel images and disk image for the bug reproduction:
```
bash scripts/download_kernels.sh
```
This will download the kernel images listed in the paper's table 1&2 into the `kernel_files` directory, each file is named as `bzImage<kernel version>` and its compressed vmlinux `vmlinuxRR-<kernel version>.gz`(please decompress before using it), use the corresponding kernel images based on the table to run the bug scripts, for example, if you are looking for 6.1.84 kernel, it should be `bzImage6184` and `vmlinuxRR-6184.gz`.

For the rootfs disk, please use the `rootfs-bug.qcow2` downloaded in [installation step](README.md) for both Syzbot Bugs and CVEs.

### Operation Guide
* `start recording`: press `ctrl+A` and `C` to enter QEMU monitor, execute `rr_record test1`
* `stop recording`: press `ctrl+A` and `C` to enter QEMU monitor, execute `rr_end_record`
* Remember each time when trying a different kernel image for replay, make sure to execute command below using the kernel's vmlinux, otherwise the replay would fail:
```
bash qemu-tcg-kvm/kernel_rr/generate_symbol.sh <vmlinux absolute path> <qemu-tcg-kvm absolute path>
```

***Note*** KRR does not support record phase being interrupted without `rr_end_record`, if it happens, the VM cannot be launched again, to recover from it, go to `kernel-rr-linux/` and execute `sh reload.sh` to reload the KVM module.

## Syzbot Bugs
***Key results: Table 1***

(Estimated human time: 1h, machine time 3h ~ 4h)

In this section, you will use KRR to reproduce several known kernel bugs from syzbot.

1. Launch the VM and reproduce bug:

For each bug, use the following QEMU command for recording(fill the `<bzImage file>` and `<disk image file>`), for bug #5, change the `-smp 1` to `-smp 2`:
```
../build/qemu-system-x86_64 -smp 1 -kernel <bzImage file> -accel kvm -cpu host -no-hpet -m 2G -append  "root=/dev/sda rw init=/lib/systemd/systemd tsc=reliable console=ttyS0 mce=off test=/root/test-<hash>" -hda <disk image file> -object memory-backend-file,size=4096M,share,mem-path=/dev/shm/ivshmem,id=hostmem -device ivshmem-plain,memdev=hostmem -D rec.log -nographic -checkpoint-interval 0 -exit-record 1
```
Note in the `-append` option, there's `test=/root/test-<hash>`, this means the KRR service in the system will automatically  start recording and execute this binary file after booting up to reproduce the bug, please refer the table below to find the corresponding test file name for the bug you are reproducing, e.g., if you are trying to reproduce the bug #4 in the table, just fill it with `test=/root/test-52a9`:

| Bug No. | File Name |
|---------|-----------|
|   #1    | test-99bd |
|   #2    | test-e392 |
|   #3    | test-fb26 |
|   #4    | test-52a9 |
|   #5    | test-6c1b |
|   #6    | test-4b81 |
|   #7    | test-06c2 |
|   #8    | test-245c |
|   #9    | test-615d |
|   #10   | test-9d1d |
|   #11   | test-f0b0 |
|   #12   | test-94ed |


2. After the system boots up, wait and see the kernel panic, then it means the bug has been triggered, now manually stop recording.
```
rr_end_record
```
Then the process is expected to exit automatically.

***Note:** sometimes the recording of bug #5 may fail with message `Orphan event from kvm on cpu X, record failed!`, in this case you may need try again.

3. Replay the bug:

For each bug, use the following command, for bug #5, change the `-smp 1` to `-smp 2`:
```
../build/qemu-system-x86_64 -accel tcg -smp 1 -cpu Broadwell -no-hpet -m 2G -kernel <kernel image file> -append  "root=/dev/sda rw init=/lib/systemd/systemd tsc=reliable console=ttyS0 mce=off" -hda <disk image file> -device ivshmem-plain,memdev=hostmem -object memory-backend-file,size=4096M,share,mem-path=/dev/shm/ivshmem,id=hostmem -kernel-replay test1 -singlestep -D rec.log -nographic
```
After launching, enter the QEMU monitor and type `cont` to start replaying. During the replay, there could be kernel crash message showing up, don't worry, it's expected from the replay, your system is alright:).

***Note:*** the replay may progress slowly at first, but generally it goes very fast later as the crash happens, on average, each replay takes about 15 ~ 30min.

## CVEs
***Key results: Table 2***
(Estimated human time: 1h, machine time 1h ~ 1.5h)

Similar to the Syzbot bugs, for each bugs there's a specific binary to trigger the bug. Use the following command to launch the QEMU for record: 
```
../build/qemu-system-x86_64 -smp 1 -kernel <bzImage file> -accel kvm -cpu host -no-hpet -m 4G -append  "root=/dev/sda rw init=/lib/systemd/systemd tsc=reliable console=ttyS0 mce=off" -hda <disk image file> -object memory-backend-file,size=4096M,share,mem-path=/dev/shm/ivshmem,id=hostmem -device ivshmem-plain,memdev=hostmem -D rec.log -nographic -checkpoint-interval 0 -exit-record 1
```

For bzImage, please refer the table 2 in the paper to find the corresponding `bzImage<version>` and `vmlinuxRR-<version>`.

Under the VM's root directory, each CVE in the table has its own directory named cve-`<cve number>`, under the directory there's an file named `exploit` to trigger the bug.

### CVE-2024-1086
* After executing the exploit, the system could crash with `refcount_t: underflow; use-after-free.` message.
* This CVE's replay time is dramatically longer than the other ones as it has enabled KASAN (~1h), recommend to try other ones first.

Reproduce:
1. In the VM:
```
cd /root/cve-2024-1086/
```

2. Start recording and execute the `exploit`:
```
./exploit /usr/bin/su
```

### CVE-2022-0847
Reproduce:
1. In the VM, switch user:
```
cd /root/cve-2022-0847
su silver
```

2. Start recording, then execute:
```
./exploit /usr/bin/su
```

3. Stop recording.

### CVE-2022-0185
Reproduce:

1. In the VM, start recording, then execute:
```
cd /root/cve-CVE-2022-0185
./exploit
```

2. Stop recording.

Directly execute the `exploit`. This reproduction does not show anything specific on the screen, as there's a heap overflow happening secretly. However, during the replay, you can follow [here](https://github.com/dcheng69/CVE-2022-0185-Case-Study/blob/main/Poc/poc.md) to use gdb to examine whether the heap overflow has happened.

### CVE-2021-4154:
Reproduce:

1. In the VM, switch the user:
```
cd /root/cve-2021-4154
su silver
```

2. Start recording, then execute:
```
./exploit
```
If it's reproduced, it shows message like this:
```
[*] start slow write to get the lock
[*] got uaf fd 4, start spray....
[!] found, file id 3
[*] overwrite done! It should be after the slow write
[*] write done!
[   62.585512] VFS: Close: file count is 0
[   62.588002] VFS: Close: file count is 0
[!] succeed
[*] checking /etc/passwd

[*] executing command : head -n 5 /etc/passwd

DirtyCred works!
```

3. Stop recording


### CVE-2022-2639: 

1. In the VM, switch user:
```
cd /root/cve-2022-2639
su silver
```

2. Start recording, then execute bug binary:
```
./exploit
```
Then the exploit message will show up.

3. Stop recording

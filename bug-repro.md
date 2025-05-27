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

To replay, use the following command for each CVE:
```
../build/qemu-system-x86_64 -accel tcg -smp 1 -cpu Broadwell -no-hpet -m 4G -kernel <bzImage file> -append  "root=/dev/sda rw init=/lib/systemd/systemd tsc=reliable console=ttyS0 mce=off" -hda <disk image file>.qcow2 -device ivshmem-plain,memdev=hostmem -object memory-backend-file,size=4096M,share,mem-path=/dev/shm/ivshmem,id=hostmem -kernel-replay test1 -singlestep -D rec.log -nographic
```

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

# Example Output
[*] creating user namespace (CLONE_NEWUSER)...
[*] creating network namespace (CLONE_NEWNET)...
[*] setting up UID namespace...
[*] configuring localhost in namespace...
[*] setting up nftables...
[+] running normal privesc
[*] waiting for the calm before the storm...
[*] sending double free buffer packet...
[   51.815511] ==================================================================
[   51.816900] BUG: KASAN: use-after-free in ip_rcv+0x127/0x1a0
[   51.817992] Read of size 8 at addr ffff8881105b6650 by task exploit/213
[   51.819221]
...
[   52.713674] Code: 89 d6 0f 05 c3 66 2e 0f 1f 84 00 00 00 00 00 66 90 48 89 f8 4d 89 c2 48 89 f7 4d 89 c8 48 89 d6 4c 8b 4c 24 08 48 89 ca 0f 05 <c3> 66 0f 1f 44 00 00 e9 db f0
[   52.717070] RSP: 002b:00007ffcf867b558 EFLAGS: 00000202 ORIG_RAX: 000000000000002c
[   52.718494] RAX: ffffffffffffffda RBX: 0000000000402382 RCX: 000000000041ae29
[   52.719821] RDX: 0000000000000014 RSI: 00000000004a9140 RDI: 0000000000000005
[   52.721155] RBP: 00007ffcf867b5a0 R08: 00007ffcf867b5d0 R09: 0000000000000010
[   52.722491] R10: 0000000000000000 R11: 0000000000000202 R12: 00007ffcf867b8a8
[   52.723813] R13: 00007ffcf867b8c0 R14: 0000000000000000 R15: 0000000000000000
[   52.725162]  </TASK>
[   52.725593] Modules linked in:
[   52.726261] ---[ end trace 0000000000000000 ]---
[   52.727130] RIP: 0010:inet_frag_rbtree_purge+0x40/0xa0
[   52.728099] Code: 89 c5 45 31 e4 4c 89 ef 4c 89 eb e8 7a 3f 0d 00 4c 89 f6 48 89 df 49 89 c5 e8 5c 30 0d 00 48 89 dd 48 8d 7b 40 e8 90 3e 6b ff <48> 8b 5b 40 48 8d bd c8 00 08
[   52.731567] RSP: 0018:ffff88811b609ab8 EFLAGS: 00010282
[   52.732557] RAX: 0000000000000000 RBX: 732e6362696c2f64 RCX: ffffffff81c19570
[   52.733875] RDX: 0000000000000000 RSI: 0000000000000008 RDI: 732e6362696c2fa4
[   52.735204] RBP: 732e6362696c2f64 R08: 0000000000000001 R09: ffff88811b6271eb
[   52.736540] R10: ffffed10236c4e3d R11: 0000000063666572 R12: 0000000000010100
[   52.737859] R13: ffff888107569700 R14: ffff8881105b0170 R15: ffff8881105b6780
[   52.739183] FS:  0000000000529ab8(0000) GS:ffff88811b600000(0000) knlGS:0000000000000000
[   52.740723] CS:  0010 DS: 0000 ES: 0000 CR0: 0000000080050033
[   52.741812] CR2: 0000010c34e00000 CR3: 0000000103412000 CR4: 0000000000750eb0
[   52.743152] DR0: 0000000000000000 DR1: 0000000000000000 DR2: 0000000000000000
[   52.744490] DR3: 0000000000000000 DR6: 00000000fffe0ff0 DR7: 0000000000000400
[   52.745818] PKRU: 55555554
[   52.746342] Kernel panic - not syncing: Fatal exception in interrupt
[   52.747745] Kernel Offset: disabled
[   52.748424] ---[ end Kernel panic - not syncing: Fatal exception in interrupt ]---
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

# Example output:
[+] hijacking suid binary..
[+] dropping suid shell..
[+] restoring suid binary..
[+] popping root shell.. (dont forget to clean up /tmp/sh ;))
```

3. Stop recording.

### CVE-2022-0185
Reproduce:

1. In the VM, start recording, then execute:
```
cd /root/cve-2022-0185
./exploit
```

2. Stop recording.

This reproduction does not show anything specific on the screen, as there's a heap overflow happening secretly. However, during the replay, you can follow [here](https://github.com/dcheng69/CVE-2022-0185-Case-Study/blob/main/Poc/poc.md) to use gdb to examine whether the heap overflow has happened.

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

# Example Output:
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

# Example Output:
[*] exploit.c:1058 [1] initialize exploit environment ...
[+] exploit.c:535 get dp_family_id = 32
[+] exploit.c:541 get flow_family_id = 34
[*] exploit.c:1061 [2] create br to check if openvswitch works ...
[   36.284956] device br1337 entered promiscuous mode
[*] exploit.c:709 br1337 ifindex: 2
[*] exploit.c:1064 [3] leak kmalloc-0x400 (msg_msg->m_list.next / prev) ...
[*] exploit.c:766 [3-1] heap fengshui: drain 0x1000~0x10000 to make next allocation adjacent (using RX_RING buffer) ...
[*] exploit.c:783 [3-3] spray 0x400 (msg_msg + msg_msgseg) -> (0x1000 + 0x400) ...
[*] exploit.c:793 [3-4] free another half RX_RING buffer ...
[*] exploit.c:801 [3-5] trigger OOB to forge msg_msg->m_ts ...
[   38.048930] netlink: 1048 bytes leftover after parsing attributes in process `exploit'.
[   38.054969] openvswitch: netlink: Flow actions may not be safe on all matching packets.
[*] exploit.c:811 [3-6] find the corrupted msg_msg (list1_corrupted_msqid) ...
[+] exploit.c:817 [+] corrupted msg_msg found, id: 8
[*] exploit.c:822 [-] but the next object is not allocated by msg_msgseg
[*] exploit.c:833 [3-7] free all uncorrupted msg_msg ...
[*] exploit.c:837 [3-8] alloc 0x400*16 `msg_msg` chain to re-acquire the 0x400 slab freed by msg_msgseg ...
[-] exploit.c:858 [-] bad luck, we don't catch 0x400 msg_msg
[!] exploit.c:1066 retry ...
[*] exploit.c:766 [3-1] heap fengshui: drain 0x1000~0x10000 to make next allocation adjacent (using RX_RING buffer) ...
[*] exploit.c:783 [3-3] spray 0x400 (msg_msg + msg_msgseg) -> (0x1000 + 0x400) ...
[*] exploit.c:793 [3-4] free another half RX_RING buffer ...
[*] exploit.c:801 [3-5] trigger OOB to forge msg_msg->m_ts ...
[   39.900239] netlink: 1048 bytes leftover after parsing attributes in process `exploit'.
[   39.906893] openvswitch: netlink: Flow actions may not be safe on all matching packets.
[*] exploit.c:811 [3-6] find the corrupted msg_msg (list1_corrupted_msqid) ...
[+] exploit.c:817 [+] corrupted msg_msg found, id: 105
[*] exploit.c:833 [3-7] free all uncorrupted msg_msg ...
[*] exploit.c:837 [3-8] alloc 0x400*16 `msg_msg` chain to re-acquire the 0x400 slab freed by msg_msgseg ...
[*] exploit.c:862 [+] it works :)
[+] exploit.c:876 [+] leak list2_leak_msqid: 1028
[+] exploit.c:877 [+] leak list2_leak_mtype: 0x742
[+] exploit.c:878 [+] leak list2_uaf_msg_addr: 0xffff88810a599800
[+] exploit.c:879 [+] leak list2_uaf_mtype: 0x642
[*] exploit.c:883 [3-10] free all uncorrupted msg_msg ...
[*] exploit.c:1068 [4] do exploit step 2 ...
[*] exploit.c:892 [4-1] heap fengshui: drain 0x1000~0x10000 to make next allocation adjacent (using RX_RING buffer) ...
[*] exploit.c:909 [4-3] spray 0x400 (msg_msg + msg_msgseg) -> (0x1000 + 0x400) ...
[*] exploit.c:919 [4-4] free another half RX_RING buffer ...
[*] exploit.c:927 [4-5] trigger OOB to forge msg_msg->m_list.next ...
[   41.748999] netlink: 1024 bytes leftover after parsing attributes in process `exploit'.
[   41.755565] openvswitch: netlink: Flow actions may not be safe on all matching packets.
[*] exploit.c:934 [4-6] free uaf msg_msg from correct msqid (list2_leak_msqid)
[*] exploit.c:939 [4-7] spray sk_buff->data to re-acquire the 0x400 slab freed by msg_msg
[*] exploit.c:953 [4-8] free sk_buff->data using fake msqid
[*] exploit.c:956 [+] freed using msqid 171
[*] exploit.c:962 [4-9] spray 0x100 pipe_buffer to re-acquire the 0x400 slab freed by sk_buff->data
[*] exploit.c:979 [4-10] free sk_buff->data to make pipe_buffer become UAF
[+] exploit.c:995 [+] uaf_pipe_idx: 0
[*] exploit.c:1004 [4-11] edit pipe_buffer->flags = PIPE_BUF_FLAG_CAN_MERGE
[*] exploit.c:1016 [4-12] try to overwrite /bin/mount
[*] exploit.c:1025 [*] see if /bin/mount changed ...
[+] exploit.c:1038 [+] exploit success!!!
[*] exploit.c:1072 [5] notify sub-process to execute suid-shell ...
[*] exploit.c:1078 [6] begin to execute suid-shell ...
```
Then the exploit message will show up.

3. Stop recording

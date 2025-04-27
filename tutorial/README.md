# KRR (Kernel RR)

All you need:
* KRR's kernel image and its vmlinux
* A rootfs disk image

1. Launch the guest, in the example below, it takes 2GB for the guest RAM, additionally, it also takes 4GB for the event trace, so make sure you have enough memory on your machine:
```
cd qemu-tcg-kvm/build
../build/qemu-system-x86_64 -smp 1 -kernel <your kernel image> -accel kvm -cpu host -no-hpet -m 2G -append  "root=/dev/sda rw init=/lib/systemd/systemd tsc=reliable console=ttyS0" -hda <your root disk image> -object memory-backend-file,size=4096M,share,mem-path=/dev/shm/ivshmem,id=hostmem -device ivshmem-plain,memdev=hostmem -nographic
```

2. After getting into the system, press `ctrl+A` and `C` to enter the QEMU monitor command, and enter:
```
rr_record test1
```
Note that "test1" is the name of your record, it could be other names.

This will output things below:
```
(qemu) rr_record test1
enabled in ivshmem
Paused VM, start taking snapshot
Snapshotted for test1
Snapshot taken, start recording...
Removing existing log files: kernel_rr.log
Reset dma sg buffer
Initial queue header enabled=1
```

3. Execute things you want to record;

4. To finish the record session, get into the QEMU monitor command again, and enter:
```
rr_end_record
```
This will have the output below that summarizes the record data, like the number of each type of events:
```
root@wintermute:~# (qemu) rr_end_record
disabled in ivshmem
event number = 0
current pos 163053, rotated_bytes 0, current_bytes 6159268, total_bytes 6159268
Getting result
Result buffer 0x0
=== Event Stats ===
Interrupt: 612
Syscall: 335
Exception: 168
CFU: 180       -> Data Copy from User
GFU: 407       -> Get from user
IO Input: 5081      -> IO Instruction
RDTSC: 154463
RDSEED: 4
PTE: 1799           -> Page Table Entry Access
Inst Sync: 0
DMA Buf Size: 151552
Total Replay Events: 163053
Time(s): 38.17
synced queue header, current_pos=10872
writing queue header with 10872, pos=48
Start persisted event
[kernel_rr_dma-9.log] Logged entry number 20
[kernel_rr_dma-40.log] No dma entry generated
Total dma buf cnt 107 size 442368
[kernel_rr_network.log] No dma entry generated
network entry number 0, total net buf 0
```

5. After finishing the record session, you get the files below, which are necessary to get it replayed:
```
kernel_rr.log: stores the event trace.
kernel_rr_dma-<number>.log: stores the disk DMA data, <number> refers to the device id.
kernel_rr_network.log: stores the network data.
test1: initial snapshot file of your system, its name is the same as the record session name you give in step 6.
```

### Important to Notice
* KRR has not yet supported multiple VMs being recorded at the same time yet (one of TODOs).
* If a record session is interrupted without "rr_end_record", then next time launching the VM would be likely to directly crash, as KRR currently has not supported such automatically recovery case. The way to workaround this is to reload the KRR KVM module: go to kernel-rr-linux, then `sh replace.sh`.
* KRR has not yet supported multiple recording sessions on one single VM's runtime, so when finish recording, if you want to record again, you need to launch a new QEMU process.


## Replay
Using KRR for replay doesn't need KVM's support since it's purely userspace (QEMU TCG), what you need is just an initial snapshot and event trace.

1. Replay prepare:
As an example, my replay snapshot is named as "test1".

First, make sure you have these 4 files under your `build` directory from last step:
- test1: the snapshot file storing VM's initial memory state;
- kernel_rr.log: main event trace;
- kernel_rr_dma-`<number>`.log: Disk DMA data;
- kernel_rr_network.log: Network data.

You also need the original disk image file you used for record, it's not going to be actually read in replay, just for consistent hardware configuration between record and replay.

2. Generate kernel symbols:
When using a different kernel image for replay, make sure to generate the kernel symbols and re-compile QEMU:
```
cd qemu-tcg-kvm/build
bash ../kernel_rr/generate_symbol.sh <absolute path to your vmlinux> <absolute path of your KRR QEMU directory>
```
KRR replayer needs some kernel symbol information to trap certain kernel code.

Symbol generation has the output below:
```
[root@tianren kernel_rr]# bash generate_symbol.sh /home/projects/linux-6.1.0/vmlinux /home/projects/qemu-tcg-kvm/
GNU gdb (GDB) Fedora 12.1-2.fc36
Copyright (C) 2022 Free Software Foundation, Inc.
License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.
Type "show copying" and "show warranty" for details.
This GDB was configured as "x86_64-redhat-linux-gnu".
Type "show configuration" for configuration details.
For bug reporting instructions, please see:
<https://www.gnu.org/software/gdb/bugs/>.
Find the GDB manual and other documentation resources online at:
    <http://www.gnu.org/software/gdb/documentation/>.

For help, type "help".
Type "apropos word" to search for commands related to "word"...
Reading symbols from /home/projects/linux-6.1.0/vmlinux...
{sysname = "Linux", '\000' <repeats 59 times>, nodename = "(none)", '\000' <repeats 58 times>, release = "6.1.0-rc7-ga9bf5136035e-dirty", '\000' <repeats 35 times>, version = "#787 SMP PREEMPT_DYNAMIC Sat Dec 28 04:23:24 EST 2024", '\000' <repeats 11 times>, machine = "x86_64", '\000' <repeats 58 times>, domainname = "(none)", '\000' <repeats 58 times>}
Symbol generation finished, please recompile the KRR QEMU
```

3. Start replay:
In summary, the replay QEMU arguments are almost the same as the arguments for the record, except the following:
```
-accel tcg  // Change from kvm to tcg
-cpu Broadwell // Change from "host" to a CPU Model
``` 

Added the following arguments:
```
-kernel-replay <record name> -singlestep
```
The `<record name>` is the name the you specified when executing `rr_record <record name>` in the record step.

**Apart from the arguments mentioned above, the other VM configuration should be exactly the same as record.**

Example:
If your record arguments are like below:
```
../build/qemu-system-x86_64 -smp 1 -kernel <your kernel image> -accel kvm -cpu host -no-hpet -m 2G -append  "root=/dev/sda rw init=/lib/systemd/systemd tsc=reliable console=ttyS0" -hda <your root disk image> -object memory-backend-file,size=4096M,share,mem-path=/dev/shm/ivshmem,id=hostmem -device ivshmem-plain,memdev=hostmem -D rec.log -nographic
```

Then the corresponding replay argument:
```
../build/qemu-system-x86_64 -accel tcg -smp 1 -cpu Broadwell -no-hpet -m 2G -kernel <your kernel image> -append  "root=/dev/sda rw init=/lib/systemd/systemd tsc=reliable console=ttyS0" -hda <your root disk image> -device ivshmem-plain,memdev=hostmem -object memory-backend-file,size=4096M,share,mem-path=/dev/shm/ivshmem,id=hostmem -kernel-replay test1 -singlestep -D rec.log -nographic
```

After launched, it stays paused, enter QEMU monitor command `cont` to start the replay execution:
```
In replay mode, execute 'cont' to start the replay

(qemu) cont
(qemu) Replayed events[1000/3951]
Replayed events[2000/3951]
Replayed events[3000/3951]
...
```

At the end, it displays something below as a summary of the replay:
```
Replay executed in 1.070952 seconds
=== Event Stats ===
Interrupt: 174
Syscall: 289
Exception: 168
CFU: 130
GFU: 409
IO Input: 675
RDTSC: 781
RDSEED: 0
PTE: 1321
Inst Sync: 0
DMA Buf Size: 0
Total Replay Events: 3951
Time(s): 0.00
```

### Use gdb to debug replay:
If you wanna debug it using gdb, you should firstly have the `vmlinux` of the same kernel used by the guest.

1. Simply add `-S -s` options into the QEMU replay commandline above, this will start a gdb-server insdie QEMU.
2. In another command line, execute 
```
gdb vmlinux
```
3. In gdb console, execute:
```
target remote :1234
```
This will connect to the gdb-server.

4. Then you can just use gdb commands just like debugging a regular program.

### Log out instructions
Using following parameter could log out instructions & associated registers from N1th to N2th instruction on CPU0.
```
-replay-log-bound cpu=0,start=N1,end=N2
```
The log file is specified by `-D logfile`.

## Use NVMe device
KRR also supports recording with emulated NVMe disk, add the following arguments:
```
-drive file=<your disk image file>,id=nvm,if=none -device nvme,serial=deadbeef,drive=nvm
```

For NVMe, KRR also supports `rr-ignore=true` parameter, if specified, the device's inputs will be ignored during the record. This could be used if the device is used for kernel bypass applications, and please make sure the device is already unbinded when start recording.

Full command:
```
-drive file=<your disk image file>,id=nvm,if=none -device nvme,serial=deadbeef,drive=nvm,rr-ignore=true
```

## Make your own recordable kernel
Due to its split-recorder design, KRR requires some modifications to the guest linux kernel. The full changes refers to this [repo](https://github.com/tianrenz2/linux-6.1.0/tree/smp-rr), but here is a single [patch file](0001-Support-KRR-guest-agent.patch) that contains all the changes. To apply the changes, mv the file to your kernel source code directory and execute:
```
git apply 0001-Support-KRR-guest-agent.patch
```
***Tips: this patch file is based on Linux 6.1.0, there might be conflicts when the kernel version is too far (e.g., 5.1.x), use the --reject option to show the conflicting files and try to resolve***

To compile, we can refer to a sample [.config](rr_guest_config) file, note that this config file is also based on linux 6.1.0, so depending on your own linux kernel version, it might be somehow different.


## KRR Development Guide
Debugging message:
In `include/sysemu/kernel-rr.h`, the macro below is not defined by default:
```
#define RR_LOG_DEBUG 1
```
If define this macro, there would be more detailed record/replay log message.

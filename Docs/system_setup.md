# Things to Do
- (Optional)Prepare WIN10
- Create Ubuntu16.04 Installation USB Drive
- Install Ubuntu16.04
- Install ROS
- Install TensorFlow

# Prepare WIN10
Assume you are going to dual boot ***Ubuntu*** alonside your ***Windows***

## Step-1. Check BIOS Mode
Search "System Information" in the search bar and open it. Make sure in `System Summary`, for `Item` `BIOS Mode` its corresponding `Value` is `UEFI`.
![sys_info](https://github.com/linZHank/two_loggers/blob/master/Docs/images/sys_info.PNG)

> If `Value` is `Legacy`, please refer [this guide](https://docs.microsoft.com/zh-cn/windows/deployment/mbr-to-gpt) to switch the disk partition style from MBR to GPT.
> - Right click `Win` button on bottom left, select `Disk Manager`, make sure *Window* is installed on Disk 0. If on other disk, you'll have to change the disk index accordingly.
> - Fire up `Command Prompt` as administrator
```console
X:\> DiskPart

DISKPART> list volume

Volume ###  Ltr  Label        Fs     Type        Size     Status     Info
  ----------  ---  -----------  -----  ----------  -------  ---------  --------
  Volume 0     F   CENA_X64FRE  UDF    DVD-ROM     4027 MB  Healthy
  Volume 1     C   System Rese  NTFS   Partition    499 MB  Healthy
  Volume 2     D   Windows      NTFS   Partition     58 GB  Healthy
  Volume 3     E   Recovery     NTFS   Partition    612 MB  Healthy    Hidden
```

> Note which volume is labeled as *Windows*, in this case **Volume 2**
```console
DISKPART> exit

Leaving DiskPart...

X:\>mbr2gpt /convert /disk:0 /allowFullOS

MBR2GPT will now attempt to convert disk 0.
If conversion is successful the disk can only be booted in GPT mode.
These changes cannot be undone!

MBR2GPT: Attempting to convert disk 0
MBR2GPT: Retrieving layout of disk
MBR2GPT: Validating layout, disk sector size is: 512 bytes
MBR2GPT: Trying to shrink the system partition
MBR2GPT: Trying to shrink the OS partition
MBR2GPT: Creating the EFI system partition
MBR2GPT: Installing the new boot files
MBR2GPT: Performing the layout conversion
MBR2GPT: Migrating default boot entry
MBR2GPT: Adding recovery boot entry
MBR2GPT: Fixing drive letter mapping
MBR2GPT: Conversion completed successfully
MBR2GPT: Before the new system can boot properly you need to switch the firmware to boot to UEFI mode!
```
> - Reboot your computer. Now, your *Windows* is on a GPT disk, and your BIOS mode should be `UEFI`.

## Step-2 Shrink Disk
- Right click `WIN` button on bottom left, select `Disk Manager`, locate the block for drive **(C:)**, right click on that block to bring up `Shrink C:` dialog.
- At **"Enter the amount of space to shrink in MB"**, input the space you want allocate to ***Ubuntu***. Then **`Shrink`**
> recommend: at least 50000 (~50G)
![shrink_disk](https://github.com/linZHank/two_loggers/blob/master/Docs/images/shrink_disk.PNG)

# Create Ubuntu16.04 Installation USB Drive
Refer to [Create a bootable USB stick on Windows](https://tutorials.ubuntu.com/tutorial/tutorial-create-a-usb-stick-on-windows#0). Note: make sure you download the [Ubuntu 16.04 desktop image](http://releases.ubuntu.com/16.04/)

# Install Ubuntu 16.04
Insert the just created Ubuntu bootable USB drive and reboot.

## Step-1 BIOS Settings
A few things you'll have to make sure.
    1. The storage option should be **AHCI** instead of ~~RAID~~.
    2. **Disable** the option of "fast boot".
    3. Set your system to boot up from **USB Drive**
    4. **Save and Exit**

## Step-2 Install Ubuntu from USB
- A (purplish) screen will show up if successfully boot up from USB. This interface is called **GRUB**, and in this grub you'll have 4 options (`Try Ubuntu without installing`; `Install Ubuntu`; `OEM install (for manufacturers)`; `Check disc for defects`)
- Select first option: **Try Ubuntu without installing**. This should brings you to the Ubuntu tryout interface (It looks exactly the same as the installed one).
![try_ubuntu](https://github.com/linZHank/two_loggers/blob/master/Docs/images/try_ubuntu.PNG)
- Double click the only icon on desktop to **Install Ubuntu 16.04LTS**
- "Continue" -\> "**don't** download update, **don't** install 3rd party software" -\> "Continue"
- Make sure the first option is exactly **Install Ubuntu alongside Windows Boot Manager**. If not, go back to beginning of this guide and make sure your boot disk has been switched to GPT format.
- "Continue" all the way till end of installation.
- Reboot and you are all set for a dual-boot(***Ubuntu*** and ***Windows***) machine. 

# Install ROS

# Install TensorFlow
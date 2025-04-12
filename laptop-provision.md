## Setup Standalone Connection
Use the Jubilee Docs: https://jubilee3d.com/index.php?title=Connecting_to_Jubilee

## For both Mac and Windows
- After setting up everything below, there's a few more we need for the workshop:
  - `python3 -m pip install opencv_contrib_python`
  - `python3 -m pip install matplotlib`
  - `python3 -m pip install jupyter`
  - Can probably throw these in a requirements file but noting it here before I forget

## Mac
### Science Jubilee + Workshop Repo
Steps to provision Mac laptop:
- `mkdir 2025PoseWorkshop`
- `cd 2025PoseWorkshop`
- `python3 -m venv .venv`
- `source .venv/bin/activate`
- `git clone https://github.com/machineagency/science-jubilee.git`
- `git clone https://github.com/machineagency/POSE25.git`
- `cd science-jubilee`
- `python3 -m pip install --upgrade pip`
- `python3 -m pip install -e .`
- `python3 -m pip install jupyterlab`
- `python3 -m ipykernel install --user --name=POSE25`
  - `python3 -m pip install ipykernel` if needed
- If your Python version raises an OpenSSL warning when running science-jubilee:
	- `python3 -m pip uninstall urllib3`
	- `python3 -m pip install urllib3==1.26.7`
  
### VS Code
- Install from [code.visualstudio.com](code.visualstudio.com)
- Move it to Applications folder
- Open the `2025PoseWorkshop` folder from above and open one of the notebooks in the `POSE2025` repo
- Can install the recommended things to run notebook in vs code
- Use the command pallette and search for `jupyter` to install jupyter extension
- Restart vs code
- Now if you choose 'Use jupyter kernel' the `POSE25` kernel will appear
- If pylance warnings appears, the quickfix to add `src/` to path will fix it

## Windows
### Science Jubilee + Workshop
- Open command prompt as administrator
- `wsl --install -d Ubuntu --web-download` to install windows subsystem for linux
- Search 'Windows Features' in settings, find 'windows subsystem for linux', and enable it
- Restart Computer
- Open command prompt as adminstrator and run `wsl` command again
  - It'll ask for a username/password
  - I used username: `machine` and password: `agency`
- `mkdir 2025PoseWorkshop`
- `cd 2025PoseWorkshop`
- `git clone https://github.com/machineagency/science-jubilee.git`
- `git clone https://github.com/machineagency/POSE25.git`
- `sudo apt update`
- `sudo apt upgrade`
- `sudo apt install python3.10-venv`
  - Assuming the `python3 -V` is 3.10
- `python3 -m venv .venv`
- `source .venv/bin/activate`
- `python3 -m pip install --upgrade pip`
- go to the science jubilee folder `cd science-jubilee`
- `python3 -m pip install -e .`
- `python3 -m pip install jupyterlab`
- `python3 -m ipykernel install --user --name=POSE25`

#### VS Code
- Install from [code.visualstudio.com](code.visualstudio.com)
- Add desktop icon and add code to path in the dialog box
- Install the WSL extension in VS Code
- Connect to WSL by opening command pallette (F1 on Windows) and searching for WSL and find 'connect to WSL'
- Open `2025PoseWorkshop` folder from above in VS Code and open a notebook from the `POSE25` directory
- Can install the recommended things to run notebook
- Use command pallette and search for `jupyter` to install jupyter extension
- Restart VC code
- Now if you choose 'use jupyter kernel' the `POSE25` kernel will appear
- if yellow line appears for pylance warning, the quickfix to add src/ to path will fix it

#### Serial device configuration
WSL runs in a virtualized environment that doesn't have direct access to hardware by default. To use serial devices, we can **forward USB device to WSL**.
1. Run Windows Powershell as Administrator
2. # Install usbipd
   winget install usbipd
   # list all usb devices
   usbipd list
   # if there is any error, download the installer directly from GitHub instead of using winget:
	Go to: https://github.com/dorssel/usbipd-win/releases
	Download the latest MSI installer (like usbipd-win_x.x.x.msi)
	Run the MSI installer as administrator
	After installation, restart your PowerShell or Command Prompt as Administrator
   # Bind the USB device (replace BUSID with your device's ID from the list)
   usbipd bind -b BUSID
   # Attach to WSL
   usbipd attach -b BUSID --wsl
3. In WSL terminal:
   # Install required packages
   sudo apt update
   sudo apt install linux-tools-generic hwdata
   # Set up usbip
   sudo update-alternatives --install /usr/local/bin/usbip usbip /usr/lib/linux-tools/*/usbip 20
   # Check if device appears
   ls -l /dev/ttyUSB* /dev/ttyACM*
3. If you see "Permission Denied" on COM Port
   # in WSL terminal, add your user to the dialout group
   sudo usermod -a -G dialout $USER
   sudo usermod -a -G tty $USER
   # Or, change device permissions directly. Replace 'ttyACM0' with your actual device path
   sudo chmod 666 /dev/ttyACM0

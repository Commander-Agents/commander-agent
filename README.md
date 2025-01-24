# Compile for windows

`pyinstaller --onefile --name agent --noconsole main.py`

And for startup

```python
import os
import winreg

def add_to_startup(executable_path):
    key = winreg.HKEY_LOCAL_MACHINE
    subkey = r"Software\Microsoft\Windows\CurrentVersion\Run"
    with winreg.OpenKey(key, subkey, 0, winreg.KEY_SET_VALUE) as registry_key:
        winreg.SetValueEx(registry_key, "MyAgent", 0, winreg.REG_SZ, executable_path)

# Exemple d'utilisation
add_to_startup(r"C:\Path\To\agent.exe")
```

# Compile for linux

`pyinstaller --onefile --name agent main.py`

For startup, create file in `/etc/systemd/system/commander-agent.service`
```sh
[Unit]
Description=Commander Agent
After=network.target

[Service]
ExecStart=/path/to/agent
Restart=always
User=root
Group=root

[Install]
WantedBy=multi-user.target
```

Then
```sh
sudo systemctl daemon-reload
sudo systemctl enable agent.service
sudo systemctl start agent.service
```

# Compile for MacOS

`pyinstaller --onefile --name agent main.py`

Then for startup, create a file in `~/Library/LaunchAgents/com.commander.agent.plist`
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.myagent.agent</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/agent</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

Then `launchctl load ~/Library/LaunchAgents/com.myagent.agent.plist`




# Enrollment process (Diffie-Hellman)

1. Server generate a RSA key pair (should be done only once)
2. Agent generate a RSA key pair
3. Agent trigger the enrollment, sending :
    - IP & Port
    - Hostname
    - Public key
4. Server generate a secret token to sign with HMAC the exchanges between the server and the agent. The token is specific for each agent
5. Server encrypt the secret with the public key of the Agent and send back the encrypted secret & the server public key. It also save the public key of the agent
6. Agent decrypt & save the secret.

And all the next exchanges are encrypted using each other public key and signed using HMAC with the shared token.
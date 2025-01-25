# How to start ?

Your server must be setup.

1. Run `python -m pip install -r requirements.txt`
2. Configure the `./config.json` file with the following content :
```json
{
    "api_url": "http://localhost:8000/api",
    "agent_port": 62026,
    "agent_protocol": "tcp",
    "keepalive_interval": 300,
    "mqtt": {
        "broker": "localhost",
        "port": "1883"
    }
}
```
3. You must update the `api_url` with the URL of your server API
4. Same for `mqtt` section
    - You can add an optionnal `"hostname": "my_agent_0001"` to force the agent name, if not used, the agent will use the computer Hostname (recommended)
5. Run `python ./main.py`


# How to re-install agent ?

1. Delete the folder `./keys/`
2. Run `python ./main.py`
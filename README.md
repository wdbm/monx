# monx

# introduction

The program monx can monitor events and execute corresponding actions according to a specified configuration. In practice, monx is used to monitor for keystroke events and then to execute commands mapped to these keystroke events in a specified configuration. The configuration file should feature a Markdown list of the following form:

    - event-execution-map
       - <event>
          - description: <natural language description>
          - command: <command>

An example configuration file is included.

# prerequisites

## docopt

```Bash
sudo apt-get -y install python-docopt
```

## pyrecon

- <https://github.com/wdbm/pyrecon>

# ideas

- <https://github.com/autokey/autokey>

---
output:
  pdf_document: default
  html_document: default
---
# Paxer

**Efficiently deploy .deb packages across multiple hosts via SSH.**

Paxer is a streamlined command-line tool designed to automate the setup of SSH access and deployment of .deb packages to remote Linux hosts. Leveraging Python, click, and paramiko, it offers a robust solution for managing distributed systems with ease.

## Key Features

    SSH Key Configuration: Seamlessly initialize SSH access across multiple hosts.
    Multi-Host Deployment: Deploy .deb packages to all configured targets in one command.
    IP Range Support: Target hosts by IP range or explicit list, with live host detection.
    Flexible Authentication: Unified or per-host password options.

## Installation

Install Paxer via PyPI:

bash
pip install paxer
Commands

Paxer provides two core commands for setup and deployment.
pax init

Configure SSH access for target hosts:
```bash
pax init --range 192.168.1.31-46 --username myuser
Options

    -r/--range: Specify an IP range (e.g., 192.168.1.31-46).
    -i/--ip: List specific IPs (e.g., 192.168.1.1,192.168.1.2).
    -e/--exclude: Exclude IPs (e.g., 192.168.1.33).
    -p/--per-ip-password: Prompt for passwords per IP.
    -u/--username: SSH username (defaults to current user).
```

## Behavior

Generates an SSH key pair at ~/.ssh/pax_key, distributes the public key to live hosts, and saves targets to ~/.pax_targets.
pax deploy

Deploy a .deb package to initialized hosts:

```bash
pax deploy mypackage.deb --username myuser
Options

    package_path: Path to the .deb file.
    -p/--per-ip-password: Prompt for sudo passwords per IP.
    -u/--username: SSH username (defaults to current user).
```

## Behavior

Uses the SSH key from init to transfer and install the .deb package on each host listed in ~/.pax_targets.
Example Workflow
1. Initialize Hosts

Set up SSH access:
```bash
pax init --range 192.168.1.31-34 --username ubuntu

Output:
text
Live hosts: ['192.168.1.31', '192.168.1.32', '192.168.1.34']
192.168.1.31: SSH key setup
192.168.1.32: SSH key setup
192.168.1.34: SSH key setup
Initialized 3 hosts.
2. Deploy a Package
```

Install nginx on all targets:
```bash
pax deploy nginx_1.18.0.deb --username ubuntu

Output:
text
192.168.1.31: Deployed - nginx (1.18.0) installed
192.168.1.32: Deployed - nginx (1.18.0) installed
192.168.1.34: Deployed - nginx (1.18.0) installed
```

## Prerequisites

    Python 3.6 or higher
    click>=8.1.3
    paramiko>=3.4.0

## Configuration Notes

    **SSH Key:** Stored at ~/.ssh/pax_key. Ensure it’s secure.
    **Sudo Privileges:** Required for dpkg -i during deployment.
    **Error Handling:** Retries passwords twice per IP before skipping.

## Contributing

Contributions are welcome to enhance Paxer’s capabilities.

    Clone the repository:
```bash
    git clone https://github.com/detox-24/pax.git
```      

## License

Released under the MIT License.
Future Enhancements

    Support for .tar.gz files
    Extending installation over a subnet

Developed by Sathiya Moorthi P

GitHub | PyPI
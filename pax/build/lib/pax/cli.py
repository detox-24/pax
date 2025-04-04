import click
import socket
import paramiko
import os
import subprocess
import re

def parse_range(range_str):
    base, limits = range_str.rsplit(".", 1)
    start, end = map(int, limits.split("-"))
    return [f"{base}.{i}" for i in range(start, end + 1)]

def check_live_ips(ips, exclude=None):
    live_ips = []
    exclude_set = set(exclude.split(",")) if exclude else set()
    for ip in ips:
        if ip not in exclude_set and socket.socket().connect_ex((ip, 22)) == 0:
            live_ips.append(ip)
    return live_ips

def setup_ssh_key(ip, username, password, pub_key):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username=username, password=password)
        ssh.exec_command(f"mkdir -p ~/.ssh && echo '{pub_key}' > ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys")
        ssh.close()
        return True, None
    except paramiko.AuthenticationException:
        return False, "Incorrect SSH password"

def deploy_package(ip, package_path, username, key_path, password):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username=username, key_filename=key_path)
        sftp = ssh.open_sftp()
        remote_path = "/tmp/" + os.path.basename(package_path)
        sftp.put(package_path, remote_path)
        sftp.close()
        stdin, stdout, stderr = ssh.exec_command(f"sudo -S dpkg -i {remote_path} && rm {remote_path}", get_pty=True)
        stdin.write(f"{password}\n")
        stdin.flush()
        output = stdout.read().decode()
        error = stderr.read().decode()
        ssh.close()
        if error and "incorrect password" in error.lower():
            return False, "Incorrect sudo password"
        elif error:
            return False, f"Deploy failed: {error.strip()}"
        match = re.search(r"Setting up (\S+) \(([^)]+)\)", output)
        if match:
            pkg, ver = match.groups()
            return True, f"{pkg} ({ver}) installed"
        return True, "Package installed"
    except paramiko.AuthenticationException:
        return False, "SSH auth error"
    except Exception as e:
        return False, f"Error: {str(e)}"

@click.group()
def cli():
    pass

@cli.command()
@click.option("-r", "--range", help="IP range, e.g., 192.168.1.3-7")
@click.option("-i", "--ips", "--ip", help="Comma-separated IPs, e.g., 192.168.1.3,192.168.1.7")
@click.option("--exclude", help="IPs to exclude, e.g., 192.168.1.5")
@click.option("-p", "--per-ip-password", is_flag=True, help="Prompt for passwords per IP")
@click.option("-u", "--username", default=os.getlogin(), help="SSH username (default: current user)")
def init(range, ips, exclude, per_ip_password, username):
    key_path = os.path.expanduser("~/.ssh/pax_key")
    pub_key_path = key_path + ".pub"
    
    if not os.path.exists(key_path):
        subprocess.run(["ssh-keygen", "-t", "rsa", "-N", "", "-f", key_path], check=True)
        click.echo("Generated Pax SSH key pair.")
    
    with open(pub_key_path, "r") as f:
        pub_key = f.read().strip()
    
    if range and ips:
        click.echo("Error: Use --range or --ips, not both.")
        return
    if not (range or ips):
        click.echo("Error: Specify --range or --ips.")
        return
    
    targets = parse_range(range) if range else ips.split(",")
    live_ips = check_live_ips(targets, exclude)
    click.echo(f"Live hosts: {live_ips}")
    
    if not live_ips:
        click.echo("No live hosts found.")
        return
    
    ip_passwords = {}
    failed = []
    if per_ip_password:
        for ip in live_ips:
            retries = 2
            while retries >= 0:
                password = click.prompt(f"Enter SSH password for {username}@{ip}:", hide_input=True)
                success, error = setup_ssh_key(ip, username, password, pub_key)
                if success:
                    ip_passwords[ip] = password
                    click.echo(f"{ip}: SSH key setup")
                    break
                click.echo(f"{ip}: {error}")
                retries -= 1
            if retries < 0:
                click.echo(f"{ip}: Skipped after 2 retries")
                failed.append(ip)
    else:
        password = click.prompt(f"Enter SSH/sudo password for {username} across targets", hide_input=True)
        for ip in live_ips:
            success, error = setup_ssh_key(ip, username, password, pub_key)
            if success:
                ip_passwords[ip] = password
                click.echo(f"{ip}: SSH key setup")
            else:
                click.echo(f"{ip}: {error}")
                failed.append(ip)
    
    if failed:
        click.echo(f"Failed to initialize: {failed}")
        live_ips = [ip for ip in live_ips if ip not in failed]
    
    if live_ips:
        with open(os.path.expanduser("~/.pax_targets"), "w") as f:
            f.write("\n".join(live_ips))
        click.echo(f"Initialized {len(live_ips)} hosts.")
    else:
        click.echo("No hosts initialized.")

@cli.command()
@click.argument("package_path")
@click.option("-p", "--per-ip-password", is_flag=True, help="Prompt for sudo passwords per IP")
@click.option("-u", "--username", default=os.getlogin(), help="SSH username (default: current user)")
def deploy(package_path, per_ip_password, username):
    key_path = os.path.expanduser("~/.ssh/pax_key")
    if not os.path.exists(key_path):
        click.echo("Error: Run 'pax init' first to set up SSH keys.")
        return
    
    with open(os.path.expanduser("~/.pax_targets"), "r") as f:
        live_ips = f.read().splitlines()
    
    if not live_ips:
        click.echo("Error: No targets initialized. Run 'pax init'.")
        return
    
    ip_passwords = {}
    failed = []
    if per_ip_password:
        for ip in live_ips:
            retries = 2
            while retries >= 0:
                password = click.prompt(f"Enter sudo password for {username}@{ip} :", hide_input=True)
                success, result = deploy_package(ip, package_path, username, key_path, password)
                if success:
                    ip_passwords[ip] = password
                    click.echo(f"{ip}: Deployed - {result}")
                    break
                click.echo(f"{ip}: Failed - {result}")
                if "incorrect sudo password" not in result.lower():
                    failed.append(ip)
                    break
                retries -= 1
            if retries < 0:
                click.echo(f"{ip}: Skipped after 2 retries")
                failed.append(ip)
    else:
        password = click.prompt(f"Enter sudo password for {username} across targets", hide_input=True)
        for ip in live_ips:
            success, result = deploy_package(ip, package_path, username, key_path, password)
            if success:
                ip_passwords[ip] = password
                click.echo(f"{ip}: Deployed - {result}")
            else:
                click.echo(f"{ip}: Failed - {result}")
                failed.append(ip)
    
    if failed:
        click.echo(f"Failed to deploy: {failed}")
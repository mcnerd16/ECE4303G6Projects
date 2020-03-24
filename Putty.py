import paramiko,spur, sys, io
import msvcrt
import spur.ssh
from contextlib import redirect_stdout

class _Getch:
    """Gets a single character from standard input.  Does not echo to the
screen."""
    def __init__(self):
        try:
            self.impl = _GetchWindows()
        except ImportError:
            self.impl = _GetchUnix()

    def __call__(self): return self.impl()
class _GetchUnix:
    def __init__(self):
        import tty, sys

    def __call__(self):
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch
class _GetchWindows:
    def __init__(self):
        import msvcrt

    def __call__(self):
        import msvcrt
        return msvcrt.getch()
getch = _Getch()

ssh_client=paramiko.SSHClient()
ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
hostCmd = input("Enter Hostname:")
portCmd = input("Enter Port Number:")
userCmd = input("Enter Username:")
print("Enter Password:")
done = False
passCmd = ""
while done == False:
    ch = getch.__call__()
    if ch.decode("utf-8") == '\r':
        done = True
    elif ch.decode("utf-8") == '\x08':
        if len(passCmd) > 0:
            passCmd = passCmd.rpartition(passCmd[len(passCmd) - 1])[0]
    else:
        passCmd += ch.decode("utf-8")
print("Connecting....")
try:
    shell = spur.SshShell(hostname=hostCmd, port=portCmd, username=userCmd, password=passCmd, missing_host_key=spur.ssh.MissingHostKey.accept)
    result = shell.run(["echo", "hello"])
    cmdInput = input("Welcome to " + hostCmd + ":\n>>")
    while (cmdInput != "exit"):
        result = shell.run(["sh", "-c",cmdInput], allow_error=True)
        if result.return_code <= 4:
            if result != 0:
                print(result.output.decode("utf-8"))
            if result.return_code != 0:
                result = shell.run(["sh", "-x",cmdInput], allow_error=True)
                print(result.to_error())
        else:
            print(result.to_error())
        cmdInput = input(">>")
except Exception as inst:
    print("Connection Failed.")
    print(inst)
finally:
    ssh_client.close()
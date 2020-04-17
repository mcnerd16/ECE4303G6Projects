import paramiko,spur, sys, io, signal
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
        import tty, sys, termios, getch

    def __call__(self):
        import sys, tty, termios, getch
#        fd = sys.stdin.fileno()
#        old_settings = termios.tcgetattr(fd)
#        try:
#            tty.setraw(sys.stdin.fileno())
#            ch = sys.stdin.read(1)
#        finally:
#            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
#        return ch
#        return getch.getch()
        import readchar
        return readchar.readchar()
class _GetchWindows:
    def __init__(self):
        import msvcrt

    def __call__(self):
        import msvcrt
        return msvcrt.getch()
getch = _Getch()

hostCmd = input("Enter Hostname:")
portCmd = input("Enter Port Number:")
userCmd = input("Enter Username:")
print("Enter Password:")
done = False
passCmd = ""
while done == False:
    ch = getch.__call__()
    try:
        ch = bytes(ch,'utf-8')
    except:
        ch = ch
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
    user = shell.run(["sh","-c","whoami"], allow_error=True).output.decode("utf-8").split("\n")[0]
    hostn = shell.run(["sh","-c","hostname"], allow_error=True).output.decode("utf-8").split("\n")[0]
    baseDir = shell.run(["sh","-c","pwd"], allow_error=True).output.decode("utf-8").split("\n")[0]
    cmdInput = input("Welcome to " + hostCmd + ":\n" + user + "@" + hostn + " ~>>")
    workDir = baseDir
    prevDir = workDir
    while (cmdInput != "exit"):
        if (cmdInput.startswith("cd ")):
            try:
                if (cmdInput.split()[1] == "~"):
                    result = shell.run(["echo", "hello"], cwd=baseDir)
                    prevDir = workDir
                    workDir = baseDir
                elif cmdInput.split()[1] == "-":
                    result = shell.run(["echo", "hello"], cwd=prevDir)
                    tempDir = prevDir
                    prevDir = workDir
                    workDir = tempDir
                elif cmdInput.split()[1].startswith(".."):
                    while cmdInput.split()[1].find("..") > -1:
                        if len(workDir.split("/")) == len(baseDir.split("/")):
                            result = shell.run(["echo", "hello"], cwd=baseDir)
                            prevDir = workDir
                            workDir = baseDir
                            break
                        elif cmdInput.split()[1][2] == "/":
                            result = shell.run(["echo", "hello"], cwd=workDir.rsplit("/",1)[0])
                            prevDir = workDir
                            workDir = workDir.rsplit("/",1)[0]
                            if cmdInput.split()[1].lstrip('../') == "":
                                break
                            cmdInput = cmdInput.split()[0] + " " + cmdInput.split()[1].lstrip('../')
                            
                    else:
                        result = shell.run(["echo", "hello"], cwd=workDir + "/" +cmdInput.split()[1])
                        prevDir = workDir
                        workDir = workDir + "/"  + cmdInput.split()[1]
                else:
                    result = shell.run(["echo", "hello"], cwd=workDir + "/" +cmdInput.split()[1])
                    prevDir = workDir
                    workDir = workDir + "/"  + cmdInput.split()[1]
            except:
                print("Not a directory")
        else:
            result = shell.spawn(["sh", "-c",cmdInput], allow_error=True, cwd=workDir, stdout=sys.stdout.buffer, store_pid=True)
            try:
                while result.is_running():
                    line = result._stdout.readline()
                    if line and line != '':
                        if type(line) == bytes:
                            print(line.decode().split('\n')[0])
                        else:
                            print(line.split('b')[0] + line.split('b')[1].decode().split('\n')[0])
            except:
                result._shell.run(["kill", "-{0}".format(signal.SIGINT), str(result.pid)])
            result = result.wait_for_result()
            if result.return_code <= 4:
                if result != 0:
                    #print(result.output.decode("utf-8"))
                    result = result
                if result.return_code != 0:
                    result = shell.run(["sh", "-x",cmdInput], allow_error=True)
                    print(result.to_error())
            else:
                print(result.to_error())
        cmdInput = input(user + "@" + hostn + " ~" + workDir.partition(baseDir)[2] + ">>")
except Exception as inst:
    print("Connection Failed.")
    print(inst)
finally:
    shell.close()

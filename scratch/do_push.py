import subprocess
import os

git_exe = r"C:\git\cmd\git.exe"

print("Switching to main branch...")
subprocess.run([git_exe, "checkout", "main"], check=True)

print("Pushing main branch to origin on GitHub...")
env = os.environ.copy()
env["GIT_TERMINAL_PROMPT"] = "0"

res = subprocess.run([git_exe, "push", "origin", "main"], capture_output=True, text=True, env=env)
print("STDOUT:", res.stdout)
print("STDERR:", res.stderr)

print("Switching back to develop branch...")
subprocess.run([git_exe, "checkout", "develop"], check=True)

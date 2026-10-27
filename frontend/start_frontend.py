"""
前端启动脚本 (改进版)
捕获 Vite 启动错误并显示
"""
import os, sys, subprocess, time

base_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(base_dir)

err_log = os.path.join(base_dir, "start_error.log")

with open(err_log, "w") as f:
    f.write("Starting Vite...\n")

vite_script = os.path.join(base_dir, "node_modules", "vite", "bin", "vite.js")

proc = subprocess.Popen(
    ["node", vite_script, "--port", "5173"],
    cwd=base_dir,
    stdout=subprocess.DEVNULL,
    stderr=open(err_log, "a"),
)

time.sleep(4)

if proc.poll() is not None:
    with open(err_log, "r") as f:
        err = f.read()
    print()
    print("=" * 50)
    print(f"[错误] 前端启动失败，退出码: {proc.returncode}")
    print()
    print("错误详情:")
    print(err[-1000:])
    print("=" * 50)
    input("\n按回车键关闭...")
    sys.exit(1)
else:
    print(f"[成功] 前端已启动 (PID: {proc.pid})")
    print(f"       http://localhost:5173")
    proc.wait()

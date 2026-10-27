"""
后端启动脚本 (改进版)
捕获 uvicorn 错误输出并显示
"""
import os, sys, subprocess, time

base_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(base_dir)
sys.path.insert(0, base_dir)

err_log = os.path.join(base_dir, "start_error.log")

# Clear old log
with open(err_log, "w") as f:
    f.write("Starting uvicorn...\n")

# Start uvicorn with stderr captured
proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
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
    print(f"[错误] 后端启动失败，退出码: {proc.returncode}")
    print()
    print("错误详情:")
    print(err[-1500:])
    print("=" * 50)
    print()
    print("请检查 backend/start_error.log 查看完整错误")
    input("\n按回车键关闭...")
    sys.exit(1)
else:
    print(f"[成功] 后端已启动 (PID: {proc.pid})")
    print(f"       http://127.0.0.1:8000")
    # Verify health
    try:
        import urllib.request
        r = urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=5)
        print(f"       健康检查: {r.read().decode()}")
    except Exception as e:
        print(f"       健康检查超时: {e}")
    proc.wait()

@echo off
echo ====================================
echo 社保系统部署修复工具
echo ====================================
echo.
echo 请按照以下步骤操作：
echo.
echo 步骤1：使用 SSH 工具登录服务器
echo   - 主机: 10.0.0.60
echo   - 用户: root
echo   - 密码: gQJwgfG9obG57p
echo.
echo 步骤2：在服务器上执行以下命令
echo ====================================
echo.
echo # 停止旧服务
echo pkill -f uvicorn
echo.
echo # 启动新服务
echo cd /opt/execl_mix/backend
echo nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 ^> backend.log 2^>^&1 ^&
echo.
echo # 等待3秒
echo sleep 3
echo.
echo # 验证服务
echo curl http://localhost:8000/health
echo.
echo ====================================
echo.
echo 步骤3：上传前端文件
echo   使用 WinSCP 或 FileZilla:
echo   - 本地: D:\execl_mix\frontend\dist
echo   - 服务器: /opt/execl_mix/frontend/dist
echo.
echo 完成后访问: http://139.199.192.190/login
echo.
pause

@echo off
REM RAG系统快速安装脚本 - Windows批处理文件

echo ============================================================
echo RAG医学文献检索系统 - 安装脚本
echo ============================================================
echo.

REM 检查Python是否安装
echo [1/4] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.9或更高版本
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)
python --version
echo.

REM 创建虚拟环境（可选）
echo [2/4] 是否创建虚拟环境？（推荐）
set /p CREATE_VENV="创建虚拟环境？(Y/N): "
if /i "%CREATE_VENV%"=="Y" (
    echo 正在创建虚拟环境...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo 虚拟环境已创建并激活
) else (
    echo 跳过虚拟环境创建
)
echo.

REM 安装依赖
echo [3/4] 安装Python依赖包...
pip install -r requirements.txt
if errorlevel 1 (
    echo 错误: 依赖安装失败
    pause
    exit /b 1
)
echo 依赖安装成功
echo.

REM 配置环境变量
echo [4/4] 配置环境变量...
if not exist .env (
    echo 复制.env.example到.env...
    copy .env.example .env
    echo.
    echo ================================================
    echo 重要: 请编辑 .env 文件并设置你的 OPENAI_API_KEY
    echo ================================================
    echo.
    echo 打开.env文件并将 your_api_key_here 替换为你的实际API密钥
    echo 示例: OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx
    echo.
    set /p OPEN_ENV="是否现在打开.env文件编辑？(Y/N): "
    if /i "%OPEN_ENV%"=="Y" (
        notepad .env
    )
) else (
    echo .env文件已存在，跳过创建
)
echo.

REM 运行测试
echo ============================================================
echo 安装完成！
echo ============================================================
echo.
echo 下一步:
echo   1. 确保.env文件中已配置正确的OPENAI_API_KEY
echo   2. 运行测试: python test_setup.py
echo   3. 快速开始: python quick_start.py
echo   4. 查看文档: README.md
echo.
set /p RUN_TEST="是否现在运行测试脚本？(Y/N): "
if /i "%RUN_TEST%"=="Y" (
    python test_setup.py
)
echo.
pause

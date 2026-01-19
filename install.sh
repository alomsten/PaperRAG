#!/bin/bash
# RAG系统快速安装脚本 - Linux/Mac Shell脚本

echo "============================================================"
echo "RAG医学文献检索系统 - 安装脚本"
echo "============================================================"
echo ""

# 检查Python是否安装
echo "[1/4] 检查Python环境..."
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3，请先安装Python 3.9或更高版本"
    exit 1
fi
python3 --version
echo ""

# 创建虚拟环境（可选）
echo "[2/4] 是否创建虚拟环境？（推荐）"
read -p "创建虚拟环境？(Y/N): " CREATE_VENV
if [[ "$CREATE_VENV" =~ ^[Yy]$ ]]; then
    echo "正在创建虚拟环境..."
    python3 -m venv venv
    source venv/bin/activate
    echo "虚拟环境已创建并激活"
else
    echo "跳过虚拟环境创建"
fi
echo ""

# 安装依赖
echo "[3/4] 安装Python依赖包..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "错误: 依赖安装失败"
    exit 1
fi
echo "依赖安装成功"
echo ""

# 配置环境变量
echo "[4/4] 配置环境变量..."
if [ ! -f .env ]; then
    echo "复制.env.example到.env..."
    cp .env.example .env
    echo ""
    echo "================================================"
    echo "重要: 请编辑 .env 文件并设置你的 OPENAI_API_KEY"
    echo "================================================"
    echo ""
    echo "使用文本编辑器打开.env文件并将 your_api_key_here 替换为你的实际API密钥"
    echo "示例: OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx"
    echo ""
    read -p "是否现在打开.env文件编辑？(Y/N): " OPEN_ENV
    if [[ "$OPEN_ENV" =~ ^[Yy]$ ]]; then
        ${EDITOR:-nano} .env
    fi
else
    echo ".env文件已存在，跳过创建"
fi
echo ""

# 运行测试
echo "============================================================"
echo "安装完成！"
echo "============================================================"
echo ""
echo "下一步:"
echo "  1. 确保.env文件中已配置正确的OPENAI_API_KEY"
echo "  2. 运行测试: python test_setup.py"
echo "  3. 快速开始: python quick_start.py"
echo "  4. 查看文档: README.md"
echo ""
read -p "是否现在运行测试脚本？(Y/N): " RUN_TEST
if [[ "$RUN_TEST" =~ ^[Yy]$ ]]; then
    python test_setup.py
fi
echo ""

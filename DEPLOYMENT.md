# Streamlit Cloud 部署说明

## 1. 本地启动方法

```bash
cd ashare_backtester
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -c "from ashare_backtester.ui import main; print('import ok')"
pytest
streamlit run app.py
```

本地页面打开后，输入股票代码、日期、资金和策略，点击“开始回测”。

## 2. 用 GitHub Desktop 上传

1. 打开 GitHub Desktop。
2. 选择 `File -> Add Local Repository...`。
3. 选择本项目文件夹：`ashare_backtester`。
4. 如果提示创建仓库，选择创建本地仓库。
5. 检查变更文件，不要勾选 `.venv/`、缓存、结果文件或密钥文件。
6. 填写提交说明，例如 `Initial ashare backtester MVP`。
7. 点击 `Commit to main`。
8. 点击 `Publish repository` 上传到 GitHub。

`.gitignore` 已排除虚拟环境、缓存、结果目录和 `.streamlit/secrets.toml`。

## 3. Streamlit Cloud 部署方法

1. 打开 [Streamlit Cloud](https://streamlit.io/cloud)。
2. 使用 GitHub 账号登录。
3. 点击 `New app`。
4. 选择刚上传的仓库。
5. Branch 选择 `main`。
6. Main file path 填写：

```text
app.py
```

7. Python version 选择 `3.12`。
8. 点击部署。

## 4. Secrets 如何填写

第一版只使用 AKShare 免费公开数据，通常不需要 Secrets。

如果以后接入 Tushare，可以在 Streamlit Cloud 的 `Advanced settings -> Secrets` 中填写：

```toml
TUSHARE_TOKEN = "你的token"
```

不要把 Token 写进代码、README 或 GitHub。

## 5. 分享到微信好友

部署成功后，Streamlit Cloud 会生成一个公开网址。复制该网址，在微信里发送给好友即可。手机和微信浏览器可以直接打开并操作页面。

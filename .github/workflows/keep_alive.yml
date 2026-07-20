name: Multi-User Streamlit Browser Keeper

on:
  schedule:
    - cron: '0 */5 * * *'  # 每12小时执行一次
  workflow_dispatch:        # 支持手动测试

jobs:
  browser-wake:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Install Dependencies
        run: |
          pip install playwright
          python -m playwright install chromium

      - name: Run Playwright Wakeup
        env:
          # 在 GitHub Secrets 中设置此 JSON
          USER_COOKIES_JSON: ${{ secrets.USER_COOKIES_JSON }}
        run: python multi_wake.py

      - name: Upload Screenshots
        if: always()  # 无论成功失败都上传截图
        uses: actions/upload-artifact@v4
        with:
          name: app-previews
          path: "*.png"
          retention-days: 1

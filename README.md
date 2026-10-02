# 6M 動能月誌

一場十年實驗的公開實驗室筆記。<https://6m.jeromewang.cloud>

- `build.py`：靜態站產製器。數字唯一來源 `data/6m_monthly.csv`（公開裁切版），
  每期敘事在 `content/YYYY-MM.json`，體檢表自原稿同步。
- `python3 build.py` → 輸出 `site/`，rsync 到主機即部署。
- 本 repo 不含任何策略程式碼。

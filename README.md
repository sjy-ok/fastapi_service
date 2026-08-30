# FastAPI Service

基于 FastAPI、SQLAlchemy 2.x Async 和 PostgreSQL 的模块化 MVP 后端，包含人员、人员变动记录以及 TM/PL/Department 管理。

要求 Python 3.11 或更高版本。

```powershell
python -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
python -m scripts.init_db
fastapi dev app/main.py
```

服务启动后可访问人员管理页面 `/`、健康检查 `/health` 和 API 文档 `/docs`。

人员、人员变动、TM、PL、Department 均提供独立 CRUD。人员变动是默认管理页面，所有关联字段必须通过远程搜索选择已有基础数据。Personnel 只有 W3 Account 必填，姓名和工号允许为空。列表接口支持模糊搜索以及简单的 `limit/offset`。被人员变动或 Leader 引用的基础数据不能删除。

TM、PL、Department 名称唯一并自动去除首尾空白。人员变动的开始与结束字段使用 `YYYY-MM-DD` 日期；新增表单默认显示 `1900-01-01`，但后端允许空开始日期且不会自动补值。

检查：

```powershell
ruff check .
pytest
```

新增模块依次实现 Model、Schema、Repository、Service、Dependencies、Router，在 `app/db/models.py` 注册模型、在 `app/api/router.py` 注册路由，最后补测试。

Service 管理 commit、rollback 和必要的 flush。Repository 不控制事务，`add` 也不隐式 flush；数据库约束错误由 Service 转换为业务异常。

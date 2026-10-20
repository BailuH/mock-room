# 数字法庭项目重构与部署解耦规划

> 版本：v1.0　日期：2026-10-19　状态：待评审

## 1. 背景与现状分析

### 1.1 项目现状

本仓为单仓（monorepo），包含三个子项目与一套 all-in-one 部署配置：

| 目录 | 角色 | 技术栈 |
|------|------|--------|
| `court_vue3/` | 主前端（门户/登录/案件管理/OCR） | Vue 3.2 + vue-cli(webpack) + Element Plus + Pinia |
| `mock-court/` | 庭审模拟页（唯一承载 LangGraph 庭审交互的 UI） | React 19 + Vite 7 + TS + Tailwind |
| `debate_mfxb2/` | 后端 | FastAPI + LangGraph + SQLAlchemy 2.0(asyncpg) + MinIO，uv 管理 |
| `docker/` + 根 `Dockerfile` | all-in-one 部署 | python:3.13-slim 内嵌 nginx + PostgreSQL 16 + MinIO + supervisord |

### 1.2 核心问题

**前端层面**
- 双前端并存，Vue 门户通过 `window.location.href` 整页硬跳转到 `/mock-court/`（`court_vue3/src/components/home/HomeComponent.vue:148`、`court_vue3/src/components/menu/MenuHome.vue:240`），不携带案件参数、不共享登录态。
- mock-court 虽然 WS 协议层完整，但入口案件是硬编码的演示案件（`mock-court/src/data/index.ts`），与用户实际创建的案件无关联。
- court_vue3 同时依赖 Pinia 和 Vuex（Vuex 为死依赖）；6 个路由指向"正在开发"占位组件。
- mock-court 仓内有孤儿残留：`csstheme/`、`login_dashboard/`、`src/app.txt`、lint_report、重复 `court.jpg`。

**部署层面**
- 单个 all-in-one 镜像：前端构建 + nginx + PostgreSQL + MinIO + FastAPI 全塞在一个 python 镜像里（`Dockerfile:46-102`），由 supervisord 管理。前后端无法独立构建、独立发布、独立伸缩，任何前端改动都要重装 PG/MinIO。
- DB 密码硬编码在 `docker/entrypoint.sh`，MinIO 密钥硬编码在 `Dockerfile:92-93`，`.env` 被打入镜像（`Dockerfile:78`）。
- 根 `docker-compose.yml`（仅 PG+MinIO）与 all-in-one 的端口约定不一致（MinIO 9000 vs 9002），`START.md` 还残留个人绝对路径。

**顺带发现的技术债**（不在本次主目标内，但建议列入 backlog）
- 后端 `/ws/trial` 无鉴权；`/api/login` 密码明文比对；`agents/denfendant.py` 拼写错误；`llmconfig.py` 三个模型名全部指向同一个实际模型；`langgraph.json` 指向已不存在的 `src/test.py`；`debate_mfxb2/CLAUDE.md` 多处与现状漂移。

### 1.3 关键事实（重构的有利条件）

- WebSocket 协议是前后端唯一强耦合点，且**定义清晰、双向可对照**：`mock-court/src/CourtClient.ts` ↔ `debate_mfxb2/src/api/websocket_schemas.py` + `graph_manager.py`。重写为 Vue 组件时协议层可直接平移。
- 演示案件数据（17 份证据 md + 照片 + `defaultCase.ts`）是独立于 React 的干净资产，可原样迁移。
- mock-court 的 Material Design 3 主题 token 体系（`src/index.css` + `ThemeContext`，9 套主题）值得保留。

## 2. 总体目标

1. **前端统一**：删除 React（mock-court），在 court_vue3 中以 Vue 组件实现庭审模拟页，与后端 WebSocket 交互，并与门户（案件管理、登录态）打通。
2. **部署解耦**：废弃 all-in-one 镜像，拆分为「前端镜像」「后端镜像」+ docker-compose（PostgreSQL、MinIO 作为独立基础设施服务），支持前后端独立构建与发布。
3. **顺带治理**：清理孤儿文件、修正文档漂移、收敛配置通路，为后续迭代降低认知负担。

## 3. 阶段规划

### Phase 0：仓库治理与安全基线（1~2 天，可与其他阶段并行）

目标：把"历史包袱"清掉，避免后续开发在垃圾文件上继续叠加。

- [ ] **删除 mock-court 孤儿文件**：`csstheme/`、`login_dashboard/`、`src/app.txt`、`lint_report*.json`、根目录重复的 `court.jpg`。
- [ ] **删除 court_vue3 死依赖**：卸载 Vuex 及配套（保留 Pinia）。
- [ ] **修正文档**：更新 `START.md`（去掉个人绝对路径、同步新部署方式）、重写 `debate_mfxb2/CLAUDE.md`、补写两个子项目 README；删除或修正指向已不存在文件的 `langgraph.json`。
- [ ] **安全基线（最小改动）**：
  - `.env` 移出镜像构建（改为运行时用 `--env-file` 或环境变量注入，见 Phase 2）；
  - `docker/entrypoint.sh` 中 DB 密码、`Dockerfile` 中 MinIO 密钥改为 build-arg / 环境变量注入；
  - 后端 `/ws/trial` 增加简单 token 校验（与登录接口返回的 token 对应，见 Phase 1.4）。

验收：两个前端与后端在本地开发模式均能正常启动，无用文件全部移除，无文档引用已删除内容。

### Phase 1：删除 React，庭审页用 Vue 重写（2~4 周，核心阶段）

#### 1.1 前期准备：协议与资产冻结

- 将 WebSocket 协议整理为一份**协议文档**（消息类型、字段、时序：`start_trial` → `session_created` → `node_executed` / `interrupt_request` → `user_input` → `trial_completed`），来源为 `websocket_schemas.py` / `graph_manager.py` / `CourtClient.ts` 三方对照。这份文档是重写期间的唯一事实来源。
- 把可迁移资产从 mock-court 中摘出到临时目录（或直接翻译）：
  - 演示案件数据（`src/data/`）→ 转为 TS/JSON 模块放入 court_vue3；
  - MD3 主题 token → 转为 CSS 变量，与 Element Plus 主题机制整合（Element Plus 支持 CSS 变量级主题定制）；
  - `CourtClient.ts` 的协议处理逻辑 → 翻译为 TypeScript/Vue 可用的 `useCourtWebSocket` composable。

#### 1.2 Vue 庭审页实现

在 court_vue3 内新建庭审模块（建议结构）：

```
court_vue3/src/
├── modules/court/              # 庭审模拟模块（新）
│   ├── api/courtClient.ts      # WS 客户端（CourtClient 的 Vue 版，含心跳/重连）
│   ├── composables/
│   │   ├── useCourtSession.ts  # 会话生命周期（对应 useCourtSession.ts）
│   │   └── useTrialState.ts    # 庭审状态机（对应 useTrialState.ts）
│   ├── components/             # 对应 React 的 12 个通用组件
│   │   ├── CourtLayout.vue     # 三栏布局（对应 App.tsx）
│   │   ├── ChatArea.vue        # 消息流 + markdown 渲染
│   │   ├── InterruptInputs.vue # 布尔/文本/证据选择三种 HITL 输入
│   │   ├── EvidencePanel.vue   # 证据列表 + 预览浮窗
│   │   ├── RoleSelector.vue    # 角色选择 + 开始庭审
│   │   └── ProgressBar.vue     # 庭审阶段进度
│   └── views/CourtView.vue     # 挂载点，替换现有空壳 CourtComponent.vue
```

要点：
- UI 组件库沿用 **Element Plus**（与门户一致），布局与交互 1:1 对标 mock-court 三栏式。
- markdown 渲染：React 端用 react-markdown，Vue 端选用 `markdown-it` + DOMPurify 等价方案。
- WS 连接地址统一走 `config.js` 的 baseURL 推导（`ws(s)://host/ws/trial`），删掉 React 端 `import.meta.env.DEV` 的分支判断，由 vue-cli 的 `devServer.proxy` 承担开发期代理。
- 保留 30s 心跳、消息类型守卫校验、重连逻辑。

#### 1.3 与门户打通（替换硬编码跳转）

- 路由 `/court` 改为指向新的 `CourtView.vue`，删除 `HomeComponent.vue:148` 和 `MenuHome.vue:240` 的 `window.location.href` 整页跳转。
- **传递案件上下文**：从案件管理页进入庭审时携带 `caseId` 路由参数；`CourtView` 通过 HTTP API 拉取案件信息与证据列表，组装 `start_trial` 的 `initial_state`，替换硬编码的 `activeCase`。
- 登录态共享：court_vue3 已有的 Pinia `loginStore` 天然生效，无需额外处理（这是删除整页跳转后的直接收益）。
- 被替换掉的半成品占位路由（`PlaintiffComponent` / `DefendantComponent` / `JudgeComponent` 等）按最终信息架构决定是删除还是由庭审页内部状态取代。

#### 1.4 收尾

- [ ] 后端 `/ws/trial` 接入与 `/api/login` 相同的简单 token 校验（Phase 0 已预留）。
- [ ] 删除整个 `mock-court/` 目录；同步更新 nginx 配置中的 `/mock-court/` 路由（见 Phase 2）。
- [ ] 用「演示案件 + 真实案件」各跑一遍完整庭审流程（开庭→调查→辩论→宣判 + HITL 中断/恢复 + 重试），与 React 版行为对照验收。

验收标准：Vue 庭审页功能与 React 版对齐（对照 mock-court 的 README 与 `frontend_analysis_report.md` 中的功能清单逐项打勾）；从案件管理页进入庭审时数据为真实案件；React 目录从仓中移除。

### Phase 2：Docker 部署解耦（3~5 天，可与 Phase 1 后半段并行）

#### 2.1 目标架构

```
┌────────────────────── docker-compose.yml (部署) ──────────────────────┐
│  frontend    nginx:alpine      静态资源(court_vue3 dist)   :80        │
│  backend     python:3.13-slim  FastAPI (uvicorn)           :8000      │
│  postgres    postgres:16-alpine                            :5432      │
│  minio       minio/minio                                   :9000/9001 │
└──────────────────────────────────────────────────────────────────────┘
```

- **frontend 镜像**：多阶段——node:20 构建 court_vue3 → nginx:alpine 托管 dist + 反代 `/api`、`/ws` 到 backend。单前端后，构建产物只有一份。
- **backend 镜像**：python:3.13-slim + uv 安装依赖 + `src/`，仅运行 uvicorn。**不再包含** PostgreSQL、MinIO、nginx、supervisord。
- **postgres / minio**：直接使用官方镜像，数据卷持久化，替代当前内嵌安装。
- 密钥/配置全部经 `.env`（git 忽略）+ compose `env_file` 注入，禁止打进任何镜像。

#### 2.2 具体改动

- [ ] 新增 `docker/frontend.Dockerfile`（构建 + nginx 托管）、`docker/backend.Dockerfile`。
- [ ] 重写根 `docker-compose.yml`：新增 `frontend`、`backend` 两个 service（本地构建），保留现有 `postgres`、`minio`，统一网络与卷；端口映射对齐开发约定（消除 9000/9002 不一致——以 compose 中统一为宿主机 `9000` 并同步 `debate_mfxb2/src/api/config.py` 默认值为准，或统一走容器内 `minio:9000`，二选一后全局一致）。
- [ ] `docker/nginx.conf` 改造为 frontend 镜像内的独立 nginx 配置（去掉 `alias /app/mock-court/`，`/api`、`/ws` 反代目标从 `127.0.0.1:8000` 改为 compose 服务名 `backend:8000`）。
- [ ] 废弃：`docker/supervisord.conf`、`docker/entrypoint.sh`、`docker/start-backend.sh`、根 `Dockerfile`（all-in-one）。可保留 all-in-one 的 Dockerfile 一个版本周期作回滚备份，标记 deprecated。
- [ ] `debate_mfxb2/.env` 的 `DATABASE_URL`、`MINIO_ENDPOINT` 默认值改为容器网络拓扑（`postgres:5432`、`minio:9000`），本地开发通过 `.env` 覆盖回 `localhost`。
- [ ] CI/发布流程：定义 `docker compose build frontend backend && docker compose push` 的发布命令；文档化「只发前端」与「只发后端」两条独立发布路径。

验收标准：`docker compose up -d` 一条命令起全套服务；前端、后端镜像可独立构建、独立推送、独立更新；`frontend` 更新不触碰数据库与存储；compose down/up 后数据保留（卷验证）。

### Phase 3：后续迭代方向（本规划范围之外，仅列建议）

按 `数字法庭开发设想.md` 对齐差距，优先级建议：
1. 后端工程化：Alembic 迁移（依赖已装但未用）、统一响应格式、分页、登录 token 体系、密码哈希。
2. 庭审体验：`/ws/trial` 鉴权强化、庭审历史持久化（目前 `SessionManager` 是纯内存 dict，重启即丢）、打分与逻辑链可视化。
3. 前端：Pinia store 拆分规范化、移除 vue-cli 迁移至 Vite（与 mock-court 原工具链一致，提升构建速度）、清理 `MenuHome.vue` 中硬编码的第三方天气 API key。

## 4. 里程碑与风险

| 里程碑 | 内容 | 预估 |
|--------|------|------|
| M1 | Phase 0 完成，仓库治理达标 | 第 1 周末 |
| M2 | 协议文档定稿 + Vue 庭审页可用（演示案件跑通） | 第 2 周末 |
| M3 | Vue 庭审页与真实案件打通，React 删除 | 第 4 周末 |
| M4 | 前后端镜像解耦，compose 一键部署 | 第 5 周中 |

**主要风险与对策**

- **Vue 重写工作量大导致延期**：先把三栏骨架 + 消息流 + HITL 输入三个核心链路跑通（M2 即可替换 Demo），证据管理、主题切换、多浮窗等增强功能可分批跟进，不必一次性对齐 5.7k 行。
- **协议在重写期间被后端改动**：Phase 1.1 先冻结协议文档并加后端消息模型的单测，重写期间后端非必要不动 WS 相关代码。
- **存量部署迁移**：服务器上已运行的 all-in-one 容器在 M4 完成前保持不动；新 compose 在过渡期与旧容器可并行验证（注意端口冲突，frontend 对外端口避开旧容器占用的 80）。
- **`.env` 从镜像中移除后部署配置缺失**：M4 交付时随 compose 提供 `.env.example` 与部署 README，明确必填项。

## 5. 目录结构展望（M4 完成后）

```
mock-room/
├── court_vue3/                 # 唯一前端（含庭审模块）
├── debate_mfxb2/               # 后端
├── docker/
│   ├── frontend.Dockerfile     # nginx 静态托管 + 反代
│   ├── backend.Dockerfile      # FastAPI
│   └── nginx.conf              # frontend 镜像专用
├── docker-compose.yml          # 部署编排（frontend/backend/postgres/minio）
├── PLAN.md                     # 本文档
├── START.md                    # 开发与部署指南（重写）
├── 数字法庭开发设想.md
└── （mock-court/、根 Dockerfile、supervisord 相关已删除）
```

# VitaBench 评测快速上手（面向外部用户）

这份文档用于把仓库整理成“开箱即可评测”的使用方式：你只需要配置自己的模型、服务商和 API Key，即可跑 VitaBench。

## 0. Conda 环境（推荐）

```bash
conda create -n vitabench python=3.10 -y
conda activate vitabench
pip install -U pip
pip install -e .
```

> 后续每次使用前先执行：`conda activate vitabench`

## 1. VitaBench 是什么

- VitaBench 总计 **400** 条任务。
- 由 4 个 split 组成，每个 **100** 条：
  - `delivery,instore,ota`（cross 场景）
  - `delivery`
  - `instore`
  - `ota`
- 标准完整评测就是把这 4 个 split 都跑完，再做汇总。

## 2. 模型与服务配置

1. 复制模板：

```bash
cp models.template.yaml models.local.yaml
```

2. 按你的服务商改 `models.local.yaml`。

### 2.1 重要说明：`zai-org/glm-5.1` 与供应商

- `zai-org/glm-5.1` 是当前仓库里对 **GLM-5.1 模型名的约定写法**（历史上常配 Novita）。
- 它只是一个“模型标识符”；真正请求哪个供应商，取决于该模型条目的 `base_url` 和 `headers.Authorization`。
- 因此：
  - 如果你用 Novita，就把 `zai-org/glm-5.1` 指到 Novita 的接口；
  - 如果你不用 Novita，也可以把同一个模型名指到其他供应商的 GLM-5.1 接口（只要 OpenAI 兼容）。

### 2.2 Novita 配置示例（user + evaluator）

```yaml
default:
  base_url: "https://api.novita.ai/v3/openai/chat/completions"
  temperature: 0.0
  max_input_tokens: 131072
  headers:
    Accept: "*/*"
    Content-Type: "application/json"
    Authorization: "Bearer ${NOVITA_API_KEY:}"

models:
  - name: "zai-org/glm-5.1"
    max_tokens: 32768
    max_input_tokens: 131072

  - name: "your-agent-model"
    max_tokens: 32768
    max_input_tokens: 131072
```

### 2.3 非 Novita 的 GLM-5.1 配置示例

把 `zai-org/glm-5.1` 这个条目改成你使用的供应商地址即可：

```yaml
models:
  - name: "zai-org/glm-5.1"
    base_url: "https://your-provider.example.com/v1/chat/completions"
    headers:
      Authorization: "Bearer ${GLM51_API_KEY:}"
```

### 2.4 user/evaluator 与 agent 来自不同供应商（推荐）

你可以在同一个 `models.local.yaml` 中给不同模型写不同 `base_url`：

```yaml
default:
  base_url: "https://api.novita.ai/v3/openai/chat/completions"
  headers:
    Authorization: "Bearer ${NOVITA_API_KEY:}"

models:
  # 固定用户模拟器与评估器：GLM-5.1（供应商 A）
  - name: "zai-org/glm-5.1"
    base_url: "https://api.novita.ai/v3/openai/chat/completions"
    headers:
      Authorization: "Bearer ${NOVITA_API_KEY:}"

  # 被评测 agent：来自供应商 B
  - name: "your-agent-model"
    base_url: "https://api.other-provider.com/v1/chat/completions"
    headers:
      Authorization: "Bearer ${AGENT_API_KEY:}"
```

3. 指定配置文件并设置 key：

```bash
export VITA_MODEL_CONFIG_PATH="$(pwd)/models.local.yaml"
export NOVITA_API_KEY="<YOUR_NOVITA_KEY>"
export AGENT_API_KEY="<YOUR_AGENT_PROVIDER_KEY>"   # 如有第二供应商
export GLM51_API_KEY="<YOUR_GLM51_PROVIDER_KEY>"   # 若 glm5.1 不走 Novita
```

## 3. 两种运行方式

### A) 串行跑四个命令（标准流程）

```bash
vita run --domain "delivery,instore,ota" --agent-llm "your-agent-model" --user-llm "zai-org/glm-5.1" --evaluator-llm "zai-org/glm-5.1" --max-concurrency 4 --save-to "benchmark_manual/cross.json"
vita run --domain "delivery"              --agent-llm "your-agent-model" --user-llm "zai-org/glm-5.1" --evaluator-llm "zai-org/glm-5.1" --max-concurrency 4 --save-to "benchmark_manual/delivery.json"
vita run --domain "instore"               --agent-llm "your-agent-model" --user-llm "zai-org/glm-5.1" --evaluator-llm "zai-org/glm-5.1" --max-concurrency 4 --save-to "benchmark_manual/instore.json"
vita run --domain "ota"                   --agent-llm "your-agent-model" --user-llm "zai-org/glm-5.1" --evaluator-llm "zai-org/glm-5.1" --max-concurrency 4 --save-to "benchmark_manual/ota.json"
```

### B) 一条命令跑完整 400 样例（推荐）

```bash
bash run_benchmark_400.sh "your-agent-model" 4 chinese
```

该脚本会自动：
- 串行执行 cross + 三个单场景，共 400 样例
- 固定 `user-llm` 与 `evaluator-llm` 为 `zai-org/glm-5.1`
- 不做自动合并；四份结果保存在同一个目录
- 在终端打印直观分数汇总（各 split 的 `avg_reward / pass^1 / 样本数`）

### C) 只给 base_url + model_id，并支持并行实验

如果你要同时跑多个 OpenAI-compatible endpoint，不要手动反复改同一个
`models.local.yaml`。可以用 `run_openai_compatible_4split.sh`，它会为每个
`RUN_NAME` 生成独立配置：

```bash
# 本地无鉴权服务
MAX_CONCURRENCY=8 \
bash run_openai_compatible_4split.sh \
  "http://127.0.0.1:8000/v1" \
  "glm-5.1-fp8" \
  "" \
  "exp_glm51_fp8_c8"

# 外部服务
MAX_CONCURRENCY=8 \
bash run_openai_compatible_4split.sh \
  "https://api.example.com/v1" \
  "provider/model-id" \
  "$AGENT_API_KEY" \
  "exp_provider_model_c8"
```

生成的配置在：

```bash
data/model_configs/benchmark_runs/<run_name>.yaml
```

结果和日志仍然在：

```bash
data/simulations/benchmark_runs/<run_name>/
data/logs/benchmark_runs/<run_name>/
```

并行跑多个实验时，给每个实验不同的 `run_name` 即可：

```bash
MAX_CONCURRENCY=8 bash run_openai_compatible_4split.sh http://host-a:8000/v1 model-a "" exp_a &
MAX_CONCURRENCY=8 bash run_openai_compatible_4split.sh http://host-b:8000/v1 model-b "" exp_b &
wait
```

启动前也可以先只生成配置、不跑评测：

```bash
DRY_RUN=1 bash run_openai_compatible_4split.sh http://host-a:8000/v1 model-a "" exp_a
```

## 4. 输出位置

- 单次运行目录（带时间戳）：
  - 结果文件：`data/simulations/benchmark_runs/<timestamp>/`
  - 日志文件：`data/logs/benchmark_runs/<timestamp>/`
- 结果文件共 4 个：
  - `delivery,instore,ota.json`
  - `delivery.json`
  - `instore.json`
  - `ota.json`

## 5. 可视化查看（支持目录）

推荐使用 Web 看板查看进行中或已完成的 benchmark run：

```bash
PYTHONPATH=src python3 -m vita.cli board --host 0.0.0.0 --port 8765
```

打开 `http://127.0.0.1:8765/dashboard`，可查看每个实验的 split 进度、分数摘要，并点击 split 展开日志 tail。

默认数据源：

- logs：`data/logs`，看板会读取其中的 `benchmark_runs/<run_name>/`
- results：`data/simulations`，看板会读取其中的 `benchmark_runs/<run_name>/`

如需指定数据源：

```bash
PYTHONPATH=src python3 -m vita.cli board \
  --host 0.0.0.0 \
  --port 8765 \
  --logs-dir /path/to/logs \
  --simulations-dir /path/to/simulations
```

`--logs-dir` 和 `--simulations-dir` 可以传根目录，也可以传已经包含 `benchmark_runs` 的目录。

现在可以直接把目录传给 `vita view`：

```bash
vita view --file "data/simulations/benchmark_runs/<timestamp>"
```

它会自动读取目录中的 `*.json` 结果文件，便于批量查看。

## 6. 环境安装（首次）

```bash
pip install -e .
```

安装完成后可以直接使用 `vita` 命令。

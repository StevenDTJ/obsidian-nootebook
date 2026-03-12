## 1. 项目概述

该项目是斯坦福大学发布的 **"Generative Agents: Interactive Simulacra of Human Behavior"** (UIST 2023) 论文的实现代码。该项目创建了一个名为 **Smallville** 的交互式虚拟小镇，其中包含 25 个由大语言模型（LLM）驱动的生成式智能体（Generative Agents），能够模拟真实的人类行为。

### 核心技术栈

- **后端**: Python 3.9, Django 2.2, OpenAI API (GPT-3.5/GPT-4)
- **前端**: Django + JavaScript 可视化
- **依赖库**: openai, numpy, pandas, scikit-learn, gensim (向量嵌入), nltk, matplotlib

---

## 2. 项目目录结构

```
generative_agents/
├── README.md                      # 项目说明文档
├── requirements.txt               # 依赖列表
├── cover.png                      # 项目封面图
│
├── environment/                   # 环境前端服务器
│   └── frontend_server/
│       ├── manage.py              # Django 管理脚本
│       ├── translator/            # Django 应用 (数据模型)
│       ├── frontend_server/       # Django 项目配置
│       └── static_dirs/assets/    # 静态资源 (地图、角色)
│           └── the_ville/         # Smallville 小镇地图数据
│
└── reverie/                       # 后端模拟服务器 (核心)
    ├── backend_server/
    │   ├── reverie.py             # 主模拟服务器入口
    │   ├── maze.py                # 地图/环境定义
    │   ├── path_finder.py         # 路径规划
    │   ├── global_methods.py      # 全局工具方法
    │   ├── persona/
    │   │   ├── persona.py         # Persona 智能体类定义
    │   │   ├── cognitive_modules/ # 认知模块 (感知-检索-计划-执行-反思)
    │   │   │   ├── perceive.py    # 感知模块
    │   │   │   ├── retrieve.py    # 记忆检索模块
    │   │   │   ├── plan.py        # 规划模块
    │   │   │   ├── execute.py     # 执行模块
    │   │   │   ├── reflect.py     # 反思/反思模块
    │   │   │   └── converse.py    # 对话模块
    │   │   ├── memory_structures/ # 记忆结构
    │   │   │   ├── associative_memory.py  # 联想记忆 (记忆流)
    │   │   │   ├── spatial_memory.py      # 空间记忆
    │   │   │   └── scratch.py              # 短期记忆/草稿本
    │   │   └── prompt_template/ # LLM 提示词模板
    │   │       ├── gpt_structure.py       # OpenAI API 封装
    │   │       ├── run_gpt_prompt.py      # 提示词执行函数
    │   │       └── v2/                      # 提示词模板文件
    │   └── utils.py               # 配置文件 (API Key 等)
    └── compress_sim_storage.py    # 模拟数据压缩工具
```

---

## 3. 智能体核心架构

### 3.1 Persona 类 (GenerativeAgent)

智能体的核心类定义在 [[persona/persona.py]]，包含以下关键组件：

```python
class Persona:
    def __init__(self, name, folder_mem_saved=False):
        # === 记忆系统 (Memory) ===
        self.s_mem = MemoryTree(...)      # 空间记忆 (世界/区域/对象层次结构)
        self.a_mem = AssociativeMemory(...)# 联想记忆 (记忆流 - Memory Stream)
        self.scratch = Scratch(...)        # 短期记忆 (草稿本)
```

### 3.2 认知循环 (Cognitive Loop)

智能体的主决策循环在 `persona.move()` 方法中实现：

```python
def move(self, maze, personas, curr_tile, curr_time):
    # 1. Perceive (感知) - 感知周围环境事件
    perceived = self.perceive(maze)

    # 2. Retrieve (检索) - 从记忆流中检索相关内容
    retrieved = self.retrieve(perceived)

    # 3. Plan (计划) - 生成长期/短期计划
    plan = self.plan(maze, personas, new_day, retrieved)

    # 4. Reflect (反思) - 反思并生成新见解
    self.reflect()

    # 5. Execute (执行) - 转换为具体行动
    return self.execute(maze, personas, plan)
```

---

## 4. 记忆系统架构

### 4.1 记忆类型

| 记忆类型               | 文件位置                                                | 描述                                             |
| ------------------ | --------------------------------------------------- | ---------------------------------------------- |
| **空间记忆 (s_mem)**   | [[persona/memory_structures/spatial_memory.py]]     | 层次化存储世界结构: World → Sector → Arena → GameObject |
| **联想记忆 (a_mem)**   | [[persona/memory_structures/associative_memory.py]] | 记忆流核心，使用事件三元组 (s, p, o) 存储                     |
| **短期记忆 (scratch)** | [[persona/memory_structures/scratch.py]]            | 当前行动、时间、状态等临时信息                                |

### 4.2 联想记忆 (Associative Memory)

记忆流的核心数据结构：

```python
class ConceptNode:
    node_id, node_type,  # 节点 ID 和类型 (event/thought/chat)
    created, expiration, # 创建时间和过期时间
    subject, predicate, object,  # 事件三元组 (s, p, o)
    description,         # 事件描述
    embedding_key,       # 向量嵌入的 key
    poignancy,          # 重要性/情感强度 (1-10)
    keywords,           # 关键词集合
    filling            # 引用其他记忆节点 (用于反思)
```

### 4.3 记忆检索算法

在 [[persona/cognitive_modules/retrieve.py]] 中实现的三因素检索模型：

```python
def new_retrieve(persona, focal_points, n_count=30):
    # 综合评分 = 3个因素的加权组合
    # 1. Recency (近期性): decay^index 衰减
    # 2. Relevance (相关性): 余弦相似度计算
    # 3. Importance (重要性): 事件情感强度 (poignancy)

    # 权重配置
    gw = [0.5, 3, 2]  # [recency, relevance, importance]
```

---

## 5. 语言模型集成层

### 5.1 API 封装

在 [[persona/prompt_template/gpt_structure.py]] 中定义：

```python
# OpenAI API Key 配置
openai.api_key = openai_api_key

# 主要调用函数
def ChatGPT_request(prompt):
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )

def GPT4_request(prompt):
    completion = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )

def get_embedding(text, model="text-embedding-ada-002"):
    # 生成文本嵌入向量用于记忆检索
    return openai.Embedding.create(input=[text], model=model)['data'][0]['embedding']
```

### 5.2 提示词模板

提示词模板存储在 [[persona/prompt_template/run_gpt_prompt.py]] 所在目录，包括：

- `wake_up_hour_v1.txt` - 生成起床时间
- `daily_planning_v6.txt` - 生成每日计划
- 任务分解、动作选择、对话生成等模板

### 5.3 安全调用机制

```python
def safe_generate_response(prompt, gpt_parameter, repeat=5, ...):
    # 失败重试机制 (最多5次)
    for i in range(repeat):
        try:
            response = GPT_request(prompt, gpt_parameter)
            if validate(response):
                return clean_up(response)
        except:
            pass
    return fail_safe_response  # 返回保底值
```

---

## 6. 环境与模拟

### 6.1 Maze 类

在 [[maze.py]] 中定义虚拟世界：

- 二维瓦片地图 (Tile-based)
- 每个瓦片包含: 世界/区域/ arena / game_object
- 事件系统: 在瓦片上记录智能体的行动

### 6.2 模拟服务器 (ReverieServer)

在 [[reverie.py]] 中：

```python
class ReverieServer:
    def __init__(self, fork_sim_code, sim_code):
        self.maze = Maze(maze_name)      # 地图实例
        self.personas = dict()            # 所有智能体
        self.personas_tile = dict()      # 智能体位置
        self.curr_time = datetime.now()  # 游戏时间
        self.step = 0                     # 模拟步数

    def start_server(self, int_counter):
        # 主循环: 每步执行一次所有智能体的认知循环
        while int_counter > 0:
            # 1. 从前端获取环境状态
            # 2. 执行所有智能体的 move() 方法
            # 3. 将行动发送给前端
            # 4. 时间推进 sec_per_step (默认 10 秒/步)
```

---

## 7. 典型行为执行轨迹

以智能体"早晨起床，去厨房找食物"为例：

```
1. Perceive (感知)
   └─ 扫描周围 vision_r 半径内的瓦片
   └─ 检索附近其他智能体的活动事件
   └─ 根据 retention 过滤已感知的事件

2. Retrieve (检索)
   └─ 对每个感知事件，从记忆流检索相关内容
   └─ 计算 [近期性 + 相关性 + 重要性] 加权得分
   └─ 返回 top-30 相关记忆节点

3. Plan (计划)
   └─ [长期] 每日计划生成 (新一天时)
   │   └─ 生成起床时间、每小时活动安排
   │   └─ 任务分解 (小时 → 分钟级任务)
   └─ [短期] 确定当前行动
       └─ 选择动作区域 (sector/arena)
       └─ 选择动作对象 (game_object)
       └─ 决定是否与附近智能体交谈/反应

4. Reflect (反思)
   └─ 定期检查是否需要反思
   └─ 从高重要性记忆生成新见解 (thought)
   └─ 更新 identity/stable set

5. Execute (执行)
   └─ 将计划转换为物理坐标
   └─ 生成动作描述和 emoji
   └─ 返回 (next_tile, pronunciation, description)
```

---

## 8. 架构设计模式

| 设计模式 | 应用场景 |
|---------|---------|
| **分层架构** | 认知模块 (perceive→retrieve→plan→execute) 顺序调用 |
| **记忆模式** | 三层记忆 (感知/工作/长期) 类似 cognitive architecture |
| **事件驱动** | 智能体对环境事件的反应机制 |
| **模板方法** | 提示词模板 + 参数化生成 |
| **工厂模式** | 通过 base simulation fork 新模拟 |

---

## 9. 关键配置

在 `reverie/backend_server/utils.py` 中：

```python
openai_api_key = "<Your OpenAI API>"    # OpenAI API 密钥
key_owner = "<Name>"                    # 用户名称

# 路径配置
maze_assets_loc = "../../environment/frontend_server/static_dirs/assets"
fs_storage = "../../environment/frontend_server/storage"      # 模拟数据存储

# 碰撞检测
collision_block_id = "32125"

debug = True
```

---

## 10. 依赖库版本

```
Django==2.2              # Web 框架
openai==0.27.0           # OpenAI API
numpy==1.25.2            # 数值计算
pandas==2.0.3           # 数据处理
gensim==3.8.0           # 词向量
scikit-learn==1.3.0     # 机器学习
nltk==3.6.5             # 自然语言处理
matplotlib==3.7.2       # 可视化
selenium==4.8.2         # 浏览器自动化
```

---

## 11. 执行流程

### 启动模拟

```bash
# 1. 启动环境服务器 (Django)
cd environment/frontend_server
python manage.py runserver

# 2. 启动模拟服务器
cd reverie/backend_server
python reverie.py

# 输入分叉模拟名称
Enter the name of the forked simulation: base_the_ville_isabella_maria_klaus

# 输入新模拟名称
Enter the name of the new simulation: test-simulation

# 运行模拟
Enter option: run 100
```

### 访问界面

- 模拟视图: http://localhost:8000/simulator_home
- 回放: http://localhost:8000/replay/<sim-name>/<step>/
- 演示: http://localhost:8000/demo/<sim-name>/<step>/<speed>/

---

## 12. 总结

该项目是一个经典的 **基于 LLM 的智能体系统** 实现，核心创新在于：

1. **记忆流架构** - 使用向量嵌入和重要性评分实现类人记忆检索
2. **认知循环** - 清晰的感知-检索-计划-执行-反思流程
3. **多层计划** - 长期(每日) + 短期(当前时刻) 的层次化规划
4. **社会交互** - 智能体间的对话生成和反应机制
5. **时间驱动** - 基于游戏时间的模拟推进机制

该架构为创建 believable human-like agents 提供了重要参考。

---

*文档生成时间: 2026-03-03*

*项目来源: Stanford HCI Group - Generative Agents (UIST 2023)*

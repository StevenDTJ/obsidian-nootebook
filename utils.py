# API 配置

# ============ DeepSeek API (用于聊天) ============
# 获取 API Key: https://platform.deepseek.com/
openai_api_key = "<Your DeepSeek API>"
key_owner = "<Name>"

# ============ Qwen API (用于 Embedding 向量化) ============
# 获取 API Key: https://dashscope.console.aliyun.com/
# 1. 登录阿里云百炼控制台
# 2. 进入 API-KEY 管理
# 3. 创建 API-KEY
# 4. 复制 API-KEY 到下方
qwen_api_key = "<Your Qwen API>"

# ============ 路径配置 ============
maze_assets_loc = "../../environment/frontend_server/static_dirs/assets"
env_matrix = f"{maze_assets_loc}/the_ville/matrix"
env_visuals = f"{maze_assets_loc}/the_ville/visuals"

fs_storage = "../../environment/frontend_server/storage"
fs_temp_storage = "../../environment/frontend_server/temp_storage"

collision_block_id = "32125"

debug = True

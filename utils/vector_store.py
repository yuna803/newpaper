"""
向量数据库模块 - 负责新闻内容的向量化存储和语义检索
================================================================
技术栈: FAISS (向量索引) + DashScope text-embedding-v4 (嵌入模型)
分片策略: 一篇新闻 = 一个文档（不切割）
持久化: chroma_db/faiss_index.pkl
================================================================

核心流程:
  审核通过 → index_news() → 自动加入向量库
  删除/驳回 → remove_news() → 从向量库移除
  用户提问 → search_news() → 返回最相关的 k 篇新闻
  首次启动 → index_all_news() → 全量索引所有已发布新闻
"""
import os
import pickle
import numpy as np
from openai import OpenAI

# ========== 配置 ==========

# 索引文件存储路径
CHROMA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chroma_db")
INDEX_FILE = os.path.join(CHROMA_PATH, "faiss_index.pkl")

# DashScope API Key（从环境变量读取，不硬编码）
API_KEY = os.environ.get("DASHSCOPE_API_KEY", "")

# DashScope 客户端（兼容 OpenAI SDK）
client = OpenAI(api_key=API_KEY, base_url="https://dashscope.aliyuncs.com/compatible-mode/v1")

# ========== 运行时状态 ==========
# _index: FAISS IndexFlatIP 实例，存储所有新闻的归一化向量
# _documents: 文档文本列表，与 _index 中的向量一一对应
# _metadatas: 元数据列表，存储每篇新闻的附加信息
_index = None
_documents = []
_metadatas = []


def _ensure_dir():
    """确保索引文件目录存在"""
    os.makedirs(CHROMA_PATH, exist_ok=True)


def _get_embedding(text: str) -> np.ndarray:
    """
    调用 DashScope text-embedding-v4 将文本转为向量
    返回归一化后的 1024 维向量，用于余弦相似度计算
    """
    resp = client.embeddings.create(model="text-embedding-v4", input=text)
    vec = np.array(resp.data[0].embedding, dtype=np.float32)
    return vec / np.linalg.norm(vec)  # L2 归一化，使内积等价于余弦相似度


def _get_embeddings_batch(texts: list[str]) -> np.ndarray:
    """
    批量获取多条文本的 embedding 向量（逐条调用，简单可靠）
    返回 shape=(n, 1024) 的 numpy 数组
    """
    vectors = []
    for text in texts:
        vectors.append(_get_embedding(text))
    return np.stack(vectors)


def _load_index():
    """
    从磁盘 pickle 文件恢复 FAISS 索引和文档数据
    在模块导入时自动调用，确保重启后索引不丢失
    """
    global _index, _documents, _metadatas
    _ensure_dir()
    if os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, "rb") as f:
            data = pickle.load(f)
            _index = data["index"]
            _documents = data["documents"]
            _metadatas = data["metadatas"]
    else:
        _index = None
        _documents = []
        _metadatas = []


def _save_index():
    """
    将当前 FAISS 索引和文档数据序列化到磁盘
    每次增/删/重建索引后自动调用
    """
    global _index, _documents, _metadatas
    _ensure_dir()
    with open(INDEX_FILE, "wb") as f:
        pickle.dump({"index": _index, "documents": _documents, "metadatas": _metadatas}, f)


def _rebuild_faiss():
    """
    用当前 _documents 列表重新创建 FAISS 索引
    步骤: 逐条获取 embedding → 构建 IndexFlatIP → 添加所有向量
    用于全量索引场景（如首次启动）
    """
    global _index, _documents
    import faiss
    if not _documents:
        _index = None
        return
    vectors = _get_embeddings_batch(_documents)
    dim = vectors.shape[1]
    _index = faiss.IndexFlatIP(dim)  # IndexFlatIP: 内积索引，配合归一化向量实现余弦相似度
    _index.add(vectors)


# 模块导入时自动加载已有索引
_load_index()


# ========== 公开接口 ==========

def index_news(news_id: int, title: str, content: str, metadata: dict):
    """
    将一篇新闻加入向量库（增量索引）
    调用时机: 管理员审核通过新闻时自动触发
    参数:
      news_id: 新闻在数据库中的 ID
      title: 新闻标题
      content: 新闻正文
      metadata: 附加信息字典（分类、作者、时间等）
    """
    global _index, _documents, _metadatas
    import faiss

    doc_text = f"标题：{title}\n{content}"
    vec = _get_embedding(doc_text).reshape(1, -1)

    _documents.append(doc_text)
    _metadatas.append({"news_id": news_id, **metadata})

    if _index is None:
        _index = faiss.IndexFlatIP(vec.shape[1])
    _index.add(vec)
    _save_index()


def remove_news(news_id: int):
    """
    从向量库中标记删除一篇新闻
    FAISS 不支持直接删除向量，采用软删除策略：
    将对应文档标记为空字符串，元数据清空，后续搜索时自动跳过
    调用时机: 管理员删除/驳回新闻时自动触发
    """
    global _documents, _metadatas
    for i, meta in enumerate(_metadatas):
        if meta.get("news_id") == news_id:
            _documents[i] = ""
            _metadatas[i] = {}
            break
    _save_index()


def search_news(query: str, k: int = 5) -> list[dict]:
    """
    语义搜索：根据用户问题找出最相关的 k 篇新闻
    原理: 将 query 转为向量 → 在 FAISS 索引中做内积搜索 → 返回得分最高的文档
    调用时机: 用户发起 AI 问答时
    返回: [{"content": "文档文本", "metadata": {...}, "score": 0.85}, ...]
    """
    global _index, _documents, _metadatas
    if _index is None or not _documents:
        return []

    vec = _get_embedding(query).reshape(1, -1)
    distances, indices = _index.search(vec, min(k * 2, len(_documents)))

    results = []
    seen = set()
    for dist, idx in zip(distances[0], indices[0]):
        if idx < 0 or idx >= len(_documents):
            continue
        if not _documents[idx]:  # 跳过已软删除的文档
            continue
        if idx in seen:
            continue
        seen.add(idx)
        results.append({
            "content": _documents[idx],
            "metadata": _metadatas[idx],
            "score": float(dist),
        })
        if len(results) >= k:
            break
    return results


def index_all_news(news_list: list) -> int:
    """
    全量重建索引：清空现有索引，重新索引所有新闻
    调用时机: 后端首次启动时（如果索引为空）
    参数: news_list = [{"id":1, "title":"...", "content":"...", ...}, ...]
    返回: 索引的文档总数
    """
    global _documents, _metadatas
    _documents = []
    _metadatas = []
    for news in news_list:
        doc_text = f"标题：{news['title']}\n{news['content']}"
        _documents.append(doc_text)
        _metadatas.append({
            "news_id": news["id"],
            "category": news.get("category", ""),
            "author": news.get("author", ""),
            "publish_time": str(news.get("publish_time", "")),
        })
    _rebuild_faiss()
    _save_index()
    return len(_documents)


def is_indexed() -> bool:
    """
    检查向量库是否已建立索引
    用于启动时判断是否需要执行全量索引
    """
    return len(_documents) > 0

from flask import Flask, request, Response, jsonify, send_from_directory
from flask_cors import CORS
from sqlalchemy import text
import sys,os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.db_config import engine
import xml.etree.ElementTree as ET
import re
import html
import json
from collections import defaultdict
from datetime import datetime, timedelta

# 停用词（用于话题聚类）
STOP_WORDS = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这', '那', '这些', '那些', '这个', '那个', '之', '与', '及', '或', '但', '而', '然而', '因为', '所以', '因此', '如果', '即使', '虽然', '尽管', '如此', '便', '由', '被', '把', '给', '让', '向', '往', '自', '从', '到', '关于', '对于', '为了', '为着', '除', '除了', '除去', 'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i', 'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at', 'this', 'but', 'his', 'by', 'from', 'they', 'we', 'say', 'her', 'she', 'or', 'an', 'will', 'my', 'one', 'all', 'would', 'there', 'their', 'what', 'so', 'up', 'out', 'if', 'about', 'who', 'get', 'which', 'go', 'me', 'when', 'make', 'can', 'like', 'time', 'no', 'just', 'him', 'know', 'take', 'people', 'into', 'year', 'your', 'good', 'some', 'could', 'them', 'see', 'other', 'than', 'then', 'now', 'look', 'only', 'come', 'its', 'over', 'think', 'also', 'back', 'after', 'use', 'two', 'how', 'our', 'work', 'first', 'well', 'way', 'even', 'new', 'want', 'because', 'any', 'these', 'give', 'day', 'most', 'us', 'is', 'was', 'are', 'were', 'been', 'has', 'had', 'did', 'does'}

# 垃圾词汇过滤（HTML元素、UI按钮、网站模板等）
JUNK_WORDS = {
    # HTML/UI元素
    'saveclick', 'share', 'click', 'button', 'btn', 'link', 'href', 'class', 'id', 'div', 'span',
    'homepage', 'posts', 'post', 'page', 'nav', 'menu', 'sidebar', 'footer', 'header', 'main',
    'secondsplay', 'video', 'audio', 'image', 'img', 'svg', 'icon', 'logo', 'banner',
    # 网站功能词汇
    'subscribe', 'follow', 'login', 'signin', 'register', 'comment', 'reply', 'share', 'like',
    'download', 'upload', 'search', 'more', 'read', 'view', 'click', 'tap', 'swipe',
    # 时间格式
    'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december',
    'jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec',
    'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday',
    'today', 'yesterday', 'tomorrow', 'day', 'week', 'month', 'year',
    # 常见无意义组合
    'artemis', 'earth', 'minister', 'talks', 'said', 'says', 'report', 'reports', 'according',
    'ap', 'reuters', 'afp', 'bbc', 'cnn', 'fox', 'news', 'breaking', 'update', 'live',
    # 新增：更多UI残留和通用无意义词
    'play', 'save', 'copy', 'paste', 'print', 'email', 'twitter', 'facebook', 'weibo', 'wechat',
    'whatsapp', 'telegram', 'linkedin', 'reddit', 'pinterest', 'tumblr', 'vk', 'ok', 'qq',
    'related', 'recommended', 'popular', 'trending', 'latest', 'featured', 'editor', 'pick',
    'gallery', 'slideshow', 'podcast', 'newsletter', 'alert', 'notification', 'popup', 'modal',
    'cookie', 'privacy', 'policy', 'terms', 'conditions', 'agreement', 'consent', 'gdpr',
    'skip', 'next', 'prev', 'previous', 'back', 'forward', 'continue', 'read', 'full', 'story',
    'expand', 'collapse', 'show', 'hide', 'toggle', 'menu', 'close', 'open', 'start', 'stop',
    'source', 'sources', 'author', 'authors', 'editor', 'editors', 'writer', 'writers',
    'published', 'updated', 'modified', 'created', 'posted', 'minutes', 'hours', 'ago',
    'widget', 'module', 'component', 'block', 'section', 'container', 'wrapper', 'holder',
}

# 中文垃圾短语过滤（正则模式）
ZH_JUNK_PATTERNS = [
    r'^\d+日?说$', r'^\d+日?称$', r'^\d+日?表示$', r'^\d+日?回应$',
    r'当地时间\d+', r'北京时间\d+', r'\d+月\d+日', r'\d+年\d+月',
    r'对此暂无回应', r'暂无回应', r'乌方对此', r'俄方对此', r'美方对此', r'中方对此',
    r'.*?新华社.*?', r'.*?央视.*?新闻.*?', r'.*?新闻网.*?',
    r'^[一二三四五六七八九十百千万亿]+$',  # 纯数字汉字
]
ZH_JUNK_PATTERN = re.compile('|'.join(ZH_JUNK_PATTERNS))

# 中文特定垃圾词（整词匹配）
ZH_JUNK_WORDS = {
    '新华社', '新华网', '央视新闻', '央视网', '人民日报', '环球时报', '界面新闻',
    '当地时间', '北京时间', '日说', '日称', '日表示', '日回应', '暂无', '对此',
    '报道称', '据报道', '消息称', '消息人士', '知情人士',
}

# 通用实体词降级（国家名、通用政治词汇等，在聚类中权重降低，不计入共享词数量）
COMMON_ENTITY_WORDS = {
    '美国', '中国', '伊朗', '俄罗斯', '乌克兰', '以色列', '朝鲜', '韩国', '日本',
    '英国', '法国', '德国', '印度', '巴基斯坦', '阿富汗', '叙利亚', '伊拉克',
    '土耳其', '埃及', '沙特', '阿联酋', '卡塔尔', '约旦', '黎巴嫩', '也门',
    '政府', '官员', '总统', '部长', '总理', '会谈', '谈判', '表示', '称', '说',
    '报道', '声明', '回应', '指出', '认为', '强调', '介绍', '国际', '国家', '地区',
    '城市', '人民', '军队', '军事', '政治', '经济', '社会', '文化', '科技', '外交',
    'trump', 'biden', 'government', 'officials', 'president', 'minister', 'prime',
    'talks', 'negotiations', 'said', 'says', 'reported', 'according', 'statement',
    'response', 'meeting', 'conference', 'summit', 'leader', 'leaders', 'country',
    'countries', 'nation', 'nations', 'world', 'global', 'region', 'regional',
    'city', 'people', 'military', 'army', 'political', 'economic', 'official',
}

def _is_zh_junk(word):
    """判断中文词是否为垃圾词"""
    if word in ZH_JUNK_WORDS:
        return True
    if ZH_JUNK_PATTERN.search(word):
        return True
    # 过滤纯数字或数字占比过高的词
    if sum(1 for c in word if c.isdigit()) / len(word) > 0.5:
        return True
    return False


try:
    import jieba
    _JIEBA_AVAILABLE = True
except ImportError:
    jieba = None
    _JIEBA_AVAILABLE = False

# 静态文件目录（生产环境）
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static')

app = Flask(__name__, static_folder=STATIC_DIR, static_url_path='')

# 配置 CORS，允许前端开发服务器访问
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:5173", "http://127.0.0.1:5173"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    },
    r"/sru*": {
        "origins": ["http://localhost:5173", "http://127.0.0.1:5173"],
        "methods": ["GET", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    },
    r"/health": {
        "origins": "*",
        "methods": ["GET", "OPTIONS"]
    }
})

class XMLSearchEngine:
    def __init__(self):
        self.engine = engine

    def search(self, query, start=1, maximum_records=20, sort_by='relevance'):
        """执行SRU搜索（XML检索增强版）"""
        try:
            with self.engine.connect() as conn:
                # 预处理查询：分词
                query_terms = self._tokenize_query(query)
                if not query_terms:
                    return self._empty_response(query, start, maximum_records)
                
                # 构建布尔查询条件
                conditions = []
                params = {}
                
                for i, term in enumerate(query_terms):
                    param_name = f'term_{i}'
                    params[param_name] = f'%{term}%'
                    # 使用JSON搜索：title_terms 和 content_terms 都包含该词
                    conditions.append(f"""
                        (JSON_SEARCH(title_terms, 'one', :{param_name}) IS NOT NULL 
                         OR JSON_SEARCH(content_terms, 'one', :{param_name}) IS NOT NULL)
                    """)
                
                # 所有词都必须出现（AND逻辑）
                where_clause = ' AND '.join(conditions)
                
                # 计数
                count_sql = f"""
                    SELECT COUNT(*) FROM news 
                    WHERE {where_clause} AND is_active = TRUE
                """
                total = conn.execute(text(count_sql), params).scalar() or 0
                
                if total == 0:
                    return self._empty_response(query, start, maximum_records)
                
                # 排序
                order_clause = 'n.created_at DESC' if sort_by == 'date' else 'n.news_id DESC'
                
                # 分页查询
                offset = max(0, start - 1)
                limit = min(maximum_records, 50)
                
                search_sql = f"""
                    SELECT 
                        n.news_id, n.title, n.summary, n.source_url,
                        n.created_at, n.language, n.has_video,
                        (SELECT country_code FROM news_countries 
                         WHERE news_id = n.news_id AND is_primary = 1 LIMIT 1) as country
                    FROM news n
                    WHERE {where_clause} AND n.is_active = TRUE
                    ORDER BY {order_clause}
                    LIMIT :limit OFFSET :offset
                """
                params['limit'] = limit
                params['offset'] = offset
                
                result = conn.execute(text(search_sql), params)
                
                records = []
                for row in result.fetchall():
                    records.append({
                        'id': row[0],
                        'title': row[1],
                        'summary': row[2],
                        'url': row[3],
                        'date': row[4].isoformat() if row[4] else None,
                        'language': row[5],
                        'country': row[7] or 'unknown',
                        'has_video': bool(row[6])
                    })
                
                return self._build_sru_response(query, start, maximum_records, total, records)
                
        except Exception as e:
            print(f"[Search Error] {e}")
            import traceback
            traceback.print_exc()
            return self._error_response(str(e))
    
    def _tokenize_query(self, query):
        """查询分词：中英文混合"""
        if not query:
            return []
        
        # 清洗
        query = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s]', ' ', query)
        terms = []
        
        # 中文用jieba
        if _JIEBA_AVAILABLE:
            words = jieba.lcut(query)
        else:
            words = query.split()
        
        for word in words:
            word = word.strip().lower()
            if not word or word in STOP_WORDS:
                continue
            if len(word) >= 2:
                terms.append(word)
        
        return list(set(terms))
    
    def _empty_response(self, query, start, maximum_records):
        return self._build_sru_response(query, start, maximum_records, 0, [])
    
    def _error_response(self, message):
        root = ET.Element('searchRetrieveResponse')
        ET.SubElement(root, 'version').text = '1.1'
        diag = ET.SubElement(root, 'diagnostics')
        ET.SubElement(diag, 'message').text = message
        return Response(ET.tostring(root, encoding='unicode'), mimetype='application/xml')
    
    def _build_sru_response(self, query, start, maximum_records, total, records):
        """构建标准SRU XML响应"""
        root = ET.Element('searchRetrieveResponse')
        
        ET.SubElement(root, 'version').text = '1.1'
        ET.SubElement(root, 'numberOfRecords').text = str(total)
        
        records_elem = ET.SubElement(root, 'records')
        
        for i, record in enumerate(records):
            record_elem = ET.SubElement(records_elem, 'record')
            ET.SubElement(record_elem, 'recordPosition').text = str(start + i)
            
            record_data = ET.SubElement(record_elem, 'recordData')
            
            # 构建DC元数据
            dc = ET.SubElement(record_data, 'dc', {
                'xmlns': 'http://purl.org/dc/elements/1.1/',
                'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance'
            })
            
            ET.SubElement(dc, 'title').text = html.escape(record.get('title', ''))
            ET.SubElement(dc, 'description').text = html.escape(record.get('summary', '')[:300])
            ET.SubElement(dc, 'identifier').text = record.get('url', '')
            ET.SubElement(dc, 'date').text = record.get('date', '')
            ET.SubElement(dc, 'language').text = record.get('language', 'zh')
            
            # 扩展字段
            ET.SubElement(dc, 'coverage').text = record.get('country', 'unknown')
            if record.get('has_video'):
                ET.SubElement(dc, 'type').text = 'video'
        
        # 添加回显参数
        echo = ET.SubElement(root, 'echoedSearchRetrieveRequest')
        ET.SubElement(echo, 'version').text = '1.1'
        ET.SubElement(echo, 'query').text = html.escape(query)
        ET.SubElement(echo, 'startRecord').text = str(start)
        ET.SubElement(echo, 'maximumRecords').text = str(maximum_records)
        
        xml_str = '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding='unicode')
        return Response(xml_str, mimetype='application/xml')


# 全局搜索引擎实例
search_engine = XMLSearchEngine()


def extract_keywords_simple(text_content, language='zh'):
    """
    从文本中提取关键词（增强版）
    - 过滤HTML标签和脚本
    - 过滤UI元素和常见垃圾词汇
    - 过滤停用词
    - 中文使用jieba分词（如可用），否则使用bigram fallback
    """
    if not text_content:
        return set()
    
    # 1. 移除HTML标签和脚本内容
    text_content = re.sub(r'<script[^>]*>.*?</script>', ' ', text_content, flags=re.DOTALL | re.IGNORECASE)
    text_content = re.sub(r'<style[^>]*>.*?</style>', ' ', text_content, flags=re.DOTALL | re.IGNORECASE)
    text_content = re.sub(r'<[^>]+>', ' ', text_content)  # 移除所有HTML标签
    
    # 2. 预清洗：移除常见UI残留组合（大小写不敏感）
    ui_patterns = [
        r'share[-\s]?save[-\s]?click', r'home[-\s]?page[-\s]?posts?', r'seconds[-\s]?play[-\s]?video',
        r'save[-\s]?click', r'share[-\s]?click', r'read[-\s]?more', r'load[-\s]?more',
        r'sign[-\s]?up', r'sign[-\s]?in', r'log[-\s]?in', r'follow[-\s]?us',
    ]
    for pattern in ui_patterns:
        text_content = re.sub(pattern, ' ', text_content, flags=re.IGNORECASE)
    
    keywords = set()
    
    if language == 'zh':
        # 中文分词：优先使用jieba
        if _JIEBA_AVAILABLE and jieba:
            words = jieba.lcut(text_content)
        else:
            # Fallback：按空格分割（兼容旧逻辑）
            words = text_content.split()
        
        for word in words:
            word = word.strip().lower()
            if not word:
                continue
            # 只保留中文和英文数字
            if not re.match(r'^[\u4e00-\u9fa5a-zA-Z0-9]+$', word):
                continue
            # 长度限制
            if not (2 <= len(word) <= 12):
                continue
            if word.isdigit():
                continue
            if word in STOP_WORDS:
                continue
            if word in JUNK_WORDS:
                continue
            if _is_zh_junk(word):
                continue
            keywords.add(word)
    else:
        words = text_content.lower().split()
        for word in words:
            word = word.strip()
            # 过滤条件
            if len(word) < 3 or len(word) > 15:  # 长度限制
                continue
            if not word.isalpha():  # 非纯字母（过滤数字混合）
                continue
            if word in STOP_WORDS:  # 停用词
                continue
            if word in JUNK_WORDS:  # 垃圾词汇
                continue
            keywords.add(word)
    
    return keywords

def jaccard_similarity(set1, set2):
    """计算Jaccard相似度"""
    if not set1 or not set2:
        return 0.0
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union > 0 else 0.0

def cluster_news_for_topics(news_list, similarity_threshold=0.35):
    """
    基于TF-IDF+余弦相似度的密度种子 + 两阶段簇中心聚类（严格版）
    - 标题关键词加权，通用实体词权重减半
    - 方法4：基于局部密度筛选簇种子，防止通用综述文当种子
    - 方法3：两阶段聚类（硬核高阈值聚核心 + 软边低阈值分配边缘）
    - 话题名基于词语共现，避免数学平均导致的拼凑
    - 反向硬校验：每篇关联新闻必须包含话题核心词的至少2个
    返回话题列表（结构与旧版保持一致）
    """
    import math
    from collections import Counter
    
    if not news_list or len(news_list) < 2:
        print(f"[Cluster] 新闻数量不足({len(news_list)}篇)，跳过聚类")
        return []
    
    TITLE_WEIGHT = 3
    HARD_THRESHOLD = 0.45      # 第一阶段：硬核聚类阈值
    SOFT_THRESHOLD = 0.30      # 第二阶段：边缘分配阈值
    DENSITY_THRESHOLD = 0.40   # 邻居密度计算阈值
    MIN_DENSITY = 3            # 成为种子的最小邻居数
    
    def _is_good_kw(kw):
        if kw in JUNK_WORDS or kw in ZH_JUNK_WORDS or _is_zh_junk(kw) or kw in COMMON_ENTITY_WORDS:
            return False
        if re.match(r'^[a-z]+$', kw) and len(kw) < 4:
            return False
        return True
    
    # 分别提取标题和正文关键词，构建带权TF向量（通用实体词权重减半）
    news_keywords = {}
    all_words = set()
    
    for news_id, title, content, language in news_list:
        title_kws = extract_keywords_simple(title, language)
        content_kws = extract_keywords_simple(content[:500], language)
        
        tf = Counter()
        for w in title_kws:
            weight = TITLE_WEIGHT * 0.5 if w in COMMON_ENTITY_WORDS else TITLE_WEIGHT
            tf[w] += weight
        for w in content_kws:
            weight = 0.5 if w in COMMON_ENTITY_WORDS else 1
            tf[w] += weight
        
        keywords_set = set(tf.keys())
        all_words.update(keywords_set)
        news_keywords[news_id] = {
            'id': news_id,
            'title': title,
            'keywords': keywords_set,
            'tf': tf
        }
    
    avg_kw = sum(len(v['keywords']) for v in news_keywords.values()) / len(news_keywords)
    print(f"[Cluster] 提取关键词完成，平均每篇 {avg_kw:.1f} 个关键词")
    
    # 计算全局IDF
    N = len(news_keywords)
    idf = {}
    for word in all_words:
        df = sum(1 for data in news_keywords.values() if word in data['tf'])
        idf[word] = math.log(N / (df + 1)) + 1.0
    
    # 构建TF-IDF向量
    vectors = {}
    for news_id, data in news_keywords.items():
        vec = {w: count * idf.get(w, 1.0) for w, count in data['tf'].items()}
        vectors[news_id] = vec
    
    def _cosine_sim(vec1, vec2):
        keys = set(vec1.keys()) | set(vec2.keys())
        dot = sum(vec1.get(k, 0) * vec2.get(k, 0) for k in keys)
        norm1 = sum(v ** 2 for v in vec1.values()) ** 0.5
        norm2 = sum(v ** 2 for v in vec2.values()) ** 0.5
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)
    
    def _cluster_center(cluster_members):
        center = Counter()
        for mid in cluster_members:
            for w, v in vectors[mid].items():
                center[w] += v
        norm = sum(v ** 2 for v in center.values()) ** 0.5
        if norm > 0:
            center = {w: v / norm for w, v in center.items()}
        return center
    
    def _quality_shared(kw_set1, kw_set2):
        shared = kw_set1 & kw_set2
        count = 0
        for w in shared:
            if w in JUNK_WORDS or w in ZH_JUNK_WORDS or _is_zh_junk(w) or w in COMMON_ENTITY_WORDS:
                continue
            if re.match(r'^[a-z]+$', w) and len(w) < 4:
                continue
            count += 1
        return count
    
    # ===== 方法4：计算局部密度，筛选高质量种子 =====
    for news_id in news_keywords:
        density = 0
        for other_id in news_keywords:
            if other_id == news_id:
                continue
            if _cosine_sim(vectors[news_id], vectors[other_id]) >= DENSITY_THRESHOLD:
                density += 1
        news_keywords[news_id]['density'] = density
    
    sorted_by_density = sorted(news_keywords.keys(), key=lambda x: news_keywords[x]['density'], reverse=True)
    seeds = [nid for nid in sorted_by_density if news_keywords[nid]['density'] >= MIN_DENSITY]
    
    # 如果种子太少，动态放宽到前30%（至少3个）
    if len(seeds) < max(3, int(len(sorted_by_density) * 0.3)):
        seeds = sorted_by_density[:max(3, int(len(sorted_by_density) * 0.3))]
    
    non_seeds = [nid for nid in sorted_by_density if nid not in seeds]
    print(f"[Cluster] 种子筛选完成：{len(seeds)} 个种子，{len(non_seeds)} 个非种子")
    
    # ===== 方法3：第一阶段 - 硬核聚类（仅对种子） =====
    clusters = []
    processed = set()
    
    for seed_id in seeds:
        if seed_id in processed:
            continue
        
        cluster = [seed_id]
        processed.add(seed_id)
        
        for other_id in seeds:
            if other_id in processed:
                continue
            center = _cluster_center(cluster)
            sim = _cosine_sim(center, vectors[other_id])
            shared_quality = _quality_shared(news_keywords[seed_id]['keywords'], news_keywords[other_id]['keywords'])
            
            if sim >= HARD_THRESHOLD or shared_quality >= 3:
                cluster.append(other_id)
                processed.add(other_id)
        
        clusters.append(cluster)
    
    print(f"[Cluster] 硬核聚类完成，形成 {len(clusters)} 个核心簇")
    for i, c in enumerate(clusters[:5]):
        print(f"[Cluster]  核心簇{i+1}: {len(c)} 篇")
    
    # ===== 方法3：第二阶段 - 边缘分配（非种子分配到最近的核心簇） =====
    orphan_news = []
    for news_id in non_seeds:
        best_idx = None
        best_sim = 0
        for idx, cluster in enumerate(clusters):
            center = _cluster_center(cluster)
            sim = _cosine_sim(center, vectors[news_id])
            if sim > best_sim:
                best_sim = sim
                best_idx = idx
        
        if best_idx is not None and best_sim >= SOFT_THRESHOLD:
            clusters[best_idx].append(news_id)
            processed.add(news_id)
        else:
            orphan_news.append(news_id)
    
    # 未分配的孤立新闻，不强行合并，各自成单篇簇
    for nid in orphan_news:
        clusters.append([nid])
        processed.add(nid)
    
    print(f"[Cluster] 边缘分配完成，{len(non_seeds) - len(orphan_news)} 篇分配成功，{len(orphan_news)} 篇保持独立")
    
    # ===== 话题名生成：基于词语共现 =====
    def _generate_topic_name(cluster):
        """基于共现频率生成话题名，返回 (topic_name, core_keywords)"""
        kw_freq = Counter()
        for nid in cluster:
            for w in news_keywords[nid]['keywords']:
                if _is_good_kw(w):
                    kw_freq[w] += 1
        
        good_kws = [w for w, c in kw_freq.most_common(20) if c >= 2]
        if not good_kws:
            return None, []
        
        # 计算共现矩阵
        cooccur = Counter()
        for nid in cluster:
            article_kws = [w for w in news_keywords[nid]['keywords'] if w in good_kws]
            for i, w1 in enumerate(article_kws):
                for w2 in article_kws[i+1:]:
                    if w1 != w2:
                        pair = tuple(sorted([w1, w2]))
                        cooccur[pair] += 1
        
        min_cooccur = max(2, int(len(cluster) * 0.3))
        valid_pairs = [(pair, cnt) for pair, cnt in cooccur.items() if cnt >= min_cooccur]
        
        if valid_pairs:
            valid_pairs.sort(key=lambda x: x[1], reverse=True)
            w1, w2 = valid_pairs[0][0]
            core_words = [w1, w2]
            
            # 尝试找第三个共现词
            best_w3 = None
            best_co = 0
            for w in good_kws:
                if w in (w1, w2):
                    continue
                cnt1 = sum(1 for nid in cluster if w in news_keywords[nid]['keywords'] and w1 in news_keywords[nid]['keywords'])
                cnt2 = sum(1 for nid in cluster if w in news_keywords[nid]['keywords'] and w2 in news_keywords[nid]['keywords'])
                if cnt1 >= min_cooccur and cnt2 >= min_cooccur and cnt1 + cnt2 > best_co:
                    best_co = cnt1 + cnt2
                    best_w3 = w
            
            if best_w3:
                core_words.append(best_w3)
                return '·'.join(core_words), core_words
            else:
                return f"{w1}·{w2}", core_words
        else:
            # 兜底：单个最高频关键词
            return good_kws[0], [good_kws[0]]
    
    # 生成话题信息
    topics = []
    for cluster in clusters:
        topic_name, core_keywords = _generate_topic_name(cluster)
        
        # 兜底：共现失败则用标题
        if not topic_name:
            rep_title = news_keywords[cluster[0]]['title']
            if rep_title:
                title_clean = rep_title
                title_clean = re.sub(r'^[\u4e00-\u9fa5]{2,5}[：:|]', '', title_clean)
                title_clean = re.sub(r'[_|｜][\u4e00-\u9fa5a-zA-Z]+$', '', title_clean)
                title_clean = re.sub(r'(\d+日说|\d+日称|\d+日表示|\d+日回应|当地时间\d+日|暂无回应)$', '', title_clean)
                title_clean = title_clean.strip()
                if title_clean and len(title_clean) >= 6 and not re.search(r'(share|saveclick|homepage|posts|secondsplay|video)', title_clean, re.IGNORECASE):
                    topic_name = title_clean[:18] + "..." if len(title_clean) > 18 else title_clean
            # 标题兜底时，core_keywords 用簇内 top3 高质量词
            kw_freq = Counter()
            for nid in cluster:
                for w in news_keywords[nid]['keywords']:
                    if _is_good_kw(w):
                        kw_freq[w] += 1
            core_keywords = [w for w, _ in kw_freq.most_common(3)]
        
        if not topic_name:
            print(f"[Topics] 丢弃簇（无法生成话题名）：{news_keywords[cluster[0]]['title'][:30]}...")
            continue
        if len(re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', '', topic_name)) < 3:
            print(f"[Topics] 丢弃簇（话题名过短）：'{topic_name}'")
            continue
        if re.search(r'(share|saveclick|homepage|posts|secondsplay|seconds|play)', topic_name, re.IGNORECASE):
            print(f"[Topics] 丢弃簇（包含UI垃圾词）：'{topic_name}'")
            continue
        
        # ===== 反向硬校验：新闻必须包含至少2个话题核心词 =====
        if len(core_keywords) >= 2:
            filtered_cluster = [
                nid for nid in cluster
                if len(set(news_keywords[nid]['keywords']) & set(core_keywords)) >= 2
            ]
            if len(filtered_cluster) == 0:
                print(f"[Topics] 丢弃簇（反向校验无通过成员）：'{topic_name}'")
                continue
            if len(filtered_cluster) < len(cluster):
                print(f"[Topics] 反向校验剔除 {len(cluster) - len(filtered_cluster)} 篇不相关新闻，从 '{topic_name}' ({len(cluster)}->{len(filtered_cluster)})")
                cluster = filtered_cluster
        
        # 统计最终关键词
        keyword_freq = Counter()
        for news_id in cluster:
            for w, cnt in news_keywords[news_id]['tf'].items():
                keyword_freq[w] += cnt
        top_keywords = [kw for kw, _ in keyword_freq.most_common(10)]
        good_keywords = [kw for kw in top_keywords if _is_good_kw(kw)]
        
        if len(good_keywords) < 2 and len(cluster) < 2:
            print(f"[Topics] 丢弃低质量簇（仅{len(cluster)}条新闻，高质量词{len(good_keywords)}个）：'{topic_name}'")
            continue
        
        print(f"[Topics] 生成话题：'{topic_name}'（{len(cluster)}篇新闻）")
        topics.append({
            'name': topic_name,
            'keywords': top_keywords,
            'news_ids': cluster,
            'news_count': len(cluster),
            'representative_id': cluster[0]
        })
    
    topics.sort(key=lambda x: x['news_count'], reverse=True)
    return topics

def update_hot_topics_internal():
    """内部函数：更新热点话题到数据库"""
    print(f"[{datetime.now()}] 开始更新热点话题...")
    
    with engine.connect() as conn:
        # 获取48小时内的新闻
        result = conn.execute(text("""
            SELECT news_id, title, content, language
            FROM news
            WHERE created_at > DATE_SUB(NOW(), INTERVAL 48 HOUR)
            ORDER BY created_at DESC
        """))
        
        news_list = [(row[0], row[1], row[2] or '', row[3] or 'zh') for row in result.fetchall()]
        
        if len(news_list) < 2:
            print(f"新闻数量不足({len(news_list)}篇)，跳过聚类")
            return 0
        
        print(f"获取到 {len(news_list)} 篇新闻，开始聚类...")
        
        # 聚类（使用函数默认阈值）
        topics = cluster_news_for_topics(news_list)
        
        if not topics:
            print("聚类结果为空")
            return 0
        
        print(f"聚类完成，生成 {len(topics)} 个话题")
        
        # 清空旧话题
        conn.execute(text("""
            DELETE nt FROM news_topics nt
            JOIN hot_topics ht ON nt.topic_id = ht.topic_id
            WHERE ht.is_active = TRUE
        """))
        conn.execute(text("DELETE FROM hot_topics WHERE is_active = TRUE"))
        
        # 插入新话题
        inserted_count = 0
        for topic in topics[:15]:  # Top15
            news_times = []
            for nid in topic['news_ids']:
                for n in news_list:
                    if n[0] == nid:
                        news_times.append(datetime.now())  # 简化处理
                        break
            
            first_time = min(news_times) if news_times else datetime.now()
            last_time = max(news_times) if news_times else datetime.now()
            
            result = conn.execute(text("""
                INSERT INTO hot_topics 
                (topic_name, topic_keywords, news_count, first_news_time, last_news_time, is_active)
                VALUES (:name, :keywords, :count, :first_time, :last_time, TRUE)
            """), {
                'name': topic['name'][:200],
                'keywords': json.dumps(topic['keywords'], ensure_ascii=False),
                'count': topic['news_count'],
                'first_time': first_time,
                'last_time': last_time
            })
            
            topic_id = conn.execute(text("SELECT LAST_INSERT_ID()")).scalar()
            
            # 插入关联
            for news_id in topic['news_ids']:
                is_rep = (news_id == topic['representative_id'])
                conn.execute(text("""
                    INSERT INTO news_topics (news_id, topic_id, similarity_score, is_representative)
                    VALUES (:news_id, :topic_id, 1.0, :is_rep)
                """), {'news_id': news_id, 'topic_id': topic_id, 'is_rep': is_rep})
            
            inserted_count += 1
        
        conn.commit()
        
        # 验证数据一致性
        verify_result = conn.execute(text("""
            SELECT ht.topic_id, ht.news_count, COUNT(nt.news_id) as actual_count
            FROM hot_topics ht
            LEFT JOIN news_topics nt ON ht.topic_id = nt.topic_id
            WHERE ht.is_active = TRUE
            GROUP BY ht.topic_id
            HAVING ht.news_count != COUNT(nt.news_id)
        """))
        inconsistent = verify_result.fetchall()
        if inconsistent:
            for row in inconsistent:
                print(f"[Warning] 话题{row[0]}数量不一致: 记录{row[1]} vs 实际{row[2]}")
        
        print(f"话题更新完成，共 {inserted_count} 个话题")
        return inserted_count


# 来源类型到颜色的映射
SOURCE_TYPE_COLORS = {
    'rss': '#3498db',      # 蓝色
    'api': '#2ecc71',      # 绿色
    'crawler': '#e74c3c',  # 红色
}

# 可信度评分到颜色的映射
def get_reliability_color(score):
    """根据可信度评分返回颜色"""
    if score >= 9:
        return '#27ae60'  # 深绿 - 极高可信度
    elif score >= 7:
        return '#2ecc71'  # 绿色 - 高可信度
    elif score >= 5:
        return '#f39c12'  # 橙色 - 中等可信度
    else:
        return '#e74c3c'  # 红色 - 低可信度


@app.route('/api/sources', methods=['GET'])
def get_sources():
    """
    获取所有新闻来源
    返回格式: [{"name": "36氪", "logo": "36", "color": "#3498db", "type": "rss"}, ...]
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT 
                    source_name,
                    source_type,
                    reliability_score
                FROM sources
                ORDER BY source_id ASC
            """))
            
            sources = []
            for row in result.fetchall():
                name = row[0]
                source_type = row[1]
                reliability = row[2] or 5
                
                # 生成 logo（取前1-2个字符）
                logo = name[:2] if len(name) >= 2 else name[:1]
                
                # 根据类型选择颜色，或根据可信度
                if source_type in SOURCE_TYPE_COLORS:
                    color = SOURCE_TYPE_COLORS[source_type]
                else:
                    color = get_reliability_color(reliability)
                
                sources.append({
                    "name": name,
                    "logo": logo,
                    "color": color,
                    "type": source_type,
                    "reliability": reliability
                })
            
            return jsonify(sources)
    except Exception as e:
        print(f"[API Error] get_sources: {e}")
        import traceback
        traceback.print_exc()
        return jsonify([]), 500

@app.route('/api/topics', methods=['GET'])
def get_hot_topics():
    """
    获取热点话题 TOP 10（带代表新闻详情）
    """
    try:
        topics = get_topic_news()
        return jsonify(topics)
    except Exception as e:
        print(f"[API Error] get_hot_topics: {e}")
        import traceback
        traceback.print_exc()
        return jsonify([]), 500

def get_topic_news():
    """
    获取热点话题及代表新闻（兼容版）
    """
    try:
        with engine.connect() as conn:
            # 获取热点话题
            result = conn.execute(text("""
                SELECT topic_id, topic_name, news_count
                FROM hot_topics
                WHERE is_active = TRUE
                ORDER BY news_count DESC, last_news_time DESC
                LIMIT 10
            """))
            
            topics = []
            for row in result.fetchall():
                topic_id = row[0]
                topic_name = row[1]
                count = row[2]
                
                # 查询话题下的新闻
                result_news = conn.execute(text("""
                    SELECT 
                        n.news_id, n.title, n.summary, n.source_url,
                        n.created_at, n.language, n.has_video,
                        nt.is_representative,
                        (SELECT country_code FROM news_countries 
                         WHERE news_id = n.news_id AND is_primary = 1 LIMIT 1) as country
                    FROM news n
                    JOIN news_topics nt ON n.news_id = nt.news_id
                    WHERE nt.topic_id = :topic_id
                    ORDER BY nt.is_representative DESC, n.created_at DESC
                    LIMIT :limit
                """), {'topic_id': topic_id, 'limit': 20})
                
                news_list = []
                for news_row in result_news.fetchall():
                    news_list.append({
                        'id': news_row[0],
                        'title': news_row[1],
                        'summary': news_row[2],
                        'url': news_row[3],
                        'date': news_row[4].isoformat() if news_row[4] else None,
                        'language': news_row[5],
                        'has_video': bool(news_row[6]),
                        'is_representative': bool(news_row[7]),
                        'country': news_row[8] or 'unknown'
                    })
                
                topics.append({
                    'id': topic_id,
                    'name': topic_name,
                    'count': count,
                    'news': news_list
                })
            
            return topics
    except Exception as e:
        print(f"[API Error] get_topic_news: {e}")
        import traceback
        traceback.print_exc()
        return []

@app.route('/api/search', methods=['GET'])
def api_search():
    """API搜索端点"""
    query = request.args.get('q', '')
    start = int(request.args.get('start', 1))
    limit = int(request.args.get('limit', 20))
    sort = request.args.get('sort', 'relevance')
    
    if not query:
        return jsonify({'error': '缺少查询参数 q'}), 400
    
    try:
        xml_response = search_engine.search(query, start, limit, sort)
        return Response(xml_response.get_data(as_text=True), mimetype='application/xml')
    except Exception as e:
        print(f"[API Error] api_search: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/sru', methods=['GET'])
def sru_search():
    """标准SRU搜索端点"""
    query = request.args.get('query', '')
    start = int(request.args.get('startRecord', 1))
    limit = int(request.args.get('maximumRecords', 20))
    sort = request.args.get('sortKeys', 'relevance')
    
    if not query:
        root = ET.Element('searchRetrieveResponse')
        ET.SubElement(root, 'version').text = '1.1'
        diag = ET.SubElement(root, 'diagnostics')
        ET.SubElement(diag, 'message').text = 'Missing query parameter'
        xml_str = '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding='unicode')
        return Response(xml_str, mimetype='application/xml', status=400)
    
    try:
        return search_engine.search(query, start, limit, sort)
    except Exception as e:
        print(f"[API Error] sru_search: {e}")
        import traceback
        traceback.print_exc()
        root = ET.Element('searchRetrieveResponse')
        ET.SubElement(root, 'version').text = '1.1'
        diag = ET.SubElement(root, 'diagnostics')
        ET.SubElement(diag, 'message').text = str(e)
        xml_str = '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding='unicode')
        return Response(xml_str, mimetype='application/xml', status=500)

@app.route('/api/dashboard', methods=['GET'])
def get_dashboard():
    """
    获取Dashboard数据
    """
    try:
        with engine.connect() as conn:
            # 1. 国家分布（Top10）
            country_result = conn.execute(text("""
                SELECT country_code, COUNT(*) as cnt
                FROM news_countries
                WHERE news_id IN (SELECT news_id FROM news WHERE is_active = TRUE AND created_at > DATE_SUB(NOW(), INTERVAL 48 HOUR))
                AND is_primary = 1
                GROUP BY country_code
                ORDER BY cnt DESC
                LIMIT 10
            """))
            countries = []
            for row in country_result.fetchall():
                countries.append({
                    'code': row[0],
                    'count': row[1]
                })
            
            # 2. 24小时趋势（按小时统计）
            trend_result = conn.execute(text("""
                SELECT 
                    DATE_FORMAT(created_at, '%Y-%m-%d %H:00') as hour,
                    COUNT(*) as cnt
                FROM news
                WHERE created_at > DATE_SUB(NOW(), INTERVAL 24 HOUR)
                GROUP BY hour
                ORDER BY hour
            """))
            trends = []
            for row in trend_result.fetchall():
                trends.append({
                    'hour': row[0],
                    'count': row[1]
                })
            
            # 3. 最新新闻（Top20）
            latest_result = conn.execute(text("""
                SELECT 
                    n.news_id, n.title, n.summary, n.source_url,
                    n.created_at, n.language, n.has_video,
                    s.source_name,
                    (SELECT country_code FROM news_countries 
                     WHERE news_id = n.news_id AND is_primary = 1 LIMIT 1) as country
                FROM news n
                JOIN sources s ON n.source_id = s.source_id
                WHERE n.is_active = TRUE
                ORDER BY n.created_at DESC
                LIMIT 20
            """))
            latest = []
            for row in latest_result.fetchall():
                latest.append({
                    'id': row[0],
                    'title': row[1],
                    'summary': row[2],
                    'url': row[3],
                    'date': row[4].isoformat() if row[4] else None,
                    'language': row[5],
                    'has_video': bool(row[6]),
                    'source': row[7],
                    'country': row[8] or 'unknown'
                })
            
            return jsonify({
                'countries': countries,
                'trends': trends,
                'latest': latest
            })
    except Exception as e:
        print(f"[API Error] get_dashboard: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()})

@app.route('/', methods=['GET'])
def index():
    """静态文件入口"""
    return send_from_directory(STATIC_DIR, 'index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)

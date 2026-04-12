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
                    WHERE {where_clause}
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
                    WHERE {where_clause}
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

def _lcs_length(a, b):
    """最长公共连续子串长度"""
    m, n = len(a), len(b)
    if m == 0 or n == 0:
        return 0
    max_len = 0
    dp = [0] * (n + 1)
    for i in range(1, m + 1):
        prev = 0
        for j in range(1, n + 1):
            temp = dp[j]
            if a[i-1] == b[j-1]:
                dp[j] = prev + 1
                if dp[j] > max_len:
                    max_len = dp[j]
            else:
                dp[j] = 0
            prev = temp
    return max_len

def extract_hot_topics(news_list):
    """
    基于标题事件短语提取的热点话题生成（改进版）
    - jieba词性标注约束，只保留包含命名实体的事件级短语
    - TF-IDF加权过滤通用词组合
    - 关联新闻 = 标题精确包含该短语的最近新闻
    返回话题列表（结构与旧版保持一致）
    """
    import math
    from collections import Counter
    
    if not news_list or len(news_list) < 2:
        return []
    
    # 扩展通用动词/无意义词集合（用于中文过滤）
    common_verbs = COMMON_ENTITY_WORDS | {
        '发展', '推动', '促进', '加强', '推进', '提高', '提升', '增强', '扩大',
        '深化', '完善', '落实', '实现', '确保', '坚持', '维护', '保障', '服务',
        '管理', '监督', '检查', '调查', '研究', '分析', '总结', '说明', '宣布',
        '发布', '签署', '达成', '举行', '召开', '访问', '会见', '会谈', '协商',
        '合作', '交流', '互动', '联系', '沟通', '协调', '配合', '支持', '帮助',
        '协助', '参与', '参加', '加入', '入选', '荣获', '获得', '取得', '完成',
        '结束', '启动', '开幕', '闭幕', '举办', '开展', '组织', '策划', '实施',
        '执行', '制定', '修订', '修改', '调整', '改革', '创新', '探索', '尝试',
        '努力', '奋斗', '争取', '期待', '希望', '成为', '需要', '可以', '没有',
        '随着', '根据', '由于', '但是', '并且', '同时', '其中', '其他', '相关',
        '实施', '计划', '回应', '声明', '报道', '称', '说', '谈', '访问', '谈判',
        '会议', '活动', '工作', '问题', '情况', '方面', '建设', '开始', '已经',
        '正在', '继续', '持续', '保持', '发生', '出现', '达到', '超过', '接近',
        '进入', '退出', '返回', '到达', '离开', '前往', '参观', '视察', '检阅',
        '会晤', '商谈', '商讨', '协定', '协议', '条约', '合同', '签订', '缔结',
        '赢得', '博得', '落得', '处理', '处置', '办理', '承办', '经办', '主办',
        '操办', '筹办', '兴办', '复办', '停办', '撤办', '创建', '创办', '创立',
        '建立', '树立', '设立', '设置', '开设', '开办', '撤销', '取消', '废除',
        '废止', '停止', '终止', '中止', '暂停', '中断', '间断', '连续', '陆续',
        '延续', '延长', '延展', '延伸', '蔓延', '延续', '沿袭', '因袭', '承袭',
        '世袭', '传袭', '抄袭', '剽袭', '侵袭', '袭击', '偷袭', '突袭', '奇袭',
        '空袭', '夜袭', '袭扰', '袭取', '袭占', '袭来', '逆袭', '反袭', '回击',
        '还击', '反击', '反攻', '反扑', '反制', '反抗', '反对', '反驳', '反诘',
        '反问', '反诉', '反告', '反咬', '反噬', '反馈', '反应', '反映', '反响',
        '回答', '答复', '回复', '批复', '批答', '答批', '核批', '审批', '报批',
        '呈批', '转批', '加批', '眉批', '旁批', '朱批', '总批', '点评', '评论',
        '议论', '讨论', '谈论', '研讨', '研判', '深究', '探究', '侦察', '侦查',
        '勘察', '勘测', '勘探', '勘查', '踏勘', '校勘', '推勘', '查勘', '勘误',
        '勘正', '校正', '校对', '校核', '核算', '计算', '累计', '总计', '合计',
        '共计', '约计', '算计', '盘算', '筹算', '测算', '推算', '演算', '验算',
        '审计', '稽核', '考核', '考查', '考察', '检验', '检测', '检疫', '查验',
        '查收', '查访', '查询', '查究', '查抄', '查封', '查扣', '查禁', '查处',
        '查办', '查缉', '查核', '审查', '核查', '稽查', '缉查', '探查', '测查',
        '普查', '巡查', '抽查', '排查', '彻查', '严查', '清查', '盘查', '纠查',
        '访查', '侦', '察', '观', '看', '望', '瞧', '视', '盯', '瞄', '瞥',
        '瞅', '瞪', '睹', '窥', '凝视', '注视', '审视', '重视', '轻视', '忽视',
        '漠视', '无视', '蔑视', '藐视', '小视', '鄙视', '歧视', '敌视', '仇视',
    }
    
    def _is_valid_phrase(words, flags):
        """验证短语的词性是否构成有效事件"""
        # 必须至少包含1个命名实体
        has_entity = any(f.startswith(('nr', 'ns', 'nt', 'nz', 'j')) for f in flags)
        if not has_entity:
            return False
        # 通用动词不能超过1个
        verb_count = sum(1 for w, f in zip(words, flags) if w in common_verbs or f.startswith('v'))
        if verb_count > 1:
            return False
        # 不能全是虚词/形容词/副词/数词/量词
        content_count = sum(1 for f in flags if not f.startswith(('d', 'p', 'c', 'u', 'e', 'y', 'o', 'm', 'q', 'a')))
        if content_count < 1:
            return False
        return True
    
    # 收集候选短语
    phrase_data = {}  # phrase -> {'news_ids': set, 'count': int}
    all_words = Counter()
    
    for news_id, title, content, language in news_list:
        if not title:
            continue
        
        if language == 'zh':
            import jieba.posseg as pseg
            words_flags = list(pseg.cut(title))
            # 按停用词/单字/数字分割
            chunks = []
            current = []
            for w, f in words_flags:
                w = w.strip()
                if not w or w.isdigit() or len(w) == 1 or w in STOP_WORDS:
                    if current:
                        chunks.append(current)
                        current = []
                    continue
                current.append((w, f))
            if current:
                chunks.append(current)
            
            for chunk in chunks:
                if len(chunk) < 2:
                    continue
                for n in range(min(3, len(chunk)), 1, -1):
                    for i in range(len(chunk) - n + 1):
                        words = [item[0] for item in chunk[i:i+n]]
                        flags = [item[1] for item in chunk[i:i+n]]
                        phrase = ''.join(words)
                        if len(phrase) < 4:
                            continue
                        if not _is_valid_phrase(words, flags):
                            continue
                        if phrase not in phrase_data:
                            phrase_data[phrase] = {'news_ids': set(), 'count': 0}
                        phrase_data[phrase]['news_ids'].add(news_id)
                        phrase_data[phrase]['count'] = len(phrase_data[phrase]['news_ids'])
                        for w in words:
                            all_words[w] += 1
        else:
            # 英文：保留2-gram/3-gram，要求包含至少一个内容词
            words = re.findall(r'\b[a-zA-Z]+\b', title.lower())
            words = [w for w in words if len(w) >= 3 and w not in STOP_WORDS]
            for n in range(3, 1, -1):
                if len(words) < n:
                    continue
                for i in range(len(words) - n + 1):
                    phrase_words = words[i:i+n]
                    phrase = ' '.join(phrase_words)
                    content_words = [w for w in phrase_words if w not in common_verbs and w not in STOP_WORDS]
                    if len(content_words) < 1:
                        continue
                    if phrase not in phrase_data:
                        phrase_data[phrase] = {'news_ids': set(), 'count': 0}
                    phrase_data[phrase]['news_ids'].add(news_id)
                    phrase_data[phrase]['count'] = len(phrase_data[phrase]['news_ids'])
                    for w in phrase_words:
                        all_words[w] += 1
    
    if not phrase_data:
        return []
    
    # 计算IDF
    N = len(news_list)
    idf = {}
    for word, freq in all_words.items():
        idf[word] = math.log(N / (freq + 1)) + 1.0
    
    # 计算短语得分
    scored_phrases = []
    for phrase, data in phrase_data.items():
        doc_freq = data['count']
        if doc_freq < 2:
            continue
        # 拆分词
        if ' ' in phrase:
            words = phrase.split()
        else:
            words = list(jieba.cut(phrase))
        avg_idf = sum(idf.get(w, 1.0) for w in words) / len(words) if words else 1.0
        if avg_idf < 1.3:  # 过滤通用词组合
            continue
        length = len(words)
        score = doc_freq * avg_idf * (1 + 0.15 * length)
        scored_phrases.append((phrase, score, doc_freq, data['news_ids']))
    
    # LCS重叠合并（阈值30%）
    scored_phrases.sort(key=lambda x: x[1], reverse=True)
    merged = []
    for phrase, score, doc_freq, news_ids in scored_phrases:
        is_dup = False
        for merged_phrase, _, _, _ in merged:
            if phrase in merged_phrase or merged_phrase in phrase:
                is_dup = True
                break
            lcs = _lcs_length(phrase, merged_phrase)
            shorter = min(len(phrase), len(merged_phrase))
            if shorter > 0 and lcs / shorter > 0.3:
                is_dup = True
                break
        if not is_dup:
            merged.append((phrase, score, doc_freq, news_ids))
    
    # 生成话题
    topics = []
    for phrase, score, doc_freq, news_ids in merged[:15]:
        related_ids = []
        for nid, title, _, lang in news_list:
            if nid not in news_ids:
                continue
            if lang == 'zh':
                if phrase in title:
                    related_ids.append(nid)
            else:
                if phrase in title.lower():
                    related_ids.append(nid)
        
        if len(related_ids) < 2:
            continue
        
        representative_id = related_ids[0]
        topics.append({
            'name': phrase,
            'keywords': [phrase],
            'news_ids': related_ids,
            'news_count': len(related_ids),
            'representative_id': representative_id
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
        
        # 提取热点话题（基于标题事件短语）
        topics = extract_hot_topics(news_list)
        
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
                WHERE news_id IN (SELECT news_id FROM news WHERE created_at > DATE_SUB(NOW(), INTERVAL 48 HOUR))
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

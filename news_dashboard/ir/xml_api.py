from flask import Flask, request, Response, jsonify
from flask_cors import CORS
from sqlalchemy import text
import sys,os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.db_config import engine
import xml.etree.ElementTree as ET
import re
import html
import json

app = Flask(__name__)

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
    
    def parse_query(self, query_str):
        """
        解析查询字符串：
        - 支持字段限定：title:中国, content:经济, country:US
        - 支持布尔逻辑：AND, OR, NOT（简化实现为AND）
        """
        # 提取字段限定
        xpath_map = {
            'title': '/news/title',
            'content': '/news/content',
            'country': '/news/metadata/country'
        }
        
        xpath_filter = None
        clean_query = query_str
        
        # 检查字段限定
        if ':' in query_str and not '://' in query_str:
            parts = query_str.split(':')
            if len(parts) >= 2 and parts[0].lower() in xpath_map:
                xpath_filter = xpath_map[parts[0].lower()]
                clean_query = ':'.join(parts[1:]).strip()
    
        # 分词（简化版，与processor一致）
        lang = 'zh' if any('\u4e00' <= c <= '\u9fff' for c in clean_query) else 'en'
    
        if lang == 'zh':
            terms = [clean_query[i:i+2] for i in range(len(clean_query)-1) if '\u4e00' <= clean_query[i] <= '\u9fff']
            terms = list(set(terms))
        else:
            # 【修复】对国家代码特殊处理：允许2字符长度
            if xpath_filter == '/news/metadata/country':
                # 国家查询：直接保留原词（不转小写，不限制长度>2）
                terms = [clean_query.strip()]
            else:
                # 普通英文查询：保留>2字符的词
                terms = [t.lower() for t in re.findall(r'\b\w+\b', clean_query) if len(t) > 2]
    
        return terms, lang, xpath_filter
    
    def _get_latest_news(self, max_results=20, offset=0):
        """获取最新新闻（内部方法，用于 * 查询）"""
        sql = text("""
            SELECT 
                n.news_id,
                n.xml_content,
                n.title,
                n.created_at,
                1.0 as score,
                1 as match_count
            FROM news n
            WHERE n.created_at > DATE_SUB(NOW(), INTERVAL 48 HOUR)
            ORDER BY n.created_at DESC
            LIMIT :limit OFFSET :offset
        """)
        
        with self.engine.connect() as conn:
            rows = conn.execute(sql, {'limit': max_results, 'offset': offset}).fetchall()
            results = []
            for r in rows:
                try:
                    xml_root = ET.fromstring(r[1] if r[1] else f'<news id="{r[0]}"><title>{html.escape(r[2])}</title></news>')
                    results.append({
                        'id': r[0], 'xml': r[1], 'title': r[2], 
                        'score': r[4], 'time': r[3]
                    })
                except:
                    results.append({
                        'id': r[0], 'xml': r[1], 'title': r[2], 
                        'score': r[4], 'time': r[3]
                    })
            return results, len(results)

    def search(self, query_str, max_results=20, offset=0):
        """执行XML检索"""
        
        # 【新增】查询为 * 时，直接返回最新新闻（用于 getLatestNews）
        if query_str.strip() == '*':
            return self._get_latest_news(max_results, offset)
        
        terms, lang, xpath = self.parse_query(query_str)
    
        # 【新增】国家查询特殊处理（强制大写 + 直接查 news_countries 表）
        if xpath == '/news/metadata/country':
            print(f"Debug: xpath={xpath}, terms={terms}, lang={lang}")
            if not terms:
                return [], 0
        
            # 转大写：us -> US, cn -> CN
            country_codes = [t.upper() for t in terms if len(t) >= 2]
            if not country_codes:
                return [], 0
        
            # 直接查 news_countries 表（精确匹配，不依赖倒排索引的大小写）
            # 【统一主要关联国逻辑】只查询 is_primary = TRUE 的记录，与热力图保持一致
            placeholders = ', '.join([f':c{i}' for i in range(len(country_codes))])
            sql = text(f"""
                SELECT 
                    n.news_id,
                    n.xml_content,
                    n.title,
                    n.created_at,
                    1.5 as score,
                    1 as match_count
                FROM news n
                JOIN news_countries nc ON n.news_id = nc.news_id AND nc.is_primary = TRUE
                WHERE nc.country_code IN ({placeholders})
                  AND n.created_at > DATE_SUB(NOW(), INTERVAL 48 HOUR)
                ORDER BY n.created_at DESC
                LIMIT :limit OFFSET :offset
            """)
        
            params = {f'c{i}': c for i, c in enumerate(country_codes)}
            params.update({'limit': max_results, 'offset': offset})
        
            with self.engine.connect() as conn:
                rows = conn.execute(sql, params).fetchall()
                results = []
                for r in rows:
                    try:
                        xml_root = ET.fromstring(r[1] if r[1] else f'<news id="{r[0]}"><title>{html.escape(r[2])}</title></news>')
                        results.append({
                            'id': r[0], 'xml': r[1], 'title': r[2], 
                            'score': r[4], 'time': r[3]
                        })
                    except:
                        results.append({
                            'id': r[0], 'xml': r[1], 'title': r[2], 
                            'score': r[4], 'time': r[3]
                        })
                return results, len(results)
    
        # 原有的 title/content 查询逻辑保持不变...
        if not terms:
            return [], 0
    
        term_list = terms[:5]
        placeholders = ', '.join([f':t{i}' for i in range(len(term_list))])
        
        # 基础查询
        sql = f"""
            SELECT 
                n.news_id,
                n.xml_content,
                n.title,
                n.created_at,
                SUM(ii.tf_weight) as score,
                COUNT(DISTINCT ii.term) as match_count
            FROM inverted_index ii
            JOIN news n ON ii.news_id = n.news_id
            WHERE ii.term IN ({placeholders})
              AND ii.language = :lang
              AND n.created_at > DATE_SUB(NOW(), INTERVAL 48 HOUR)
        """
        
        # 添加XPath限定
        if xpath:
            sql += " AND ii.xpath_path = :xpath"
        
        sql += """
            GROUP BY n.news_id
            HAVING match_count >= :min_match
            ORDER BY score DESC, n.created_at DESC
            LIMIT :limit OFFSET :offset
        """
        
        params = {f't{i}': t for i, t in enumerate(term_list)}
        params.update({
            'lang': lang,
            'min_match': max(1, len(term_list) * 0.5),  # 至少匹配50%的词
            'limit': max_results,
            'offset': offset
        })
        
        if xpath:
            params['xpath'] = xpath
        
        with self.engine.connect() as conn:
            rows = conn.execute(text(sql), params).fetchall()
            results = []
            for r in rows:
                try:
                    # 解析XML提取结构化数据
                    xml_root = ET.fromstring(r[1] if r[1] else f'<news id="{r[0]}"><title>{html.escape(r[2])}</title></news>')
                    results.append({
                        'id': r[0],
                        'xml': r[1],
                        'title': r[2],
                        'score': r[4],
                        'time': r[3]
                    })
                except:
                    results.append({
                        'id': r[0],
                        'xml': r[1],
                        'title': r[2],
                        'score': r[4],
                        'time': r[3]
                    })
            
            return results, len(results)
    
    def generate_sru_response(self, query, results, start=1, total=None):
        """生成SRU标准XML响应"""
        if total is None:
            total = len(results)
        
        root = ET.Element("searchRetrieveResponse")
        ET.SubElement(root, "version").text = "1.1"
        ET.SubElement(root, "numberOfRecords").text = str(total)
        
        records = ET.SubElement(root, "records")
        for idx, r in enumerate(results, start):
            record = ET.SubElement(records, "record")
            ET.SubElement(record, "recordSchema").text = "news"
            ET.SubElement(record, "recordPacking").text = "xml"
            ET.SubElement(record, "recordPosition").text = str(idx)
            
            rec_data = ET.SubElement(record, "recordData")
            if r['xml']:
                try:
                    # 嵌入预存XML
                    elem = ET.fromstring(r['xml'])
                    rec_data.append(elem)
                except:
                    ET.SubElement(rec_data, "news").text = r['title']
            else:
                ET.SubElement(rec_data, "news").text = r['title']
        
        # 回显查询
        echo = ET.SubElement(root, "echoedSearchRetrieveRequest")
        ET.SubElement(echo, "query").text = query
        
        return ET.tostring(root, encoding='unicode', method='xml')

engine_search = XMLSearchEngine()

@app.route('/sru', methods=['GET'])
def sru_search():
    """
    SRU协议检索端点
    参数：
    - query: 查询词（支持title:xxx, content:xxx限定）
    - start: 起始位置
    - maximumRecords: 每页数量（最大50）
    - language: 强制语言（zh/en，可选）
    """
    query = request.args.get('query', '').strip()
    start = int(request.args.get('start', 1))
    max_records = min(int(request.args.get('maximumRecords', 20)), 50)
    
    if not query:
        return Response(
            '<error>Query parameter is required</error>',
            mimetype='application/xml',
            status=400
        )
    
    results, total = engine_search.search(query, max_records, start-1)
    xml_resp = engine_search.generate_sru_response(query, results, start, total)
    
    return Response(xml_resp, mimetype='application/xml; charset=utf-8')

@app.route('/sru/explain', methods=['GET'])
def sru_explain():
    """SRU协议说明"""
    explain = """<?xml version="1.0"?>
    <explainResponse>
        <serverInfo>
            <host>oracle-cloud-vm</host>
            <port>5000</port>
            <database>quicknews_maindb</database>
        </serverInfo>
        <indexInfo>
            <index><title>Title</title><map>title</map></index>
            <index><title>Content</title><map>content</map></index>
            <index><title>Country</title><map>country</map></index>
        </indexInfo>
        <configInfo>
            <supports>Boolean AND</supports>
            <supports>Fielded search (title:, content:, country:)</supports>
            <supports>Chinese n-gram</supports>
            <supports>English stemmed words</supports>
        </configInfo>
    </explainResponse>"""
    return Response(explain, mimetype='application/xml')

@app.route('/health', methods=['GET'])
def health():
    """健康检查"""
    try:
        conn = engine.connect()
        conn.execute(text("SELECT 1"))
        conn.close()
        return {'status': 'ok', 'database': 'connected'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}, 500


# ==================== 新增 API 端点 ====================

@app.route('/api/stats/countries', methods=['GET'])
def get_country_stats():
    """
    获取近48小时内各国新闻数量统计（包含所有关联国家）
    返回格式: {"CN": 45, "US": 38, "JP": 25, ...}
    """
    try:
        with engine.connect() as conn:
            # 限制 is_primary = TRUE
            result = conn.execute(text("""
                SELECT 
                    nc.country_code,
                    COUNT(DISTINCT nc.news_id) as news_count
                FROM news_countries nc
                JOIN news n ON nc.news_id = n.news_id
                WHERE n.created_at > DATE_SUB(NOW(), INTERVAL 48 HOUR)
                  AND nc.is_primary = TRUE        -- ← 只统计主要关联国
                GROUP BY nc.country_code
                ORDER BY news_count DESC
            """))
            
            stats = {}
            for row in result.fetchall():
                country_code = row[0]
                count = row[1]
                if country_code:
                    stats[country_code] = count
            
            return jsonify(stats)
    except Exception as e:
        print(f"[API Error] get_country_stats: {e}")
        return jsonify({"error": str(e)}), 500


# ==================== 停用词表 ====================

# 中文停用词表（扩展版）
ZH_STOPWORDS = {
    # 基础停用词
    '的', '了', '和', '是', '在', '我', '有', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '看', '好', '自己', '这', '那', '之', '与', '及', '或', '但', '而', '因为', '所以', '因此', '如果', '虽然', '由', '被', '把', '给', '让', '向', '从', '为', '对', '关于', '通过', '作为', '进行', '表示', '认为', '已经', '开始', '目前', '今年', '去年', '正在', '成为', '需要', '可以', '没有', '以及', '随着', '根据', '由于', '但是', '并且', '同时', '其中', '其他', '相关',
    # 扩展停用词
    '一些', '这些', '那些', '问题', '方面', '情况', '工作', '发展', '建设', '政府', '国家', '地区', '国际', '世界', '报道', '记者', '消息', '来源', '图片', '视频', '时间', '日期', '时候', '今天', '明天', '昨天', '此时', '此前', '之后', '后来', '近日', '日前', '目前', '现在', '当时', '当场', '即将', '将要', '曾经', '一度', '一直', '不断', '逐渐', '进一步', '继续', '持续', '保持', '加强', '推进', '推动', '促进', '提高', '提升', '增强', '扩大', '深化', '完善', '落实', '实现', '确保', '坚持', '维护', '保障', '服务', '管理', '监督', '检查', '调查', '研究', '分析', '总结', '介绍', '说明', '指出', '强调', '提出', '呼吁', '宣布', '发布', '签署', '达成', '举行', '召开', '访问', '会见', '会谈', '协商', '合作', '交流', '互动', '联系', '沟通', '协调', '配合', '支持', '帮助', '协助', '参与', '参加', '加入', '入选', '荣获', '获得', '取得', '完成', '结束', '启动', '开幕', '闭幕', '举办', '开展', '组织', '策划', '实施', '执行', '制定', '修订', '修改', '调整', '改革', '创新', '探索', '尝试', '努力', '奋斗', '争取', '期待', '希望', '愿望', '目标', '目的', '意义', '价值', '作用', '影响', '效果', '成果', '成绩', '业绩', '表现', '状态', '形势', '趋势', '走向', '格局', '环境', '条件', '基础', '平台', '机制', '体系', '结构', '模式', '方式', '方法', '途径', '渠道', '手段', '措施', '办法', '策略', '战略', '规划', '计划', '方案', '议程', '日程', '安排', '部署', '配置', '设置', '规定', '规则', '制度', '政策', '法律', '法规', '条例', '标准', '规范', '准则', '原则', '要求', '条件', '资格', '能力', '水平', '质量', '品质', '效率', '速度', '进度', '节奏', '规模', '范围', '领域', '行业', '产业', '市场', '企业', '公司', '机构', '单位', '部门', '团队', '组织', '群体', '个人', '人士', '专家', '学者', '官员', '领导', '代表', '成员', '群众', '公众', '市民', '居民', '游客', '观众', '读者', '用户', '客户', '消费者', '投资者', '创业者', '从业者', '劳动者', '员工', '职员', '干部', '党员', '团员', '队员', '选手', '运动员', '演员', '歌手', '作家', '艺术家', '科学家', '工程师', '医生', '护士', '教师', '学生', '儿童', '青年', '少年', '老年', '妇女', '男性', '女性', '朋友', '家人', '亲属', '同事', '同学', '同胞', '同志', '伙伴', '盟友', '对手', '敌人', '竞争者', '邻居', '市民', '国民', '公民', '人类', '人口', '人们', '人才', '人物', '人员', '人力', '人手', '人头', '人群', '人体', '人心', '人性', '人生', '人士', '人间', '人世', '人事', '人工', '人才', '人口',
    # 数字相关
    '一', '二', '三', '四', '五', '六', '七', '八', '九', '十', '百', '千', '万', '亿',
    # 时间相关
    '年', '月', '日', '时', '分', '秒', '周', '星期', '季度',
}

# 英文停用词表（扩展版）
EN_STOPWORDS = {
    'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i', 'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at', 'this', 'but', 'his', 'by', 'from', 'they', 'we', 'say', 'her', 'she', 'or', 'an', 'will', 'my', 'one', 'all', 'would', 'there', 'their', 'what', 'so', 'up', 'out', 'if', 'about', 'who', 'get', 'which', 'go', 'me', 'when', 'make', 'can', 'like', 'time', 'no', 'just', 'him', 'know', 'take', 'people', 'into', 'year', 'your', 'good', 'some', 'could', 'them', 'see', 'other', 'than', 'then', 'now', 'look', 'only', 'come', 'its', 'over', 'think', 'also', 'back', 'after', 'use', 'two', 'how', 'our', 'work', 'first', 'well', 'way', 'even', 'new', 'want', 'because', 'any', 'these', 'give', 'day', 'most', 'us', 'is', 'was', 'are', 'were', 'been', 'has', 'had', 'did', 'does', 'doing', 'done', 'said', 'says', 'saying', 'made', 'making', 'came', 'coming', 'went', 'gone', 'got', 'getting', 'saw', 'seen', 'knew', 'known', 'thinking', 'thought', 'took', 'taken', 'told', 'asking', 'asked', 'working', 'worked', 'felt', 'trying', 'tried', 'left', 'leaving', 'called', 'calling', 'needed', 'needing', 'became', 'become', 'meaning', 'meant', 'kept', 'keeping', 'letting', 'putting', 'bringing', 'brought', 'began', 'begun', 'helped', 'helping', 'showed', 'shown', 'heard', 'hearing', 'played', 'playing', 'ran', 'run', 'running', 'moved', 'moving', 'lived', 'living', 'believed', 'believing', 'held', 'holding', 'happened', 'happening', 'stood', 'standing', 'lost', 'losing', 'paid', 'paying', 'met', 'meeting', 'included', 'including', 'continued', 'continuing', 'learned', 'learnt', 'learning', 'changed', 'changing', 'led', 'leading', 'understood', 'understanding', 'watched', 'watching', 'followed', 'following', 'stopped', 'stopping', 'created', 'creating', 'spoke', 'spoken', 'speaking', 'read', 'reading', 'allowed', 'allowing', 'added', 'adding', 'spent', 'spending', 'grew', 'grown', 'growing', 'opened', 'opening', 'walked', 'walking', 'offered', 'offering', 'remembered', 'remembering', 'loved', 'loving', 'considered', 'considering', 'appeared', 'appearing', 'bought', 'buying', 'waited', 'waiting', 'served', 'serving', 'died', 'dying', 'sent', 'sending', 'expected', 'expecting', 'built', 'building', 'stayed', 'staying', 'fell', 'fallen', 'falling', 'cut', 'cutting', 'reached', 'reaching', 'killed', 'killing', 'remained', 'remaining', 'suggested', 'suggesting', 'raised', 'raising', 'passed', 'passing', 'sold', 'selling', 'required', 'requiring', 'reported', 'reporting', 'decided', 'deciding', 'pulled', 'pulling',
}


@app.route('/api/stats/topics', methods=['GET'])
def get_hot_topics():
    """
    获取近48小时内的热门话题 TOP 10
    返回格式: [{"name": "人工智能", "count": 156}, {"name": "气候变化", "count": 132}, ...]
    """
    try:
        with engine.connect() as conn:
            # 获取近48小时的新闻标题
            result = conn.execute(text("""
                SELECT 
                    n.news_id,
                    n.title,
                    n.language
                FROM news n
                WHERE n.created_at > DATE_SUB(NOW(), INTERVAL 48 HOUR)
                ORDER BY n.created_at DESC
                LIMIT 500
            """))
            
            rows = result.fetchall()
            
            # 从标题中提取 n-gram
            ngram_counts = {}
            
            for row in rows:
                news_id = row[0]
                title = row[1] or ''
                lang = row[2] or 'zh'
                
                if lang == 'zh':
                    # 中文：提取 3-gram 和 4-gram
                    chars = [c for c in title if '\u4e00' <= c <= '\u9fff']
                    
                    # 3-gram
                    for i in range(len(chars) - 2):
                        ngram = chars[i] + chars[i+1] + chars[i+2]
                        # 过滤包含停用词的 n-gram
                        if not any(c in ZH_STOPWORDS for c in ngram):
                            if ngram not in ngram_counts:
                                ngram_counts[ngram] = {'count': 0, 'news_ids': set()}
                            ngram_counts[ngram]['news_ids'].add(news_id)
                    
                    # 4-gram
                    for i in range(len(chars) - 3):
                        ngram = chars[i] + chars[i+1] + chars[i+2] + chars[i+3]
                        if not any(c in ZH_STOPWORDS for c in ngram):
                            if ngram not in ngram_counts:
                                ngram_counts[ngram] = {'count': 0, 'news_ids': set()}
                            ngram_counts[ngram]['news_ids'].add(news_id)
                else:
                    # 英文：提取 2-gram 和 3-gram（词级别）
                    words = re.findall(r'\b[a-zA-Z]+\b', title.lower())
                    words = [w for w in words if len(w) >= 3 and w not in EN_STOPWORDS]
                    
                    # 2-gram
                    for i in range(len(words) - 1):
                        ngram = words[i] + ' ' + words[i+1]
                        if ngram not in ngram_counts:
                            ngram_counts[ngram] = {'count': 0, 'news_ids': set()}
                        ngram_counts[ngram]['news_ids'].add(news_id)
                    
                    # 3-gram
                    for i in range(len(words) - 2):
                        ngram = words[i] + ' ' + words[i+1] + ' ' + words[i+2]
                        if ngram not in ngram_counts:
                            ngram_counts[ngram] = {'count': 0, 'news_ids': set()}
                        ngram_counts[ngram]['news_ids'].add(news_id)
            
            # 获取国家名称列表用于过滤
            country_result = conn.execute(text("""
                SELECT country_code, country_name, country_name_en 
                FROM countries
            """))
            country_names = set()
            country_codes = set()
            for row in country_result.fetchall():
                country_codes.add(row[0].lower())
                if row[1]:
                    country_names.add(row[1])
                if row[2]:
                    country_names.add(row[2].lower())
            
            # 过滤并计算 doc_freq
            filtered_topics = []
            for ngram, data in ngram_counts.items():
                # 过滤条件
                if len(ngram) < 3:  # 长度过滤
                    continue
                if ngram.isdigit():  # 纯数字
                    continue
                if re.match(r'^\d+年$|^\d+月$|^\d+日$', ngram):  # 日期格式
                    continue
                if ngram.lower() in country_codes or ngram in country_names:  # 国家名
                    continue
                
                doc_freq = len(data['news_ids'])
                if doc_freq >= 2:  # 至少出现在2条新闻中
                    filtered_topics.append({
                        'name': ngram,
                        'count': doc_freq
                    })
            
            # 按出现频率排序，取前10
            filtered_topics.sort(key=lambda x: x['count'], reverse=True)
            top_topics = filtered_topics[:10]
            
            # 如果没有足够的中文话题，回退到英文
            if len(top_topics) < 5:
                # 补充英文话题
                en_result = conn.execute(text("""
                    SELECT 
                        n.news_id,
                        n.title
                    FROM news n
                    WHERE n.created_at > DATE_SUB(NOW(), INTERVAL 48 HOUR)
                      AND n.language = 'en'
                    ORDER BY n.created_at DESC
                    LIMIT 200
                """))
                
                for row in en_result.fetchall():
                    title = row[1] or ''
                    words = re.findall(r'\b[a-zA-Z]+\b', title.lower())
                    words = [w for w in words if len(w) >= 4 and w not in EN_STOPWORDS]
                    
                    for i in range(len(words) - 1):
                        ngram = words[i] + ' ' + words[i+1]
                        if ngram not in ngram_counts:
                            # 检查是否已存在
                            exists = False
                            for topic in top_topics:
                                if topic['name'].lower() == ngram.lower():
                                    exists = True
                                    break
                            if not exists and len(ngram) >= 4:
                                # 简单计数
                                pass
            
            return jsonify(top_topics)
    except Exception as e:
        print(f"[API Error] get_hot_topics: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


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
                    "type": source_type
                })
            
            return jsonify(sources)
    except Exception as e:
        print(f"[API Error] get_sources: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/categories', methods=['GET'])
def get_categories():
    """
    获取所有新闻分类
    返回格式: [{"category_id": 1, "category_name": "科技", "category_code": "tech", "color_code": "#3498db"}, ...]
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT 
                    category_id,
                    category_name,
                    category_code,
                    color_code
                FROM categories
                ORDER BY sort_order ASC
            """))
            
            categories = []
            for row in result.fetchall():
                categories.append({
                    "category_id": row[0],
                    "category_name": row[1],
                    "category_code": row[2],
                    "color_code": row[3]
                })
            
            return jsonify(categories)
    except Exception as e:
        print(f"[API Error] get_categories: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/news/category/<category_code>', methods=['GET'])
def get_news_by_category(category_code):
    """
    获取指定分类下的最新新闻
    返回格式: [{"id": 123, "title": "...", "summary": "...", "time": "...", "country": "CN"}, ...]
    """
    try:
        with engine.connect() as conn:
            # 获取分类ID
            cat_result = conn.execute(
                text("SELECT category_id FROM categories WHERE category_code = :code"),
                {'code': category_code}
            ).fetchone()
            
            if not cat_result:
                return jsonify({"error": "Category not found"}), 404
            
            category_id = cat_result[0]
            
            # 获取该分类下的新闻
            result = conn.execute(text("""
                SELECT 
                    n.news_id,
                    n.title,
                    n.summary,
                    n.created_at,
                    nc.country_code
                FROM news n
                JOIN news_categories ncat ON n.news_id = ncat.news_id
                LEFT JOIN news_countries nc ON n.news_id = nc.news_id AND nc.is_primary = TRUE
                WHERE ncat.category_id = :category_id
                  AND n.created_at > DATE_SUB(NOW(), INTERVAL 48 HOUR)
                ORDER BY n.created_at DESC
                LIMIT 20
            """), {'category_id': category_id})
            
            news_list = []
            for row in result.fetchall():
                news_list.append({
                    "id": row[0],
                    "title": row[1],
                    "summary": (row[2][:200] + '...') if row[2] and len(row[2]) > 200 else (row[2] or ''),
                    "time": row[3].strftime('%Y-%m-%d %H:%M:%S') if row[3] else None,
                    "country": row[4] or ''
                })
            
            return jsonify(news_list)
    except Exception as e:
        print(f"[API Error] get_news_by_category: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/news/<int:news_id>', methods=['GET'])
def get_news_detail(news_id):
    """
    获取单条新闻详情（含图片、视频）
    返回格式: {
        "id": 123,
        "title": "新闻标题",
        "summary": "摘要",
        "content": "正文内容",
        "published_at": "2024-01-15 10:30:00",
        "source_name": "新华网",
        "source_url": "http://...",
        "country_code": "CN",
        "country_name": "中国",
        "images": [{"url": "...", "caption": "..."}],
        "videos": [{"url": "...", "type": "mp4"}]
    }
    """
    try:
        with engine.connect() as conn:
            # 获取新闻基本信息
            news_result = conn.execute(text("""
                SELECT 
                    n.news_id,
                    n.title,
                    n.summary,
                    n.content,
                    n.published_at,
                    n.source_url,
                    s.source_name,
                    nc.country_code,
                    c.country_name
                FROM news n
                LEFT JOIN sources s ON n.source_id = s.source_id
                LEFT JOIN news_countries nc ON n.news_id = nc.news_id AND nc.is_primary = TRUE
                LEFT JOIN countries c ON nc.country_code = c.country_code
                WHERE n.news_id = :news_id
                LIMIT 1
            """), {'news_id': news_id})
            
            row = news_result.fetchone()
            if not row:
                return jsonify({"error": "News not found"}), 404
            
            # 构建新闻数据
            news_data = {
                "id": row[0],
                "title": row[1],
                "summary": row[2],
                "content": row[3] or row[2] or "",
                "published_at": row[4].strftime('%Y-%m-%d %H:%M:%S') if row[4] else None,
                "source_url": row[5],
                "source_name": row[6] or "未知来源",
                "country_code": row[7],
                "country_name": row[8]
            }
            
            # 获取图片
            images_result = conn.execute(text("""
                SELECT media_url, is_cover, width, height
                FROM media
                WHERE news_id = :news_id AND media_type = 'image'
                ORDER BY is_cover DESC, media_id ASC
            """), {'news_id': news_id})
            
            images = []
            for img_row in images_result.fetchall():
                images.append({
                    "url": img_row[0],
                    "is_cover": bool(img_row[1]),
                    "width": img_row[2],
                    "height": img_row[3]
                })
            news_data["images"] = images
            
            # 获取视频
            videos_result = conn.execute(text("""
                SELECT media_url, media_type
                FROM media
                WHERE news_id = :news_id AND media_type = 'video'
                ORDER BY media_id ASC
            """), {'news_id': news_id})
            
            videos = []
            for vid_row in videos_result.fetchall():
                url = vid_row[0]
                # 判断视频类型
                video_type = "mp4"
                if '.m3u8' in url.lower():
                    video_type = "hls"
                elif 'youtube' in url.lower() or 'youtu.be' in url.lower():
                    video_type = "youtube"
                elif 'bilibili' in url.lower():
                    video_type = "bilibili"
                elif 'player' in url.lower() or 'embed' in url.lower():
                    video_type = "embed"
                
                videos.append({
                    "url": url,
                    "type": video_type
                })
            news_data["videos"] = videos
            
            return jsonify(news_data)
    except Exception as e:
        print(f"[API Error] get_news_detail: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


def create_app():
    """创建 Flask 应用实例（供外部调用）"""
    return app


if __name__ == '__main__':
    # 生产环境使用gunicorn: gunicorn -w 4 -b 0.0.0.0:5000 xml_api:app
    app.run(host='0.0.0.0', port=5000, threaded=True, debug=False)

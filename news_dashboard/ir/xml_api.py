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
    
        return terms, lang, xpath_filter, clean_query
    
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
        
        terms, lang, xpath, clean_query = self.parse_query(query_str)
    
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
    
        # title查询回退到LIKE匹配，避免bigram索引无法命中jieba热点短语
        if xpath == '/news/title':
            if not clean_query:
                return [], 0
            
            def _build_results(rows):
                results = []
                for r in rows:
                    try:
                        xml_root = ET.fromstring(r[1] if r[1] else f'<news id="{r[0]}"><title>{html.escape(r[2])}</title></news>')
                        results.append({'id': r[0], 'xml': r[1], 'title': r[2], 'score': r[4], 'time': r[3]})
                    except:
                        results.append({'id': r[0], 'xml': r[1], 'title': r[2], 'score': r[4], 'time': r[3]})
                return results
            
            safe_pattern = clean_query.replace('%', '\\%').replace('_', '\\_')
            sql = text("""
                SELECT n.news_id, n.xml_content, n.title, n.created_at, 2.0 as score, 1 as match_count
                FROM news n
                WHERE n.title LIKE :pattern
                  AND n.created_at > DATE_SUB(NOW(), INTERVAL 48 HOUR)
                ORDER BY n.created_at DESC
                LIMIT :limit OFFSET :offset
            """)
            with self.engine.connect() as conn:
                rows = conn.execute(sql, {'pattern': f'%{safe_pattern}%', 'limit': max_results, 'offset': offset}).fetchall()
                results = _build_results(rows)
                if results:
                    return results, len(results)
            
            # 兜底：拆成关键词用 AND LIKE 搜索（兼容jieba空格丢失、merge超长词等情况）
            keywords = [k for k in re.split(r'[^a-zA-Z0-9\u4e00-\u9fff]+', clean_query) if len(k) >= 2]
            if keywords:
                like_clauses = ' AND '.join([f"n.title LIKE :p{i}" for i in range(len(keywords))])
                sql_fallback = text(f"""
                    SELECT n.news_id, n.xml_content, n.title, n.created_at, 1.5 as score, 1 as match_count
                    FROM news n
                    WHERE {like_clauses}
                      AND n.created_at > DATE_SUB(NOW(), INTERVAL 48 HOUR)
                    ORDER BY n.created_at DESC
                    LIMIT :limit OFFSET :offset
                """)
                params = {f'p{i}': f'%{kw.replace("%", "\\%").replace("_", "\\_")}%' for i, kw in enumerate(keywords)}
                params.update({'limit': max_results, 'offset': offset})
                with self.engine.connect() as conn:
                    rows = conn.execute(sql_fallback, params).fetchall()
                    results = _build_results(rows)
                    return results, len(results)
            
            return [], 0
    
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
            
            # 添加时间戳（供前端展示）
            if r.get('time'):
                time_val = r['time']
                if hasattr(time_val, 'strftime'):
                    time_str = time_val.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    time_str = str(time_val)
                datestamp = ET.SubElement(record, "datestamp")
                datestamp.text = time_str
            
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
                  AND nc.is_primary = TRUE        -- 只统计主要关联国
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
    # 【新增】财经术语停用词（避免破碎词组）
    '同比', '环比', '增长', '下降', '上升', '减少', '增加', '涨幅', '跌幅', '百分点',
    '净利润', '归母', '归母净', '母净利', '归母利润', '母净利润', '利润总', '利润总额',
    '营业', '营业收', '业收入', '营业收', '营收', '成本', '费用', '资产', '负债',
    '股东', '权益', '每股', '收益', '现金流', '流动', '非流动', '负债率',
    '毛利率', '净利率', '收益率', '回报率', '市盈率', '市净率',
}

# 中文精简停用词表（用于jieba分词后过滤虚词）
ZH_STOPWORDS_SMALL = {
    '的', '了', '和', '是', '在', '我', '有', '不', '人', '都', '也', '很', '到', '说', '要', '去', '你', '会', '着', '看', '好', '自己',
    '这', '那', '这些', '那些', '这个', '那个', '之', '与', '及', '或', '但', '而', '因为', '所以', '因此', '如果', '即使', '虽然', '尽管',
    '由', '被', '把', '给', '让', '向', '往', '自', '从', '到', '对', '关于', '对于', '为了', '通过', '作为', '随着', '根据', '由于', '但是',
    '并且', '同时', '其中', '其他', '相关', '一个', '一些', '此时', '此前', '之后', '后来', '近日', '日前', '目前', '现在', '当时', '当场',
    '即将', '将要', '曾经', '一度', '一直', '不断', '逐渐', '进一步', '继续', '持续', '保持', '进行', '表示', '认为', '已经', '开始',
    '今年', '去年', '正在', '成为', '需要', '可以', '没有', '年', '月', '日', '时', '分', '秒',
    '一', '二', '三', '四', '五', '六', '七', '八', '九', '十',
    '们', '它', '他', '她', '地', '得', '下', '上', '中', '里', '内', '外', '间', '边', '面', '头', '部', '家', '个', '种', '类',
    '第', '每', '各', '整', '等', '多', '大', '小', '高', '低', '长', '短', '来', '出', '起', '过', '回', '开', '放', '做', '打', '吃', '走', '跑',
}

# 英文停用词表（扩展版）
EN_STOPWORDS = {
    'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i', 'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at', 'this', 'but', 'his', 'by', 'from', 'they', 'we', 'say', 'her', 'she', 'or', 'an', 'will', 'my', 'one', 'all', 'would', 'there', 'their', 'what', 'so', 'up', 'out', 'if', 'about', 'who', 'get', 'which', 'go', 'me', 'when', 'make', 'can', 'like', 'time', 'no', 'just', 'him', 'know', 'take', 'people', 'into', 'year', 'your', 'good', 'some', 'could', 'them', 'see', 'other', 'than', 'then', 'now', 'look', 'only', 'come', 'its', 'over', 'think', 'also', 'back', 'after', 'use', 'two', 'how', 'our', 'work', 'first', 'well', 'way', 'even', 'new', 'want', 'because', 'any', 'these', 'give', 'day', 'most', 'us', 'is', 'was', 'are', 'were', 'been', 'has', 'had', 'did', 'does', 'doing', 'done',
}

# 【新增】财经术语模式（用于过滤破碎词组）
FINANCIAL_PATTERNS = [
    r'归母净利润',
    r'同比增长',
    r'环比下降',
    r'营业收入',
    r'净利润率',
    r'毛利率',
    r'资产负债',
    r'现金流',
    r'每股收益',
    r'市盈率',
    r'市净率',
    r'收益率',
    r'回报率',
    r'百分点',
    r'营收增长',
    r'利润增长',
    r'业绩增长',
]

# 【新增】无意义短词模式（需要过滤）
MEANLESS_PATTERNS = [
    r'^[母归归母母净净利利润润母净归母归母净归母利润母净利润]+$',  # 破碎的财务词
    r'^[同比比增增长长同比增比增长]+$',  # 破碎的增长词
    r'^..$',  # 只有2个字符
    r'^第[一二三四五六七八九十]+$',  # "第一", "第二"等
    r'^[上下左右前后内外]+$',  # 纯方位词
]


def is_meaningless_phrase(phrase):
    """
    判断一个词组是否无意义（破碎词组或常见术语）
    仅对完全匹配的破碎词进行过滤，避免子串误杀正常短语
    """
    # 检查是否是破碎的财务术语（精确匹配）
    fragmented_terms = ['归母净', '母净利', '归母利', '母净利润', '同比增', '比增长', '环比增']
    for term in fragmented_terms:
        if phrase == term:
            if phrase not in ['归母净利润', '同比增长', '环比下降', '营业收入']:
                return True
    
    # 检查是否匹配无意义模式
    for pattern in MEANLESS_PATTERNS:
        if re.match(pattern, phrase):
            return True
    
    return False


def _lcs_length(a, b):
    """求两个字符串的最长公共连续子串长度"""
    m, n = len(a), len(b)
    if m == 0 or n == 0:
        return 0
    max_len = 0
    # 只需要一维DP
    dp = [0] * (n + 1)
    for i in range(1, m + 1):
        prev = 0
        for j in range(1, n + 1):
            temp = dp[j]
            if a[i-1] == b[j-1]:
                dp[j] = prev + 1
                max_len = max(max_len, dp[j])
            else:
                dp[j] = 0
            prev = temp
    return max_len


def merge_overlapping_ngrams(ngrams_with_scores):
    """
    合并重叠的n-gram，保留得分最高的短语。
    重叠判定：子串包含，或最长公共连续子串超过较短者的40%。
    """
    if not ngrams_with_scores:
        return []
    
    # 按得分降序，然后按长度降序
    sorted_ngrams = sorted(ngrams_with_scores, key=lambda x: (-x[1], -len(x[0])))
    
    merged = []
    
    for ngram, score, doc_freq in sorted_ngrams:
        is_overlapping = False
        for merged_ngram, _, _ in merged:
            # 1. 子串包含
            if ngram in merged_ngram or merged_ngram in ngram:
                is_overlapping = True
                break
            # 2. 最长公共连续子串过长
            lcs = _lcs_length(ngram, merged_ngram)
            shorter = min(len(ngram), len(merged_ngram))
            if shorter > 0 and lcs / shorter > 0.4:
                is_overlapping = True
                break
        
        if not is_overlapping and not is_meaningless_phrase(ngram):
            merged.append((ngram, score, doc_freq))
    
    return merged


def extract_meaningful_phrases(title, news_id, phrases_dict):
    """
    从中文标题中提取有意义的短语
    纯jieba分词后按连续块组合（停用词/单字/数字为界），保证产物是原始标题的连续子串。
    不再补充字符级n-gram，避免产生无意义碎片。
    """
    if not title:
        return
    
    # jieba未安装时降级为字符级4-gram
    if not _JIEBA_AVAILABLE:
        chars = [c for c in title if '\u4e00' <= c <= '\u9fff']
        if len(chars) < 4:
            return
        for n in range(6, 3, -1):
            for i in range(len(chars) - n + 1):
                phrase = ''.join(chars[i:i+n])
                if is_meaningless_phrase(phrase):
                    continue
                if phrase.isdigit():
                    continue
                if re.match(r'^\d+年$|^\d+月$|^\d+日$', phrase):
                    continue
                if phrase not in phrases_dict:
                    phrases_dict[phrase] = {'count': 0, 'news_ids': set(), 'length': n}
                phrases_dict[phrase]['news_ids'].add(news_id)
                phrases_dict[phrase]['count'] = len(phrases_dict[phrase]['news_ids'])
        return
    
    # jieba分词后按连续块组合，确保产物在原始标题中连续出现
    words = list(jieba.cut(title))
    chunks = []
    current_chunk = []
    for w in words:
        w = w.strip()
        if not w:
            continue
        if w.isdigit():
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = []
            continue
        if len(w) == 1 or w in ZH_STOPWORDS_SMALL or is_meaningless_phrase(w):
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = []
            continue
        current_chunk.append(w)
    if current_chunk:
        chunks.append(current_chunk)
    
    norm_title = re.sub(r'\s+', '', title)
    for chunk in chunks:
        if len(chunk) < 2:
            continue
        # 如果整个chunk全是纯英文单词，跳过（英文有专门管道）
        if all(re.match(r'^[a-zA-Z]+$', w) for w in chunk):
            continue
        
        def _join_sub(words):
            # 中英相邻时英文后加空格，中文相邻不加空格
            res = words[0]
            for w in words[1:]:
                if re.search(r'[a-zA-Z]$', res) and re.match(r'[a-zA-Z]', w):
                    res += ' ' + w
                else:
                    res += w
            return res
        
        for n in range(3, 1, -1):
            for i in range(len(chunk) - n + 1):
                phrase = _join_sub(chunk[i:i+n])
                if len(phrase) < 4:
                    continue
                # 验证去掉空格后确实是原始标题的子串
                if re.sub(r'\s+', '', phrase) not in norm_title:
                    continue
                if phrase not in phrases_dict:
                    phrases_dict[phrase] = {'count': 0, 'news_ids': set(), 'length': n}
                phrases_dict[phrase]['news_ids'].add(news_id)
                phrases_dict[phrase]['count'] = len(phrases_dict[phrase]['news_ids'])


def extract_en_phrases(title, news_id, phrases_dict):
    """从英文标题中提取2-gram和3-gram，并验证为原始标题的连续子串"""
    lower_title = title.lower()
    words = re.findall(r'\b[a-zA-Z]+\b', lower_title)
    words = [w for w in words if len(w) >= 3 and w not in EN_STOPWORDS]
    
    for i in range(len(words) - 1):
        phrase = words[i] + ' ' + words[i+1]
        if len(phrase) < 4 or phrase not in lower_title:
            continue
        if phrase not in phrases_dict:
            phrases_dict[phrase] = {'count': 0, 'news_ids': set(), 'length': 2}
        phrases_dict[phrase]['news_ids'].add(news_id)
        phrases_dict[phrase]['count'] = len(phrases_dict[phrase]['news_ids'])
    
    for i in range(len(words) - 2):
        phrase = words[i] + ' ' + words[i+1] + ' ' + words[i+2]
        if len(phrase) < 4 or phrase not in lower_title:
            continue
        if phrase not in phrases_dict:
            phrases_dict[phrase] = {'count': 0, 'news_ids': set(), 'length': 3}
        phrases_dict[phrase]['news_ids'].add(news_id)
        phrases_dict[phrase]['count'] = len(phrases_dict[phrase]['news_ids'])


@app.route('/api/stats/topics', methods=['GET'])
def get_hot_topics():
    """
    获取近48小时内的热门话题 TOP 10
    中英文分开统计后合并，避免英文被中文挤出
    中文使用jieba分词，英文使用2-gram/3-gram
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT n.news_id, n.title, n.language
                FROM news n
                WHERE n.created_at > DATE_SUB(NOW(), INTERVAL 48 HOUR)
                ORDER BY n.created_at DESC
                LIMIT 500
            """))
            rows = result.fetchall()
            
            zh_phrases = {}
            en_phrases = {}
            
            for row in rows:
                news_id = row[0]
                title = row[1] or ''
                lang = row[2] or 'zh'
                
                if lang == 'zh':
                    extract_meaningful_phrases(title, news_id, zh_phrases)
                else:
                    extract_en_phrases(title, news_id, en_phrases)
            
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
            
            def build_topics(phrases, min_freq):
                ngrams = []
                for phrase, data in phrases.items():
                    doc_freq = data['count']
                    length = data['length']
                    if len(phrase) < 4:
                        continue
                    if phrase.isdigit():
                        continue
                    if re.match(r'^\d+年$|^\d+月$|^\d+日$', phrase):
                        continue
                    if phrase.lower() in country_codes or phrase in country_names:
                        continue
                    if is_meaningless_phrase(phrase):
                        continue
                    # 过滤纯英文无空格黏合词（如 oppositiongroupmembers）
                    if re.fullmatch(r'[a-zA-Z]+', phrase) and len(phrase) > 10:
                        continue
                    score = doc_freq * (1 + 0.2 * length)
                    if doc_freq >= min_freq:
                        ngrams.append((phrase, score, doc_freq))
                merged = merge_overlapping_ngrams(ngrams)
                merged.sort(key=lambda x: x[1], reverse=True)
                return merged
            
            zh_topics = build_topics(zh_phrases, 1)  # 中文门槛降到1，jieba长词重复率低
            en_topics = build_topics(en_phrases, 1)  # 英文门槛保持1
            
            # 合并策略：中文优先，确保至少6个中文席位
            top_topics = []
            for phrase, score, count in zh_topics[:6]:
                top_topics.append({'name': phrase, 'count': count})
            for phrase, score, count in en_topics[:10 - len(top_topics)]:
                top_topics.append({'name': phrase, 'count': count})
            # 若英文不足，再用中文补
            for phrase, score, count in zh_topics[6:10 - len(top_topics)]:
                top_topics.append({'name': phrase, 'count': count})
            
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


# 前端路由 - 所有非 API 请求都返回 index.html（支持 React Router）
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    """服务前端静态文件"""
    # API 请求直接返回 404，让 Flask 处理
    if path.startswith('api/') or path.startswith('sru') or path == 'health':
        return jsonify({"error": "Not found"}), 404
    
    # 检查静态文件是否存在
    file_path = os.path.join(STATIC_DIR, path)
    if path and os.path.exists(file_path) and os.path.isfile(file_path):
        return send_from_directory(STATIC_DIR, path)
    
    # 否则返回 index.html（让 React Router 处理前端路由）
    index_path = os.path.join(STATIC_DIR, 'index.html')
    if os.path.exists(index_path):
        return send_from_directory(STATIC_DIR, 'index.html')
    
    # 如果没有静态文件，返回简单的 API 说明
    return jsonify({
        "status": "QuickNews API is running",
        "endpoints": {
            "health": "/health",
            "api": "/api/*",
            "sru": "/sru",
            "categories": "/api/categories",
            "country_stats": "/api/stats/countries",
            "hot_topics": "/api/stats/topics"
        }
    })


def create_app():
    """创建 Flask 应用实例（供外部调用）"""
    return app


if __name__ == '__main__':
    # 生产环境使用gunicorn: gunicorn -w 4 -b 0.0.0.0:5000 xml_api:app
    app.run(host='0.0.0.0', port=5000, threaded=True, debug=False)

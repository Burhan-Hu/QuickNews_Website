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

from core.stopwords import TOPIC_STOP_WORDS as STOP_WORDS

# 通用实体词降级（国家名、通用政治词汇等，在聚类中权重降低，不计入共享词数量）
COMMON_ENTITY_WORDS = {
    '美国', '中国', '伊朗', '俄罗斯', '乌克兰', '以色列', '朝鲜', '韩国', '日本',
    '英国', '法国', '德国', '印度', '巴基斯坦', '阿富汗', '叙利亚', '伊拉克',
    '土耳其', '埃及', '沙特', '阿联酋', '卡塔尔', '约旦', '黎巴嫩', '也门',
    '政府', '官员', '总统', '部长', '总理', '会谈', '谈判', '表示', '称', '说',
    '报道', '声明', '回应', '指出', '认为', '强调', '介绍', '国际', '国家', '地区',
    '城市', '人民', '军队', '军事', '政治', '经济', '社会', '文化', '科技', '外交',
    'trump', 'government', 'officials', 'president', 'minister', 'prime',
    'talks', 'negotiations', 'said', 'says', 'reported', 'according', 'statement',
    'response', 'meeting', 'conference', 'summit', 'leader', 'leaders', 'country',
    'countries', 'nation', 'nations', 'world', 'global', 'region', 'regional',
    'city', 'people', 'military', 'army', 'political', 'economic', 'official',
}

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
        """执行SRU搜索（XML检索增强版）- 兼容前端 news 格式"""
        try:
            with self.engine.connect() as conn:
                records = []
                clean_query = (query or '').strip()
                
                if clean_query == '*':
                    # 返回最新新闻（按入库时间排序）
                    sql = """
                        SELECT 
                            n.news_id, n.title, n.summary, n.source_url,
                            n.created_at, n.language, n.has_video,
                            nc.country_code
                        FROM news n
                        LEFT JOIN news_countries nc ON n.news_id = nc.news_id AND nc.is_primary = 1
                        ORDER BY n.created_at DESC
                        LIMIT :limit OFFSET :offset
                    """
                    result = conn.execute(text(sql), {
                        'limit': min(maximum_records, 50),
                        'offset': max(0, start - 1)
                    })
                    for row in result.fetchall():
                        records.append({
                            'id': row[0],
                            'title': row[1] or '',
                            'summary': row[2] or '',
                            'url': row[3] or '',
                            'date': row[4].isoformat() if row[4] else '',
                            'language': row[5] or 'zh',
                            'has_video': bool(row[6]),
                            'country': row[7] or 'unknown'
                        })
                
                elif clean_query.lower().startswith('country:'):
                    # 按国家精确筛选
                    country_code = clean_query.split(':', 1)[1].strip().upper()
                    sql = """
                        SELECT 
                            n.news_id, n.title, n.summary, n.source_url,
                            n.created_at, n.language, n.has_video,
                            nc.country_code
                        FROM news n
                        JOIN news_countries nc ON n.news_id = nc.news_id
                        WHERE nc.country_code = :code
                        ORDER BY n.created_at DESC
                        LIMIT :limit OFFSET :offset
                    """
                    result = conn.execute(text(sql), {
                        'code': country_code,
                        'limit': min(maximum_records, 50),
                        'offset': max(0, start - 1)
                    })
                    for row in result.fetchall():
                        records.append({
                            'id': row[0],
                            'title': row[1] or '',
                            'summary': row[2] or '',
                            'url': row[3] or '',
                            'date': row[4].isoformat() if row[4] else '',
                            'language': row[5] or 'zh',
                            'has_video': bool(row[6]),
                            'country': row[7] or 'unknown'
                        })
                
                elif clean_query.lower().startswith('title:'):
                    # 按标题模糊搜索
                    title_query = clean_query.split(':', 1)[1].strip()
                    sql = """
                        SELECT 
                            n.news_id, n.title, n.summary, n.source_url,
                            n.created_at, n.language, n.has_video,
                            (SELECT country_code FROM news_countries 
                             WHERE news_id = n.news_id AND is_primary = 1 LIMIT 1) as country
                        FROM news n
                        WHERE n.title LIKE :q
                        ORDER BY n.created_at DESC
                        LIMIT :limit OFFSET :offset
                    """
                    result = conn.execute(text(sql), {
                        'q': f'%{title_query}%',
                        'limit': min(maximum_records, 50),
                        'offset': max(0, start - 1)
                    })
                    for row in result.fetchall():
                        records.append({
                            'id': row[0],
                            'title': row[1] or '',
                            'summary': row[2] or '',
                            'url': row[3] or '',
                            'date': row[4].isoformat() if row[4] else '',
                            'language': row[5] or 'zh',
                            'has_video': bool(row[6]),
                            'country': row[7] or 'unknown'
                        })
                
                else:
                    # 普通关键词搜索：使用 inverted_index
                    query_terms = self._tokenize_query(query)
                    if not query_terms:
                        return self._empty_response(query, start, maximum_records)
                    
                    term_list = query_terms[:5]
                    placeholders = ', '.join([f':t{i}' for i in range(len(term_list))])
                    
                    sql = f"""
                        SELECT 
                            n.news_id,
                            n.title,
                            n.summary,
                            n.source_url,
                            n.created_at,
                            n.language,
                            n.has_video,
                            (SELECT country_code FROM news_countries 
                             WHERE news_id = n.news_id AND is_primary = 1 LIMIT 1) as country,
                            SUM(ii.tf_weight) as score,
                            COUNT(DISTINCT ii.term) as match_count
                        FROM inverted_index ii
                        JOIN news n ON ii.news_id = n.news_id
                        WHERE ii.term IN ({placeholders})
                          AND ii.language = :lang
                          AND n.created_at > DATE_SUB(NOW(), INTERVAL 48 HOUR)
                        GROUP BY n.news_id
                        HAVING match_count >= :min_match
                        ORDER BY score DESC, n.created_at DESC
                        LIMIT :limit OFFSET :offset
                    """
                    
                    params = {f't{i}': t for i, t in enumerate(term_list)}
                    params.update({
                        'lang': 'zh' if any('\u4e00' <= c <= '\u9fff' for c in query) else 'en',
                        'min_match': max(1, len(term_list) * 0.5),
                        'limit': min(maximum_records, 50),
                        'offset': max(0, start - 1)
                    })
                    
                    result = conn.execute(text(sql), params)
                    
                    for row in result.fetchall():
                        records.append({
                            'id': row[0],
                            'title': row[1] or '',
                            'summary': row[2] or '',
                            'url': row[3] or '',
                            'date': row[4].isoformat() if row[4] else '',
                            'language': row[5] or 'zh',
                            'has_video': bool(row[6]),
                            'country': row[7] or 'unknown',
                            'score': row[8]
                        })
                
                return self._build_sru_response(query, start, maximum_records, len(records), records)
                
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
        """构建兼容前端的SRU XML响应（使用 <news> 格式）"""
        root = ET.Element('searchRetrieveResponse')
        
        ET.SubElement(root, 'version').text = '1.1'
        ET.SubElement(root, 'numberOfRecords').text = str(total)
        
        records_elem = ET.SubElement(root, 'records')
        
        for i, record in enumerate(records):
            record_elem = ET.SubElement(records_elem, 'record')
            ET.SubElement(record_elem, 'recordPosition').text = str(start + i)
            ET.SubElement(record_elem, 'datestamp').text = record.get('date', '')
            
            record_data = ET.SubElement(record_elem, 'recordData')
            
            # 构建兼容前端的 <news> 格式
            news = ET.SubElement(record_data, 'news', {'id': str(record.get('id', ''))})
            
            title_elem = ET.SubElement(news, 'title')
            title_elem.text = html.escape(record.get('title', ''))
            
            summary_elem = ET.SubElement(news, 'summary')
            summary_elem.text = html.escape(record.get('summary', '')[:300])
            
            metadata = ET.SubElement(news, 'metadata')
            ET.SubElement(metadata, 'country').text = record.get('country', 'unknown')
            
            if record.get('url'):
                ET.SubElement(news, 'url').text = record.get('url', '')
            if record.get('language'):
                ET.SubElement(news, 'language').text = record.get('language', 'zh')
            if record.get('has_video'):
                ET.SubElement(news, 'type').text = 'video'
        
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

# 强事件词表（正向激励）
EVENT_WORDS = {
    # 中文：冲突/军事/政治/外交/灾难/科技
    '战争', '冲突', '袭击', '突袭', '偷袭', '轰炸', '打击', '制裁', '禁运',
    '停火', '停战', '谈判', '和谈', '对话', '磋商', '协商', '斡旋',
    '协议', '条约', '协定', '草案', '备忘录', '共识', '宣言', '声明',
    '选举', '投票', '公投', '弹劾', '罢免', '辞职', '解职', '撤职',
    '访问', '会晤', '会谈', '接见', '拜会', '出访', '来访', '国事访问','会',
    '宣战', '入侵', '占领', '攻占', '失守', '沦陷', '解放', '收复',
    '撤离', '撤退', '撤军', '增兵', '派兵', '出兵', '驻军', '换俘',
    '维和', '斡旋', '调解', '调停', '仲裁', '裁决', '判决', '宣判',
    '政变', '兵变', '革命', '变革', '改革', '改制', '变法', '维新',
    '抗议', '示威', '游行', '集会', '请愿', '罢工', '罢课', '罢市',
    '暴动', '骚乱', '动乱', '战乱', '动荡', '混乱', '失序', '罢市',
    '枪击', '开火', '交火', '巷战', '近战', '夜战', '伏击', '围剿',
    '刺杀', '暗杀', '狙杀', '处决', '斩首', '绑架', '劫持', '勒索',
    '越狱', '逃狱', '劫狱', '走私', '贩毒', '洗钱', '诈骗', '贪腐',
    '地震', '海啸', '台风', '飓风', '龙卷风', '洪水', '洪涝', '干旱',
    '火灾', '火警', '塌方', '坍塌', '滑坡', '泥石流', '雪崩', '溃坝',
    '坠毁', '撞机', '空难', '海难', '沉船', '触礁', '搁浅', '相撞',
    '疫情', '瘟疫', '病毒', '流感', '传染', '爆发', '扩散', '蔓延',
    '疫苗', '接种', '解封', '解禁', '放开', '封锁', '隔离', '封控',
    '破产', '倒闭', '清算', '重组', '裁员', '减薪', '罢工', '并购',
    '收购', '兼并', '合并', '分拆', '上市', '退市', '停牌', '复牌',
    '发射', '升空', '起飞', '着陆', '降落', '对接', '交会', '返回',
    '探测', '勘测', '巡航', '巡视', '巡视', '航行', '试射', '演练',
    '卫星', '飞船', '火箭', '导弹', '核弹', '核武器', '原子', '氢弹',
    # 英文
    'war', 'conflict', 'attack', 'strikes', 'strike', 'bombing', 'bombings',
    'raid', 'raids', 'invasion', 'invasions', 'occupation', 'withdrawal',
    'retreat', 'sanctions', 'ceasefire', 'truce', 'negotiations', 'talks',
    'deal', 'deals', 'agreement', 'treaty', 'election', 'vote', 'voting',
    'impeachment', 'resignation', 'visit', 'summit', 'meeting', 'coup',
    'revolution', 'protest', 'protests', 'demonstration', 'demonstrations',
    'riot', 'riots', 'unrest', 'shooting', 'shootings', 'assassination',
    'kidnapping', 'hijacking', 'earthquake', 'tsunami', 'typhoon', 'flood',
    'fire', 'collapse', 'crash', 'crashes', 'sinking', 'pandemic', 'outbreak',
    'vaccine', 'lockdown', 'bankruptcy', 'layoff', 'layoffs', 'merger',
    'acquisition', 'launch', 'landing', 'missile', 'nuclear', 'test',
}

# 直接过滤的模板/属性短语黑名单
JUNK_PHRASES = {
    # 中文地震/气象模板
    '震源深度', '震级', '级地震', '余震', '北纬', '东经', 
    '地震震级', '地震深度', '地震烈度', '震中位置', '震中距',
    # 中文财经模板
    '收盘价', '开盘价', '市盈率', '市值','同比增长', '环比下降', '环比上涨', '同比下降', '同比增长率',
    '同比预增', '同比预降', '环比预增', '环比预降', '归母净利润', '一季度净利润', '一季度营收','暨', 
    # 通用报道模板
    '据报道', '消息称', '采访时表示', '对此表示', '会议指出', '会议强调',
    '会议指出', '会议强调', '会议指出', '会议要求', '会议认为','消息人士称'
    '发言人表示', '发言人称', '负责人称', '负责人表示','摄氏度', '降水量', '降水量毫米', '最高气温', '最低气温',
    # 英文泛领域词
    'social media', 'artificial intelligence', 'climate change',
    'stock market', 'interest rates', 'inflation rate', 'economic growth',
    'global economy', 'financial markets', 'exchange rate',
    # 纯属性词
    'population', 'birth rate','death toll', 'life expectancy', 'average temperature',
    # 英文时间模板
    'days ago', 'hours ago', 'weeks ago', 'months ago', 'years ago',
    'last week', 'last month', 'last year', 'this week', 'this month',
}

# 正则黑名单
JUNK_PHRASE_PATTERNS = [
    re.compile(r'^\d+级$'),           # 3级、5级
    re.compile(r'^\d+\.\d+级$'),     # 3.5级
    re.compile(r'^第?\d+名$'),        # 第一名、第3名
    re.compile(r'^\d+\.\d+$'),       # 纯数字如 3.5
    re.compile(r'^[一二三四五六七八九十百]+强$'),  # 百强、十强
    re.compile(r'^\d+年$'),           # 2024年
    re.compile(r'^\d+月$'),           # 5月
    re.compile(r'^\d+日$'),           # 12日
    re.compile(r'^\d+\s+(days?|hours?|weeks?|months?|years?)\s+ago$'),  # 3 days ago
]

def extract_hot_topics(news_list):
    """
    基于标题事件短语提取的热点话题生成（事件级改进版）
    - 强化事件性约束：必须有实体+动作/事件词
    - 引入事件性得分加权
    - 过滤模板词和纯实体短语
    返回话题列表（结构与旧版保持一致）
    """
    import math
    from collections import Counter
    
    if not news_list or len(news_list) < 2:
        return []
    
    # phrase 末尾垃圾动词（抽象方向 / 日常事务 / 言说表态）
    # 只拦截 phrase 末尾的这些动词，防止"中国共产党加强""国务院办理"类垃圾
    common_verbs = COMMON_ENTITY_WORDS | {
        # 抽象方向动词
        '发展', '推动', '促进', '加强', '推进', '提高', '提升', '增强', '扩大',
        '深化', '完善', '落实', '实现', '确保', '坚持', '维护', '保障', '服务',
        # 日常事务动词
        '管理', '监督', '检查', '调查', '研究', '分析','处置', '执行', '制定',
        # 言说动词
        '表示', '称', '说', '指出', '认为', '强调', '介绍', '宣布', '回应',
        '发布', '报道', '谈',
        # 协作/参与动词
        '交流', '联系', '沟通', '协调', '配合', '支持', '帮助',
        '协助', '参与', '参加', '加入', '入选', '荣获', '获得', '取得', '完成',
        # 状态/过程动词
        '结束', '组织', '策划', '实施', '修订', '修改', '调整', '改革',
        '创新', '探索', '尝试', '努力', '奋斗', '争取', '期待', '希望', '成为',
        '需要', '可以', '没有', '随着', '根据', '由于', '但是', '并且', '同时',
        '其中', '其他', '相关', '计划', '工作', '问题', '情况', '方面', '建设',
        '开始', '已经', '正在', '继续', '持续', '保持', '发生', '出现', '达到',
        '超过', '接近', '进入', '退出', '返回', '到达', '离开', '前往', '参观',
        '视察', '商谈', '商讨', '协定', '协议', '条约', '合同', '赢得', '博得',
        '落得', '承办', '经办', '主办', '操办', '筹办', '兴办', '复办', '停办',
        '建立', '树立', '设置', '开设', '开办', '撤销', '取消', '废除', '废止',
        '停止', '终止', '中止', '暂停', '中断', '间断', '连续', '陆续', '延续',
        '延长', '延展', '延伸', '蔓延',
        # 反向/对抗动词
        '反对', '反驳', '反诘', '反问', '反诉', '反告', '反咬', '反噬', '反馈',
        '反应', '反映', '反响',
        # 批/答动词
        '回答', '答复', '回复', '批复', '批答', '答批', '核批', '报批', '呈批',
        '转批', '加批', '眉批', '旁批', '朱批', '总批', '点评', '评论', '议论',
        '讨论', '谈论', '研讨', '深究', '探究',
        # 侦查/勘察动词
        '侦察', '侦查', '勘察', '勘测', '勘探', '勘查', '踏勘', '校勘', '推勘',
        '查勘', '勘误', '勘正', '校正', '校对', '校核', '累计', '总计', '合计',
        '共计', '约计', '算计', '盘算', '筹算', '测算', '推算', '演算', '验算',
        '审计', '稽核', '考核', '考查', '考察', '检验', '检测', '检疫', '查验',
        '查收', '查访', '查询', '查究', '查抄', '查封', '查扣', '查禁', '查处',
        '查缉', '查核', '审查', '稽查', '缉查', '探查', '测查', '巡查', '纠查',
        '访查',
        # 视觉动词
        '侦', '察', '观', '看', '望', '瞧', '视', '盯', '瞄', '瞥', '瞅', '瞪',
        '睹', '窥', '凝视', '注视', '审视', '重视', '轻视', '忽视', '漠视', '无视',
        '蔑视', '藐视', '鄙视', '歧视', '敌视', '仇视',
        # 财经模板词
        '同比', '环比', '预增', '预降', '预计', '营收', '净利润', '归母', '成交额',
        '成交量', '市盈率', '市值', '一季度', '二季度', '三季度', '四季度', '半年报',
        '年报', '单日', '暨', '同比增长', '环比下降', '环比上涨', '同比下降',
        '同比增长率', '同比预增', '同比预降', '环比预增', '环比预降',
    }
    
    # 中文职务词（用于过滤纯职务+人名）
    ZH_TITLES = {'总统', '总理', '首相', '主席', '总书记', '部长', '外长', '防长',
                 '国务卿', '财长', '国防部长', '外交部长', '总统候选人', '副总统',
                 '议长', '省长', '市长', '县长', '州长', '省长', '委员长', '主任',
                 '书记', '局长', '厅长', '司长', '处长', '科长', '队长', '所长',
                 '院长', '校长', '厂长', '经理', '董事长', '总裁', 'ceo', 'cfo'}
    
    def _is_valid_phrase(words, flags, language='zh'):
        """验证短语是否构成有效新闻事件"""
        if language == 'zh':
            # 不能全是虚词/形容词/副词/数词/量词
            content_count = sum(1 for f in flags if not f.startswith(('d', 'p', 'c', 'u', 'e', 'y', 'o', 'm', 'q', 'a')))
            if content_count < 1:
                return False
            
            # 过滤纯职务+人名（如"总统万斯"）
            phrase_str = ''.join(words)
            if len(words) == 2 and (words[0] in ZH_TITLES or phrase_str.startswith('总统') or phrase_str.startswith('总理')):
                if flags[1].startswith(('nr', 'nz', 'nrt')):
                    return False
            
            return True
        else:
            # 必须包含至少1个 EVENT_WORDS 中的词
            has_event = any(w in EVENT_WORDS for w in words)
            if not has_event:
                return False
            
            # 不能全是普通名词
            content_count = sum(1 for w in words if w not in common_verbs and w not in STOP_WORDS)
            if content_count < 1:
                return False
            
            return True
    
    def _get_event_bonus(words, flags, language='zh'):
        """计算短语的事件性加权得分"""
        if language == 'zh':
            has_entity = any(f.startswith(('nr', 'ns', 'nt', 'nz', 'j', 'nrt')) for f in flags)
            has_event = any(
                (f.startswith('v') and w not in common_verbs) or w in EVENT_WORDS
                for w, f in zip(words, flags)
            )
            
            if has_entity and has_event:
                bonus = 1.6      # 实体+事件，最高优先级（伊朗战争）
            elif has_entity:
                bonus = 0.8      # 有实体但无事件（中国经济圆桌、俄外交部）
            elif has_event:
                bonus = 0.5      # 有事件但无实体（较少见）
            else:
                bonus = 0.2      # 纯普通名词组合，只有数量极高才会出现
        else:
            if any(w in EVENT_WORDS for w in words):
                bonus = 1.6
            else:
                bonus = 0.3
        
        return bonus
    
    # 收集候选短语
    phrase_data = {}  # phrase -> {'news_ids': set, 'count': int, 'words': list, 'flags': list, 'lang': str, 'times': list}
    all_words = Counter()
    now = datetime.now()
    
    for news_id, title, content, language, created_at in news_list:
        if not title:
            continue
        
        # 统一 created_at 为 datetime 对象
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            except Exception:
                created_at = now
        if not isinstance(created_at, datetime):
            created_at = now
        
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
                for n in range(min(4, len(chunk)), 1, -1):  # 最多4-gram
                    for i in range(len(chunk) - n + 1):
                        words = [item[0] for item in chunk[i:i+n]]
                        flags = [item[1] for item in chunk[i:i+n]]
                        phrase = ''.join(words)
                        if len(phrase) < 4 or len(phrase) > 20:
                            continue
                        if not _is_valid_phrase(words, flags, language='zh'):
                            continue
                        if phrase in JUNK_PHRASES or any(p.match(phrase) for p in JUNK_PHRASE_PATTERNS):
                            continue
                        if phrase not in phrase_data:
                            phrase_data[phrase] = {'news_ids': set(), 'count': 0, 'words': words, 'flags': flags, 'lang': 'zh', 'times': []}
                        phrase_data[phrase]['news_ids'].add(news_id)
                        phrase_data[phrase]['count'] = len(phrase_data[phrase]['news_ids'])
                        phrase_data[phrase]['times'].append(created_at)
                        for w in words:
                            all_words[w] += 1
        else:
            # 英文：保留2-gram/3-gram/4-gram
            words = re.findall(r'\b[a-zA-Z]+\b', title.lower())
            words = [w for w in words if len(w) >= 3 and w not in STOP_WORDS]
            for n in range(4, 1, -1):
                if len(words) < n:
                    continue
                for i in range(len(words) - n + 1):
                    phrase_words = words[i:i+n]
                    phrase = ' '.join(phrase_words)
                    if len(phrase) > 40:
                        continue
                    if not _is_valid_phrase(phrase_words, None, language='en'):
                        continue
                    if phrase in JUNK_PHRASES or any(p.match(phrase) for p in JUNK_PHRASE_PATTERNS):
                        continue
                    if phrase not in phrase_data:
                        phrase_data[phrase] = {'news_ids': set(), 'count': 0, 'words': phrase_words, 'flags': None, 'lang': 'en', 'times': []}
                    phrase_data[phrase]['news_ids'].add(news_id)
                    phrase_data[phrase]['count'] = len(phrase_data[phrase]['news_ids'])
                    phrase_data[phrase]['times'].append(created_at)
                    for w in phrase_words:
                        all_words[w] += 1
    
    if not phrase_data:
        return []
    
    # 计算IDF
    N = len(news_list)
    idf = {}
    for word, freq in all_words.items():
        idf[word] = math.log(N / (freq + 1)) + 1.0
    
    # 计算短语得分（引入事件性加权 + 时间衰减）
    scored_phrases = []
    for phrase, data in phrase_data.items():
        doc_freq = data['count']
        if doc_freq < 2:
            continue
        
        words = data['words']
        flags = data['flags']
        lang = data['lang']
        
        avg_idf = sum(idf.get(w, 1.0) for w in words) / len(words) if words else 1.0
        if avg_idf < 1.2:  # 略微放宽通用词阈值
            continue
        
        length = len(words)
        event_bonus = _get_event_bonus(words, flags, language=lang)
        
        # 时间衰减加权：平均新闻年龄越小得分越高，范围 [0.8, 1.2]
        times = data['times']
        if times:
            avg_age_hours = sum((now - t).total_seconds() for t in times) / len(times) / 3600.0
            time_bonus = max(0.8, min(1.2, 1.2 - (0.4 * avg_age_hours / 48.0)))
        else:
            time_bonus = 1.0
        
        score = doc_freq * avg_idf * (1 + 0.12 * length) * event_bonus * time_bonus
        scored_phrases.append((phrase, score, doc_freq, data['news_ids'], times))
    
    # LCS重叠合并（阈值25%，更严格去重）
    scored_phrases.sort(key=lambda x: x[1], reverse=True)
    merged = []
    for phrase, score, doc_freq, news_ids, times in scored_phrases:
        is_dup = False
        for merged_phrase, _, _, _, _ in merged:
            if phrase in merged_phrase or merged_phrase in phrase:
                is_dup = True
                break
            lcs = _lcs_length(phrase, merged_phrase)
            shorter = min(len(phrase), len(merged_phrase))
            if shorter > 0 and lcs / shorter > 0.25:
                is_dup = True
                break
        if not is_dup:
            merged.append((phrase, score, doc_freq, news_ids, times))
    
    # 生成话题
    topics = []
    for phrase, score, doc_freq, news_ids, times in merged[:15]:
        related_ids = []
        for nid, title, _, lang, _ in news_list:
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
            'representative_id': representative_id,
            'times': times
        })
    
    topics.sort(key=lambda x: x['news_count'], reverse=True)
    return topics

def update_hot_topics_internal():
    """内部函数：更新热点话题到数据库"""
    print(f"[{datetime.now()}] 开始更新热点话题...")
    
    with engine.connect() as conn:
        # 获取48小时内的新闻
        result = conn.execute(text("""
            SELECT news_id, title, content, language, created_at
            FROM news
            WHERE created_at > DATE_SUB(NOW(), INTERVAL 48 HOUR)
            ORDER BY created_at DESC
        """))
        
        news_list = [(row[0], row[1], row[2] or '', row[3] or 'zh', row[4]) for row in result.fetchall()]
        
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
            news_times = topic.get('times', [])
            if not news_times:
                for nid in topic['news_ids']:
                    for n in news_list:
                        if n[0] == nid:
                            news_times.append(n[4] if len(n) > 4 else datetime.now())
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

# ==================== 新增 API 端点（从旧版恢复）====================

@app.route('/api/stats/countries', methods=['GET'])
def get_country_stats():
    """
    获取近48小时内各国新闻数量统计（包含所有关联国家）
    返回格式: {"CN": 45, "US": 38, ...}
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT 
                    nc.country_code,
                    COUNT(DISTINCT nc.news_id) as news_count
                FROM news_countries nc
                JOIN news n ON nc.news_id = n.news_id
                WHERE n.created_at > DATE_SUB(NOW(), INTERVAL 48 HOUR)
                  AND nc.is_primary = TRUE
                GROUP BY nc.country_code
                ORDER BY news_count DESC
            """))
            stats = {}
            for row in result.fetchall():
                if row[0]:
                    stats[row[0]] = row[1]
            return jsonify(stats)
    except Exception as e:
        print(f"[API Error] get_country_stats: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/categories', methods=['GET'])
def get_categories():
    """
    获取所有新闻分类
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
    """
    try:
        with engine.connect() as conn:
            cat_result = conn.execute(
                text("SELECT category_id FROM categories WHERE category_code = :code"),
                {'code': category_code}
            ).fetchone()
            if not cat_result:
                return jsonify({"error": "Category not found"}), 404
            category_id = cat_result[0]
            result = conn.execute(text("""
                SELECT 
                    n.news_id, n.title, n.summary, n.created_at, nc.country_code
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
        return jsonify({"error": str(e)}), 500


@app.route('/api/news/<int:news_id>', methods=['GET'])
def get_news_detail(news_id):
    """
    获取单条新闻详情（含图片、视频）
    """
    try:
        with engine.connect() as conn:
            news_result = conn.execute(text("""
                SELECT 
                    n.news_id, n.title, n.summary, n.content, n.published_at,
                    n.source_url, s.source_name, nc.country_code, c.country_name
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
                SELECT media_url FROM media
                WHERE news_id = :news_id AND media_type = 'image'
                ORDER BY media_id ASC
            """), {'news_id': news_id})
            news_data["images"] = [{"url": r[0]} for r in images_result.fetchall()]
            # 获取视频
            videos_result = conn.execute(text("""
                SELECT media_url FROM media
                WHERE news_id = :news_id AND media_type = 'video'
                ORDER BY media_id ASC
            """), {'news_id': news_id})
            videos = []
            for r in videos_result.fetchall():
                url = r[0]
                vtype = "mp4"
                if '.m3u8' in url.lower(): vtype = "hls"
                elif 'youtube' in url.lower() or 'youtu.be' in url.lower(): vtype = "youtube"
                elif 'bilibili' in url.lower(): vtype = "bilibili"
                elif 'player' in url.lower() or 'embed' in url.lower(): vtype = "embed"
                videos.append({"url": url, "type": vtype})
            news_data["videos"] = videos
            return jsonify(news_data)
    except Exception as e:
        print(f"[API Error] get_news_detail: {e}")
        return jsonify({"error": str(e)}), 500


# 前端路由 - 所有非 API 请求都返回 index.html（支持 React Router）
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    """服务前端静态文件"""
    if path.startswith('api/') or path.startswith('sru') or path == 'health':
        return jsonify({"error": "Not found"}), 404
    file_path = os.path.join(STATIC_DIR, path)
    if path and os.path.exists(file_path) and os.path.isfile(file_path):
        return send_from_directory(STATIC_DIR, path)
    index_path = os.path.join(STATIC_DIR, 'index.html')
    if os.path.exists(index_path):
        return send_from_directory(STATIC_DIR, 'index.html')
    return jsonify({
        "status": "QuickNews API is running",
        "endpoints": {
            "health": "/health",
            "api": "/api/*",
            "sru": "/sru",
            "categories": "/api/categories",
            "country_stats": "/api/stats/countries",
            "hot_topics": "/api/topics"
        }
    })


@app.route('/api/stats/topics', methods=['GET'])
def get_stats_topics():
    """
    获取热点话题 TOP 10（简化版，供前端热力图页面使用）
    返回格式: [{"id": 1, "name": "...", "count": 10}, ...]
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT topic_id, topic_name, news_count
                FROM hot_topics
                WHERE is_active = TRUE
                ORDER BY news_count DESC, last_news_time DESC
                LIMIT 10
            """))
            
            topics = []
            for row in result.fetchall():
                topics.append({
                    'id': row[0],
                    'name': row[1],
                    'count': row[2]
                })
            
            return jsonify(topics)
    except Exception as e:
        print(f"[API Error] get_stats_topics: {e}")
        import traceback
        traceback.print_exc()
        return jsonify([]), 500


@app.route('/api/topics/<int:topic_id>/news', methods=['GET'])
def get_topic_news_detail(topic_id):
    """
    获取指定话题下的关联新闻
    """
    try:
        limit = int(request.args.get('limit', 20))
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT 
                    n.news_id, n.title, n.summary, n.source_url,
                    n.created_at, n.language, n.has_video,
                    nc.country_code
                FROM news n
                JOIN news_topics nt ON n.news_id = nt.news_id
                LEFT JOIN news_countries nc ON n.news_id = nc.news_id AND nc.is_primary = 1
                WHERE nt.topic_id = :topic_id
                ORDER BY nt.is_representative DESC, n.created_at DESC
                LIMIT :limit
            """), {'topic_id': topic_id, 'limit': limit})
            
            news_list = []
            for row in result.fetchall():
                news_list.append({
                    'id': row[0],
                    'title': row[1],
                    'summary': row[2],
                    'url': row[3],
                    'time': row[4].isoformat() if row[4] else '',
                    'language': row[5],
                    'has_video': bool(row[6]),
                    'country': row[7] or 'unknown'
                })
            
            return jsonify({'news': news_list})
    except Exception as e:
        print(f"[API Error] get_topic_news_detail: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'news': []}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
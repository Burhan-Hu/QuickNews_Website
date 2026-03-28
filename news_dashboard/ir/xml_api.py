from flask import Flask, request, Response
from sqlalchemy import text
import sys,os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.db_config import engine
import xml.etree.ElementTree as ET
import re
import html
import json

app = Flask(__name__)

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
    
    def search(self, query_str, max_results=20, offset=0):
        """执行XML检索"""
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
                JOIN news_countries nc ON n.news_id = nc.news_id
                WHERE nc.country_code IN ({placeholders})
                  AND nc.is_primary = TRUE
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

if __name__ == '__main__':
    # 生产环境使用gunicorn: gunicorn -w 4 -b 0.0.0.0:5000 xml_api:app
    app.run(host='0.0.0.0', port=5000, threaded=True, debug=False)
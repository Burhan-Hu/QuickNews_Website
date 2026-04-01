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


# ==================== 新增 API 端点 ====================

@app.route('/api/stats/countries', methods=['GET'])
def get_country_stats():
    """
    获取近48小时内各国新闻数量统计
    返回格式: {"CN": 45, "US": 38, "JP": 25, ...}
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT 
                    nc.country_code,
                    COUNT(*) as news_count
                FROM news_countries nc
                JOIN news n ON nc.news_id = n.news_id
                WHERE n.created_at > DATE_SUB(NOW(), INTERVAL 48 HOUR)
                  AND nc.is_primary = TRUE
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


@app.route('/api/stats/topics', methods=['GET'])
def get_hot_topics():
    """
    获取近48小时内的热门话题 TOP 10
    返回格式: [{"name": "人工智能", "count": 156}, {"name": "气候变化", "count": 132}, ...]
    """
    try:
        with engine.connect() as conn:
            # 方案1: 从 inverted_index 表查询高频词项（标题权重更高）
            result = conn.execute(text("""
                SELECT 
                    ii.term,
                    COUNT(DISTINCT ii.news_id) as doc_count,
                    SUM(ii.tf_weight) as total_weight
                FROM inverted_index ii
                JOIN news n ON ii.news_id = n.news_id
                WHERE n.created_at > DATE_SUB(NOW(), INTERVAL 48 HOUR)
                  AND ii.language = 'zh'
                  AND LENGTH(ii.term) >= 2
                  AND ii.term NOT IN ('中国', '美国', '日本', '今天', '我们', '他们', '可以', '进行', '表示', '认为', '已经', '开始', '目前', '今年', '去年')
                GROUP BY ii.term
                HAVING doc_count >= 2
                ORDER BY total_weight DESC, doc_count DESC
                LIMIT 10
            """))
            
            topics = []
            for row in result.fetchall():
                term = row[0]
                count = int(row[1])
                # 过滤单字和纯数字
                if len(term) >= 2 and not term.isdigit():
                    topics.append({
                        "name": term,
                        "count": count
                    })
            
            # 如果没有中文话题，尝试查询英文
            if not topics:
                result = conn.execute(text("""
                    SELECT 
                        ii.term,
                        COUNT(DISTINCT ii.news_id) as doc_count,
                        SUM(ii.tf_weight) as total_weight
                    FROM inverted_index ii
                    JOIN news n ON ii.news_id = n.news_id
                    WHERE n.created_at > DATE_SUB(NOW(), INTERVAL 48 HOUR)
                      AND ii.language = 'en'
                      AND LENGTH(ii.term) >= 3
                    GROUP BY ii.term
                    HAVING doc_count >= 2
                    ORDER BY total_weight DESC, doc_count DESC
                    LIMIT 10
                """))
                
                for row in result.fetchall():
                    term = row[0]
                    count = int(row[1])
                    if len(term) >= 3:
                        topics.append({
                            "name": term,
                            "count": count
                        })
            
            return jsonify(topics)
    except Exception as e:
        print(f"[API Error] get_hot_topics: {e}")
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

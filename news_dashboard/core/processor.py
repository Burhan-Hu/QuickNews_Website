from html.parser import HTMLParser
import re
import json
import os

class MLStripper(HTMLParser):
    """HTML标签清洗器"""
    def __init__(self):
        super().__init__()
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

class ContentProcessor:
    """
    XML检索增强版：支持中英文分词，输出JSON格式供数据库存储过程使用
    国家关键词支持从数据库 country_keywords 表加载，失败时使用内置默认值
    """
    
    # source_name 到 source_id 的映射（与 schema2.sql 中的来源顺序一致）
    SOURCE_NAME_TO_ID = {
        # NewsAPI
        'NewsAPI': 1,
        # RSS 来源
        '36氪': 2,
        '虎嗅网': 3,
        'RT-中文': 4,
        'FoxNews-World': 5,
        '南华早报-SCMP': 6,
        'FoxNews-Politics': 7,
        'ChinaDaily': 8,
        'NewYorker': 9,
        '凤凰网-军事': 10,
        'AP-美联社': 11,
        '经济日报': 12,
        # HTML 爬取来源
        '新华网-时政': 13,
        'CNN': 14,
        '界面新闻': 15,
        'Al Jazeera': 16,
        '环球时报': 17,
        'ScienceDaily': 18,
        '俄罗斯卫星通讯社': 19,
        '纽约时报-中文': 20,
        '纽约时报中文版': 20,
        'BBC': 21,
        # 兼容 fetcher.py 中 NewsAPI 返回的名称
        'newsapi': 1,
    }
    
    def __init__(self):
        # 从数据库加载国家关键词（如果失败则使用内置默认值）
        self.country_keywords = self._load_country_keywords()
        
        # 中文停用词（简化版）
        self.zh_stopwords = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', 
                             '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', 
                             '着', '没有', '看', '好', '自己', '这', '那', '这些', '那些', '这个', 
                             '那个', '之', '与', '及', '或', '但', '而', '然而', '因为', '所以', 
                             '因此', '如果', '即使', '虽然', '尽管', '如此', '便', '就', '即使', 
                             '由', '被', '把', '给', '让', '向', '往', '自', '从', '到', '关于', 
                             '对于', '为了', '为着', '除', '除了', '除去', '凭着', '根据', '按照', 
                             '通过', '经过', '随着', '作为', '如同', '好像', '一样', '似的', '似乎', 
                             '一样', '一般', '似的', '一样地', '般地',}
        # 英文停用词
        self.en_stopwords = {'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i', 
                             'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at', 
                             'this', 'but', 'his', 'by', 'from', 'they', 'we', 'say', 'her', 'she', 
                             'or', 'an', 'will', 'my', 'one', 'all', 'would', 'there', 'their', 'what',
                               'so', 'up', 'out', 'if', 'about', 'who', 'get', 'which', 'go', 'me', 
                               'when', 'make', 'can', 'like', 'time', 'no', 'just', 'him', 'know', 
                               'take', 'people', 'into', 'year', 'your', 'good', 'some', 'could', 
                               'them', 'see', 'other', 'than', 'then', 'now', 'look', 'only', 'come', 
                               'its', 'over', 'think', 'also', 'back', 'after', 'use', 'two', 'how', 
                               'our', 'work', 'first', 'well', 'way', 'even', 'new', 'want', 'because',
                                 'any', 'these', 'give', 'day', 'most', 'us', 'is', 'was', 'are', 'were', 
                                 'been', 'has', 'had', 'did', 'does', 'doing', 'done'}

    def _load_country_keywords(self):
        """
        从数据库 country_keywords 表加载国家关键词
        如果失败或表为空，使用内置默认值
        """
        try:
            from config.db_config import engine
            from sqlalchemy import text
            
            with engine.connect() as conn:
                result = conn.execute(text(
                    "SELECT country_code, keyword FROM country_keywords ORDER BY country_code"
                ))
                rows = result.fetchall()
                
                if not rows:
                    print("[Processor] country_keywords 表为空，使用内置默认关键词")
                    return self.COUNTRY_KEYWORDS
                
                # 转换为字典格式
                keywords_dict = {}
                for row in rows:
                    code, keyword = row[0], row[1]
                    if code not in keywords_dict:
                        keywords_dict[code] = {'keywords': [], 'weight': 1.0}
                    keywords_dict[code]['keywords'].append(keyword)
                
                print(f"[Processor] 从数据库加载了 {len(keywords_dict)} 个国家的关键词")
                return keywords_dict
                
        except Exception as e:
            print(f"[Processor] 加载数据库关键词失败: {e}, 使用内置默认关键词")
            return self.COUNTRY_KEYWORDS

    @staticmethod
    def clean_html(raw_html):
        """去除HTML标签，返回纯文本"""
        if not raw_html:
            return ''
        try:
            s = MLStripper()
            s.feed(raw_html)
            return s.get_data().strip()
        except:
            return re.sub(r'<[^>]+>', '', raw_html).strip()

    def tokenize_chinese(self, text):
        """
        中文分词：使用n-gram（2元组）+ 单字 Fallback
        实际生产环境建议接入jieba（本地库，无云服务）
        """
        if not text:
            return []
        
        # 清洗文本
        text = re.sub(r'[^\u4e00-\u9fffa-zA-Z0-9]', ' ', text)
        
        terms = []
        chars = [c for c in text if '\u4e00' <= c <= '\u9fff' or c.isalnum()]
        
        # 产生n-gram（2元组）
        for i in range(len(chars) - 1):
            bigram = chars[i] + chars[i+1]
            if len(bigram) == 2 and bigram not in self.zh_stopwords:
                terms.append(bigram)
        
        # 同时保留单字（长度>1的字）
        for c in chars:
            if '\u4e00' <= c <= '\u9fff' and c not in self.zh_stopwords and len(c) > 1:
                terms.append(c)
        
        return list(set(terms))  # 去重

    def tokenize_english(self, text):
        """
        英文分词：空格切分 + 词干提取（简化版）+ 停用词过滤
        """
        if not text:
            return []
        
        # 转小写，替换非字母数字为空格
        text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text.lower())
        words = text.split()
        
        # 过滤停用词和短词
        terms = []
        for word in words:
            word = word.strip()
            if len(word) > 2 and word not in self.en_stopwords:
                # 简化词干提取（去除常见后缀）
                if word.endswith('ing') and len(word) > 5:
                    word = word[:-3]
                elif word.endswith('ed') and len(word) > 4:
                    word = word[:-2]
                elif word.endswith('s') and len(word) > 3 and not word.endswith('ss'):
                    word = word[:-1]
                terms.append(word)
        
        return list(set(terms))

    def detect_language(self, text):
        """检测语言：简单启发式（含中文字符即为zh）"""
        if any('\u4e00' <= c <= '\u9fff' for c in text):
            return 'zh'
        return 'en'

    def identify_countries(self, title, content):
        """
        【新逻辑】只返回一个主要关联国
        1. 标题优先：标题中出现的国家按出现次数统计
        2. 标题无匹配 → 正文统计出现次数最多的国家
        3. 都没有匹配 → 返回空（无关联国）
        """
        if not title and not content:
            return []

        title = title or ''
        content = content or ''

        # 标题优先统计
        title_counts = {}
        for country_code, data in self.country_keywords.items():
            count = sum(title.count(kw) for kw in data['keywords'])
            if count > 0:
                title_counts[country_code] = count

        if title_counts:
            # 取出现次数最多的国家作为主要关联国
            max_country = max(title_counts.items(), key=lambda x: x[1])[0]
            return [(max_country, True)]

        # 标题无匹配 → 正文统计
        content_counts = {}
        for country_code, data in self.country_keywords.items():
            count = sum(content.count(kw) for kw in data['keywords'])
            if count > 0:
                content_counts[country_code] = count

        if content_counts:
            # 取出现次数最多的国家作为主要关联国
            max_country = max(content_counts.items(), key=lambda x: x[1])[0]
            return [(max_country, True)]

        # 都没有匹配到任何国家
        return []

    def process_article(self, article):
        """
        处理文章：清洗HTML、分词、生成JSON格式分词结果
        返回：包含terms_json的字典，供存储过程使用
        """
        content = self.clean_html(article.get('content', ''))
        title = self.clean_html(article.get('title', ''))
        
        if not content or not title:
            return None
        
        # 检测语言
        lang = self.detect_language(title + content)
        
        # 分词
        if lang == 'zh':
            title_terms = self.tokenize_chinese(title)
            content_terms = self.tokenize_chinese(content[:1000])  # 限制长度提升性能
        else:
            title_terms = self.tokenize_english(title)
            content_terms = self.tokenize_english(content[:2000])
        
        # 根据 source_name 获取 source_id
        source_name = article.get('source_name', '')
        source_id = self.SOURCE_NAME_TO_ID.get(source_name, 1)
        
        # 【新增】识别相关国家
        related_countries = self.identify_countries(title, content)
        
        return {
            'title': title[:300],
            'content': content[:20000],
            'source_url': article.get('source_url', '')[:800],
            'source_id': source_id,
            'published_at': article.get('published_at'),
            'language': lang,
            'hint_country': article.get('country_hint'),
            'hint_category': article.get('category_hint'),
            'images': article.get('images', []),
            'videos': article.get('videos', []),
            'image_url': article.get('image_url'),
            # 【新增】分词结果JSON，供数据库存储过程使用
            'title_terms_json': json.dumps(title_terms, ensure_ascii=False),
            'content_terms_json': json.dumps(content_terms, ensure_ascii=False),
            'term_count': len(title_terms) + len(content_terms),
            # 【新增】相关国家列表
            'related_countries': related_countries,
        }

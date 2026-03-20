import re
from collections import Counter

class ContentProcessor:
    """
    内容处理器：国家识别与分类（使用文化/地理/经济符号，避免敏感人物）
    """
    
    # 国家识别词典（中性词汇：地理、文化、经济符号）
    COUNTRY_PROFILES = {
        'CN': {
            'geo': ['北京', '上海', '广州', '深圳', '香港', '台北', '长江', '黄河', '泰山', '黄山', '熊猫'],
            'culture': ['春节', '中秋', '饺子', '茶', '书法', '京剧', '长城', '故宫', '高铁', '丝绸'],
            'econ': ['人民币', '元', ' Alibaba', ' Tencent', '抖音', '淘宝', '小米', '华为'],
            'lang': ['China', 'Chinese']
        },
        'US': {
            'geo': ['纽约', '洛杉矶', '芝加哥', '硅谷', '好莱坞', '黄石', '大峡谷', '夏威夷'],
            'culture': ['好莱坞', 'NBA', '摇滚', '汉堡', '星巴克', '迪士尼', '感恩节', '棒球'],
            'econ': ['美元', 'USD', '华尔街', '纳斯达克', 'Apple', 'Google', 'Amazon', 'Microsoft', 'Tesla'],
            'lang': ['America', 'American', 'USA', 'US', 'United States']
        },
        'JP': {
            'geo': ['东京', '大阪', '京都', '富士山', '北海道', '冲绳', '樱花', '新干线'],
            'culture': ['寿司', '拉面', '动漫', '和服', '神社', '相扑', '武士', '任天堂', '索尼'],
            'econ': ['日元', 'Yen', 'Toyota', 'Honda', 'Sony', 'Nintendo', '优衣库'],
            'lang': ['Japan', 'Japanese', 'Tokyo']
        },
        'GB': {
            'geo': ['伦敦', '曼彻斯特', '爱丁堡', '泰晤士河', '大本钟', '巨石阵'],
            'culture': ['英超', '红茶', '皇家', '莎士比亚', '哈利波特', '摇滚', '下午茶'],
            'econ': ['英镑', 'Pound', 'BBC', 'HSBC', 'Unilever', 'BP'],
            'lang': ['UK', 'Britain', 'British', 'England', 'English']
        },
        'DE': {
            'geo': ['柏林', '慕尼黑', '法兰克福', '莱茵河', '阿尔卑斯', '黑森林'],
            'culture': ['啤酒', '香肠', '汽车', '足球', '古典音乐', '哲学', '啤酒节'],
            'econ': ['欧元', 'Euro', 'BMW', '奔驰', '大众', '西门子', 'SAP', '阿迪达斯'],
            'lang': ['Germany', 'German', 'Deutschland']
        },
        'FR': {
            'geo': ['巴黎', '里昂', '马赛', '塞纳河', '阿尔卑斯', '卢浮宫', '埃菲尔铁塔'],
            'culture': ['葡萄酒', '奶酪', '时尚', '艺术', '足球', '电影', '面包', '香水'],
            'econ': ['欧元', 'Euro', 'LVMH', '香奈儿', '迪奥', '空客', 'Total', '欧莱雅'],
            'lang': ['France', 'French', 'Paris']
        }
    }
    
    # 分类规则（中性关键词）
    CATEGORY_RULES = {
        'tech': {
            'keywords': ['科技', '技术', '互联网', 'AI', '人工智能', '芯片', '手机', '电脑', '软件', '硬件', '数据', '算法', 
                        'tech', 'technology', 'software', 'hardware', 'AI', 'artificial intelligence', 'chip', 'smartphone', 'digital', 'cyber'],
            'weight': 1.0
        },
        'politics': {  
            'keywords': ['政治', '外交', '选举', '议会', '政府', '政策', '立法', '党', '总统', '首相', '部长',
                        'politics', 'political', 'election', 'government', 'policy', 'diplomatic', 'parliament', 'congress', 'senate'],
            'weight': 1.0
        },
        'economy': {
            'keywords': ['经济', '金融', '股市', '贸易', '市场', '投资', '银行', '货币', '财政', '商业', '公司', '企业', 'GDP',
                        'economy', 'finance', 'stock', 'trade', 'market', 'investment', 'bank', 'business', 'company', 'economic'],
            'weight': 1.0
        },
        'military': {
            'keywords': ['军事', '国防', '武器', '导弹', '军舰', '战机', '军队', '安全', '战争', '冲突', '防御',
                        'military', 'defense', 'weapon', 'missile', 'navy', 'army', 'air force', 'war', 'conflict', 'security'],
            'weight': 1.0
        },
        'culture': {
            'keywords': ['文化', '艺术', '电影', '音乐', '书', '展览', '旅游', '美食', '历史', '遗产',
                        'culture', 'art', 'movie', 'film', 'music', 'book', 'exhibition', 'travel', 'food', 'history'],
            'weight': 1.0
        },
        'sports': {  # 新增：体育
            'keywords': ['体育', '运动', '足球', '篮球', '奥运', '比赛', '联赛', '冠军', '世界杯', 'NBA', '运动员',
                        'sports', 'football', 'soccer', 'basketball', 'olympic', 'match', 'game', 'league', 'championship', 'player'],
            'weight': 1.0
        },
        'society': {  # 新增：社会
            'keywords': ['社会', '民生', '教育', '医疗', '环境', '气候', '灾难', '事故', '犯罪', '法律', '就业',
                        'society', 'social', 'education', 'medical', 'health', 'environment', 'climate', 'disaster', 'accident', 'crime'],
            'weight': 1.0
        },
        'international': {  # 新增：国际（综合）
            'keywords': ['国际', '全球', '世界', '跨国', '外交', '关系',
                        'international', 'global', 'world', 'foreign', 'affairs', 'diplomacy', 'relations'],
            'weight': 0.8  # 权重较低，避免与politics重复
    }
}
    def extract_countries(self, title, summary, hint_country=None):
        """
        识别新闻关联国家
        hint_country: RSS源预设的国家（如'US', 'RU'）
        """
        text = f"{title} {summary}"
        scores = {}
    
        # 1. 基于词典匹配（与之前相同）
        for code, profile in self.COUNTRY_PROFILES.items():
            score = 0
            for word in profile['geo']:
                score += text.count(word) * 3
            for word in profile['culture']:
                score += text.count(word) * 2
            for word in profile['econ']:
                score += text.count(word) * 2
            for word in profile['lang']:
                score += text.count(word) * 1
        
            if score > 0:
                scores[code] = score
    
        # 2. RSS源预设国家（强提示）
        if hint_country:
            hint_upper = hint_country.upper()
            if hint_upper in self.COUNTRY_PROFILES:
                # 预设国家加高分，但不一定是主国家（内容可能涉及他国）
                scores[hint_upper] = scores.get(hint_upper, 0) + 30
    
        # 3. NewsAPI提示
        if hint_country and hint_country.lower() in ['us', 'gb', 'jp', 'de', 'fr', 'ru', 'cn', 'in', 'kr']:
            pass  # 已在上面处理
    
        if not scores:
            if hint_country:
                return [(hint_country.upper(), True, 1)]
            return [('US', True, 1)]  # 默认
    
        # 排序并标记主要关联国
        sorted_countries = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        results = []
    
        for i, (code, score) in enumerate(sorted_countries[:3]):
            is_primary = (i == 0) or (score > sorted_countries[0][1] * 0.7)
            results.append((code, is_primary, score))
    
        return results
    
    def classify_categories(self, title, summary, hint_category=None):
        """
        多标签分类，返回: [(category_code, confidence), ...]
        """
        text = f"{title} {summary}".lower()
        scores = {}
        
        for cat_code, rule in self.CATEGORY_RULES.items():
            score = 0
            for keyword in rule['keywords']:
                if keyword.lower() in text:
                    score += 1
            if score > 0:
                scores[cat_code] = min(score / 3.0, 1.0)  # 归一化，最多3个关键词命中得1.0
        
        # NewsAPI提示处理
        if hint_category and hint_category in self.CATEGORY_RULES:
            scores[hint_category] = scores.get(hint_category, 0) + 0.5
            if scores[hint_category] > 1.0:
                scores[hint_category] = 1.0
        
        if not scores:
            return [('general', 0.5)]  # 默认分类
        
        # 返回所有得分>0.3的分类（多标签）
        threshold = 0.3
        return [(code, score) for code, score in scores.items() if score >= threshold]
    
    def process_article(self, article):
        """
        处理单条新闻，添加countries和categories字段
        验证数据完整性：content和summary都不能为空，content必须>=60字
        """
        # 验证：content和summary都不能为空
        content = article.get('content', '').strip() if article.get('content') else ''
        summary = article.get('summary', '').strip() if article.get('summary') else ''
        
        # 如果都为空，则跳过此条新闻
        if not content and not summary:
            print(f"    [Skip] 空数据：标题={article.get('title', '')[0:30]}, content和summary都为空")
            return None
        
        # 如果content<60字，直接放弃（低质量内容）
        if content and len(content) < 60:
            print(f"    [Skip] content过短：{len(content)}字（<60字最小限制），标题={article.get('title', '')[0:30]}")
            return None
        
        # 确保至少有summary
        if not summary and content:
            article['summary'] = content[:500]
        elif not content and summary:
            # 如果没有content但有summary，检查summary长度
            if len(summary) < 60:
                print(f"    [Skip] content和summary都过短，标题={article.get('title', '')[0:30]}")
                return None
            article['content'] = summary
        
        # 国家识别
        hint_country = article.get('country_hint')
        article['countries'] = self.extract_countries(
            article['title'], 
            article['summary'], 
            hint_country
        )
        
        # 分类
        hint_cat = article.get('category_hint')
        article['categories'] = self.classify_categories(
            article['title'],
            article['summary'],
            hint_cat
        )
        
        return article
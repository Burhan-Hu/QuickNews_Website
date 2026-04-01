/**
 * QuickNews XML API 封装
 * 对接 Flask 后端 API (http://localhost:5000)
 */

const API_BASE = 'http://localhost:5000';

/**
 * 解析 XML 响应，提取新闻数据
 * @param {string} xmlText - XML 文本
 * @returns {Array} 新闻数组
 */
export function parseNewsXML(xmlText) {
  const parser = new DOMParser();
  const doc = parser.parseFromString(xmlText, 'text/xml');
  
  // 检查解析错误
  const parserError = doc.querySelector('parsererror');
  if (parserError) {
    console.error('XML parsing error:', parserError.textContent);
    return [];
  }
  
  const records = doc.querySelectorAll('record');
  const news = [];
  
  records.forEach((record, index) => {
    try {
      const newsElem = record.querySelector('news');
      if (!newsElem) return;
      
      const id = newsElem.getAttribute('id') || `record-${index}`;
      const title = newsElem.querySelector('title')?.textContent?.trim() || '';
      const summary = newsElem.querySelector('summary')?.textContent?.trim() || '';
      
      // 提取元数据
      const metadata = newsElem.querySelector('metadata');
      const country = metadata?.querySelector('country')?.textContent?.trim() || '';
      
      // 提取时间
      const time = newsElem.querySelector('time')?.textContent?.trim() || 
                   newsElem.querySelector('published_at')?.textContent?.trim() || '';
      
      news.push({
        id,
        title,
        summary: summary.length > 200 ? summary.substring(0, 200) + '...' : summary,
        country,
        time
      });
    } catch (err) {
      console.error('Error parsing record:', err);
    }
  });
  
  return news;
}

/**
 * 搜索新闻
 * @param {string} query - 搜索查询 (支持 title:xxx, country:XX 等限定)
 * @param {number} maxRecords - 最大返回数量
 * @returns {Promise<Array>} 新闻数组
 */
export async function searchNews(query, maxRecords = 20) {
  try {
    const url = `${API_BASE}/sru?query=${encodeURIComponent(query)}&maximumRecords=${maxRecords}`;
    
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Accept': 'application/xml',
      },
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const xmlText = await response.text();
    const news = parseNewsXML(xmlText);
    
    // 如果返回空数组，尝试使用 Mock 数据
    if (news.length === 0) {
      console.log('[API] 返回空数据，使用 Mock 数据');
      return getMockNews(query);
    }
    
    return news;
  } catch (error) {
    console.error('Search news error:', error);
    // 返回模拟数据用于演示
    return getMockNews(query);
  }
}

/**
 * 获取最新新闻
 * @param {number} maxRecords - 最大返回数量
 * @returns {Promise<Array>} 新闻数组
 */
export async function getLatestNews(maxRecords = 20) {
  return searchNews('*', maxRecords);
}

/**
 * 按国家搜索新闻
 * @param {string} countryCode - 国家代码 (如 'CN', 'US')
 * @param {number} maxRecords - 最大返回数量
 * @returns {Promise<Array>} 新闻数组
 */
export async function searchByCountry(countryCode, maxRecords = 20) {
  return searchNews(`country:${countryCode}`, maxRecords);
}

/**
 * 按标题搜索新闻
 * @param {string} keyword - 关键词
 * @param {number} maxRecords - 最大返回数量
 * @returns {Promise<Array>} 新闻数组
 */
export async function searchByTitle(keyword, maxRecords = 20) {
  return searchNews(`title:${keyword}`, maxRecords);
}

/**
 * 健康检查
 * @returns {Promise<Object>} 健康状态
 */
export async function checkHealth() {
  try {
    const response = await fetch(`${API_BASE}/health`);
    return await response.json();
  } catch (error) {
    console.error('Health check error:', error);
    return { status: 'error', message: error.message };
  }
}

/**
 * 获取模拟新闻数据 (用于演示/API不可用时)
 * @param {string} query - 查询词
 * @returns {Array} 模拟新闻数组
 */
function getMockNews(query) {
  const mockNews = [
    {
      id: '1',
      title: '中国科技创新取得重大突破',
      summary: '中国在人工智能和量子计算领域取得重大进展，多项技术达到国际领先水平。',
      country: 'CN',
      time: '2024-01-15 10:30:00'
    },
    {
      id: '2',
      title: '美国总统发表国情咨文演讲',
      summary: '美国总统在国会发表年度国情咨文，阐述未来一年的政策方向和施政重点。',
      country: 'US',
      time: '2024-01-15 09:00:00'
    },
    {
      id: '3',
      title: '日本经济持续增长',
      summary: '日本第四季度GDP增长超预期，出口和内需双双回暖。',
      country: 'JP',
      time: '2024-01-15 08:30:00'
    },
    {
      id: '4',
      title: '欧盟通过新气候法案',
      summary: '欧盟成员国一致通过新的气候保护法案，目标2050年实现碳中和。',
      country: 'DE',
      time: '2024-01-15 07:00:00'
    },
    {
      id: '5',
      title: '英国首相访问印度',
      summary: '英国首相与印度总理举行会谈，双方签署多项合作协议。',
      country: 'GB',
      time: '2024-01-15 06:30:00'
    },
    {
      id: '6',
      title: '俄罗斯举办国际经济论坛',
      summary: '圣彼得堡国际经济论坛开幕，吸引全球数千名商界领袖参会。',
      country: 'RU',
      time: '2024-01-15 05:00:00'
    },
    {
      id: '7',
      title: '印度航天计划取得新进展',
      summary: '印度成功发射新一代通信卫星，标志着航天技术的重大突破。',
      country: 'IN',
      time: '2024-01-15 04:30:00'
    },
    {
      id: '8',
      title: '法国举办国际艺术展',
      summary: '巴黎卢浮宫举办大型国际艺术展，展出来自世界各地的珍贵艺术品。',
      country: 'FR',
      time: '2024-01-15 03:00:00'
    }
  ];
  
  // 根据查询词过滤
  if (query && query !== '*') {
    const lowerQuery = query.toLowerCase();
    return mockNews.filter(item => 
      item.title.toLowerCase().includes(lowerQuery) ||
      item.country.toLowerCase() === lowerQuery.replace('country:', '')
    );
  }
  
  return mockNews;
}

/**
 * 获取国家新闻统计 (用于热力图) - 旧方法，保留兼容性
 * @returns {Object} 国家代码到新闻数量的映射
 */
export async function getCountryStats() {
  try {
    // 尝试获取所有新闻并统计
    const allNews = await searchNews('*', 100);
    const stats = {};
    
    allNews.forEach(news => {
      if (news.country) {
        stats[news.country] = (stats[news.country] || 0) + 1;
      }
    });
    
    // 如果统计结果为空，使用 Mock 数据
    if (Object.keys(stats).length === 0) {
      console.log('[API] 国家统计为空，使用 Mock 数据');
      return getMockCountryStats();
    }
    
    return stats;
  } catch (error) {
    console.error('Get country stats error:', error);
    // 返回模拟数据
    return getMockCountryStats();
  }
}

/**
 * 获取模拟国家统计数据
 * @returns {Object} 模拟的国家统计数据
 */
function getMockCountryStats() {
  return {
    'CN': 45,
    'US': 38,
    'JP': 25,
    'GB': 20,
    'RU': 18,
    'IN': 15,
    'FR': 12,
    'DE': 10
  };
}

// ==================== 新增 API 方法 ====================

/**
 * 从后端 API 获取国家新闻统计 (用于热力图)
 * @returns {Promise<Object>} 国家代码到新闻数量的映射
 */
export async function getCountryStatsFromAPI() {
  try {
    const response = await fetch(`${API_BASE}/api/stats/countries`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    
    // 如果返回空对象，回退到 Mock 数据
    if (!data || Object.keys(data).length === 0) {
      console.log('[API] 国家统计 API 返回空数据，使用 Mock 数据');
      return getMockCountryStats();
    }
    
    return data;
  } catch (error) {
    console.error('Get country stats from API error:', error);
    // 返回模拟数据
    return getMockCountryStats();
  }
}

/**
 * 获取热门话题 TOP 10
 * @returns {Promise<Array>} 热门话题数组 [{"name": "人工智能", "count": 156}, ...]
 */
export async function getHotTopics() {
  try {
    const response = await fetch(`${API_BASE}/api/stats/topics`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    
    // 如果返回空数组，回退到 Mock 数据
    if (!data || data.length === 0) {
      console.log('[API] 热门话题 API 返回空数据，使用 Mock 数据');
      return getMockHotTopics();
    }
    
    return data;
  } catch (error) {
    console.error('Get hot topics error:', error);
    // 返回模拟数据
    return getMockHotTopics();
  }
}

/**
 * 获取模拟热门话题数据
 * @returns {Array} 模拟的热门话题数据
 */
function getMockHotTopics() {
  return [
    { name: '人工智能', count: 156 },
    { name: '气候变化', count: 132 },
    { name: '经济发展', count: 128 },
    { name: '国际关系', count: 98 },
    { name: '科技创新', count: 87 },
  ];
}

/**
 * 获取新闻来源列表
 * @returns {Promise<Array>} 新闻来源数组 [{"name": "36氪", "logo": "36", "color": "#3498db", "type": "rss"}, ...]
 */
export async function getSources() {
  try {
    const response = await fetch(`${API_BASE}/api/sources`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    
    // 如果返回空数组，回退到 Mock 数据
    if (!data || data.length === 0) {
      console.log('[API] 新闻来源 API 返回空数据，使用 Mock 数据');
      return getMockSources();
    }
    
    return data;
  } catch (error) {
    console.error('Get sources error:', error);
    // 返回模拟数据
    return getMockSources();
  }
}

/**
 * 获取模拟新闻来源数据
 * @returns {Array} 模拟的新闻来源数据
 */
function getMockSources() {
  return [
    { name: 'Reuters', logo: 'R', color: '#ff6b00', type: 'rss' },
    { name: 'BBC', logo: 'B', color: '#bb1919', type: 'rss' },
    { name: '新华网', logo: 'X', color: '#c41e3a', type: 'crawler' },
    { name: 'Associated Press', logo: 'AP', color: '#ff0000', type: 'api' },
    { name: '财新网', logo: 'C', color: '#1a5276', type: 'rss' },
    { name: '澎湃新闻', logo: 'P', color: '#000000', type: 'rss' },
    { name: 'TechCrunch', logo: 'TC', color: '#0a9e01', type: 'rss' },
    { name: 'The Verge', logo: 'V', color: '#e2127a', type: 'rss' },
  ];
}

// ==================== 新闻详情 API ====================

/**
 * 获取单条新闻详情
 * @param {string|number} newsId - 新闻ID
 * @returns {Promise<Object>} 新闻详情对象
 */
export async function getNewsDetail(newsId) {
  try {
    const response = await fetch(`${API_BASE}/api/news/${newsId}`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    
    // 如果返回错误，使用 Mock 数据
    if (data.error) {
      console.log('[API] 新闻详情 API 返回错误，使用 Mock 数据');
      return getMockNewsDetail(newsId);
    }
    
    return data;
  } catch (error) {
    console.error('Get news detail error:', error);
    // 返回模拟数据
    return getMockNewsDetail(newsId);
  }
}

/**
 * 获取模拟新闻详情数据
 * @param {string|number} newsId - 新闻ID
 * @returns {Object} 模拟的新闻详情
 */
function getMockNewsDetail(newsId) {
  const mockDetails = {
    '1': {
      id: 1,
      title: '中国科技创新取得重大突破',
      summary: '中国在人工智能和量子计算领域取得重大进展，多项技术达到国际领先水平。',
      content: `中国在科技创新领域取得了令人瞩目的重大突破。在人工智能领域，中国研究人员开发的最新大语言模型在多项国际评测中名列前茅，展现出强大的自然语言理解和生成能力。

在量子计算方面，中国科学家成功研制出新一代量子计算机，量子比特数量达到世界领先水平。这一突破将为密码学、药物研发、金融建模等领域带来革命性变化。

此外，中国在芯片制造、5G通信、新能源等前沿科技领域也取得了重要进展。专家表示，这些成就标志着中国正在从科技大国向科技强国迈进。

未来，中国将继续加大科技投入，推动产学研深度融合，力争在更多关键核心技术领域实现自主可控。`,
      published_at: '2024-01-15 10:30:00',
      source_name: '新华网',
      source_url: 'http://www.xinhuanet.com/tech/20240115/c_1123456789.htm',
      country_code: 'CN',
      country_name: '中国',
      images: [
        { url: 'https://picsum.photos/800/400?random=1', caption: '中国科技创新成果展示', is_cover: true },
        { url: 'https://picsum.photos/800/400?random=2', caption: '量子计算机实验室', is_cover: false },
      ],
      videos: []
    },
    '2': {
      id: 2,
      title: '美国总统发表国情咨文演讲',
      summary: '美国总统在国会发表年度国情咨文，阐述未来一年的政策方向和施政重点。',
      content: `美国总统在国会联席会议上发表了年度国情咨文演讲，向全国民众阐述了未来一年的政策方向和施政重点。

在经济方面，总统强调了继续推动就业增长、控制通货膨胀的重要性。他提出了一系列措施，包括加大对基础设施的投资、支持制造业回流、降低家庭能源成本等。

在外交政策上，总统重申了与盟友加强合作、应对全球挑战的承诺。他特别提到了气候变化、网络安全、地区冲突等议题，表示美国将在国际舞台上发挥领导作用。

演讲结束后，国会两院议员对总统的施政纲领反应不一。支持者认为这些政策将有助于国家发展，而反对者则对某些提议提出了质疑。

分析人士指出，这次国情咨文演讲将为即将到来的选举定下基调，各党派将围绕这些政策议题展开激烈辩论。`,
      published_at: '2024-01-15 09:00:00',
      source_name: 'CNN',
      source_url: 'https://edition.cnn.com/politics/2024/01/15/state-of-the-union',
      country_code: 'US',
      country_name: '美国',
      images: [
        { url: 'https://picsum.photos/800/400?random=3', caption: '总统在国会发表演讲', is_cover: true },
      ],
      videos: [
        { url: 'https://www.youtube.com/embed/dQw4w9WgXcQ', type: 'youtube' }
      ]
    },
    '3': {
      id: 3,
      title: '日本经济持续增长',
      summary: '日本第四季度GDP增长超预期，出口和内需双双回暖。',
      content: `日本内阁府公布的数据显示，日本第四季度国内生产总值（GDP）环比增长0.6%，按年率计算增长2.4%，超出市场预期。

数据显示，出口和内需是推动经济增长的主要动力。受益于全球需求回暖，日本汽车、电子产品等出口表现强劲。同时，国内消费也在稳步恢复，零售销售额连续数月保持增长。

日本央行表示，经济持续复苏为货币政策正常化创造了条件。市场普遍预期，央行可能在年内结束负利率政策。

分析人士认为，尽管面临人口老龄化、劳动力短缺等结构性挑战，但日本经济正在走出长期停滞的阴影。政府推出的经济刺激措施和企业改革正在发挥作用。

不过，也有专家提醒，全球经济不确定性、地缘政治风险等因素可能给日本经济复苏带来挑战。`,
      published_at: '2024-01-15 08:30:00',
      source_name: 'NHK',
      source_url: 'https://www3.nhk.or.jp/news/20240115/economy',
      country_code: 'JP',
      country_name: '日本',
      images: [
        { url: 'https://picsum.photos/800/400?random=4', caption: '东京街头景象', is_cover: true },
        { url: 'https://picsum.photos/800/400?random=5', caption: '日本制造业工厂', is_cover: false },
      ],
      videos: []
    }
  };
  
  // 返回对应ID的详情，如果没有则返回第一个
  return mockDetails[newsId] || mockDetails['1'];
}

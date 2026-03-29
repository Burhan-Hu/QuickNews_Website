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
    return parseNewsXML(xmlText);
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
 * 获取国家新闻统计 (用于热力图)
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
    
    return stats;
  } catch (error) {
    console.error('Get country stats error:', error);
    // 返回模拟数据
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
}

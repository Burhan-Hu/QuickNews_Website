/**
 * API 工具函数
 * 封装与后端的所有交互
 */

// API 基础 URL：开发环境使用 localhost，生产环境使用相对路径（同域）
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''; // 空字符串表示使用相对路径，适用于前后端同域部署

/**
 * 搜索新闻
 * @param {string} query - 搜索关键词
 * @param {number} maxResults - 最大结果数
 * @returns {Promise<Array>} 新闻列表
 */
export async function searchNews(query, maxResults = 20) {
  try {
    const response = await fetch(
      `${API_BASE_URL}/sru?query=${encodeURIComponent(query)}&maximumRecords=${maxResults}`
    );
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const xmlText = await response.text();
    return parseSRUResponse(xmlText);
  } catch (error) {
    console.error('Search news error:', error);
    throw error;
  }
}

/**
 * 获取最新新闻
 * @param {number} maxResults - 最大结果数
 * @returns {Promise<Array>} 新闻列表
 */
export async function getLatestNews(maxResults = 20) {
  try {
    const response = await fetch(
      `${API_BASE_URL}/sru?query=*&maximumRecords=${maxResults}`
    );
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const xmlText = await response.text();
    return parseSRUResponse(xmlText);
  } catch (error) {
    console.error('Get latest news error:', error);
    throw error;
  }
}

/**
 * 获取分类列表
 * @returns {Promise<Array>} 分类列表
 */
export async function getCategories() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/categories`);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Get categories error:', error);
    // 返回默认分类作为降级方案
    return [
      { category_id: 1, category_name: '科技', category_code: 'tech', color_code: '#3498db' },
      { category_id: 2, category_name: '政治', category_code: 'politics', color_code: '#e74c3c' },
      { category_id: 3, category_name: '经济', category_code: 'economy', color_code: '#2ecc71' },
      { category_id: 4, category_name: '军事', category_code: 'military', color_code: '#9b59b6' },
      { category_id: 5, category_name: '文化', category_code: 'culture', color_code: '#f39c12' },
      { category_id: 6, category_name: '体育', category_code: 'sports', color_code: '#1abc9c' },
      { category_id: 7, category_name: '社会', category_code: 'society', color_code: '#34495e' },
      { category_id: 8, category_name: '国际', category_code: 'international', color_code: '#e67e22' },
    ];
  }
}

/**
 * 获取指定分类下的新闻
 * @param {string} categoryCode - 分类代码
 * @param {number} maxResults - 最大结果数
 * @returns {Promise<Array>} 新闻列表
 */
export async function getNewsByCategory(categoryCode, maxResults = 20) {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/news/category/${encodeURIComponent(categoryCode)}?limit=${maxResults}`
    );
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Get news by category error:', error);
    throw error;
  }
}

/**
 * 获取新闻详情
 * @param {number} newsId - 新闻ID
 * @returns {Promise<Object>} 新闻详情
 */
export async function getNewsDetail(newsId) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/news/${newsId}`);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Get news detail error:', error);
    throw error;
  }
}

/**
 * 获取国家统计
 * @returns {Promise<Object>} 国家统计对象 {CN: 45, US: 38, ...}
 */
export async function getCountryStatsFromAPI() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/stats/countries`);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Get country stats error:', error);
    return {};
  }
}

/**
 * 获取热门话题
 * @returns {Promise<Array>} 热门话题列表 [{name: '...', count: 10}, ...]
 */
export async function getHotTopics() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/stats/topics`);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Get hot topics error:', error);
    return [];
  }
}

/**
 * 获取新闻来源
 * @returns {Promise<Array>} 来源列表
 */
export async function getSources() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/sources`);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Get sources error:', error);
    return [];
  }
}

/**
 * 解析 SRU XML 响应
 * @param {string} xmlText - XML 文本
 * @returns {Array} 解析后的新闻列表
 */
function parseSRUResponse(xmlText) {
  try {
    const parser = new DOMParser();
    const xmlDoc = parser.parseFromString(xmlText, 'text/xml');
    
    // 检查解析错误
    const parserError = xmlDoc.querySelector('parsererror');
    if (parserError) {
      console.error('XML parse error:', parserError.textContent);
      return [];
    }
    
    const records = xmlDoc.querySelectorAll('record');
    const newsList = [];
    
    records.forEach((record) => {
      const recordData = record.querySelector('recordData');
      if (!recordData) return;
      
      const newsElem = recordData.querySelector('news');
      if (!newsElem) return;
      
      const id = newsElem.getAttribute('id') || '';
      const titleElem = newsElem.querySelector('title');
      const summaryElem = newsElem.querySelector('summary');
      const metadataElem = newsElem.querySelector('metadata');
      
      const title = titleElem ? extractCDATAOrText(titleElem) : '';
      const summary = summaryElem ? extractCDATAOrText(summaryElem) : '';
      const country = metadataElem ? metadataElem.querySelector('country')?.textContent || '' : '';
      
      // 从 record 中获取时间
      const time = record.querySelector('recordPosition')?.textContent || '';
      
      newsList.push({
        id: parseInt(id) || newsList.length + 1,
        title: title,
        summary: summary,
        country: country,
        time: time,
      });
    });
    
    return newsList;
  } catch (error) {
    console.error('Parse SRU response error:', error);
    return [];
  }
}

/**
 * 提取 CDATA 或文本内容
 * @param {Element} element - DOM 元素
 * @returns {string} 文本内容
 */
function extractCDATAOrText(element) {
  if (!element) return '';
  
  // 尝试获取 CDATA 内容
  for (let node of element.childNodes) {
    if (node.nodeType === Node.CDATA_SECTION_NODE) {
      return node.textContent.trim();
    }
  }
  
  // 回退到普通文本
  return element.textContent.trim();
}

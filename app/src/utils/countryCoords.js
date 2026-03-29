/**
 * 国家坐标映射表
 * 用于 3D 地球热力图定位
 * 坐标格式: { lat: 纬度, lon: 经度, name: 中文名, emoji: 国旗emoji }
 */

export const countryCoords = {
  // 亚洲
  'CN': { lat: 35.8617, lon: 104.1954, name: '中国', emoji: '🇨🇳' },
  'JP': { lat: 36.2048, lon: 138.2529, name: '日本', emoji: '🇯🇵' },
  'IN': { lat: 20.5937, lon: 78.9629, name: '印度', emoji: '🇮🇳' },
  'KR': { lat: 35.9078, lon: 127.7669, name: '韩国', emoji: '🇰🇷' },
  'ID': { lat: -0.7893, lon: 113.9213, name: '印度尼西亚', emoji: '🇮🇩' },
  'TH': { lat: 15.8700, lon: 100.9925, name: '泰国', emoji: '🇹🇭' },
  'VN': { lat: 14.0583, lon: 108.2772, name: '越南', emoji: '🇻🇳' },
  'MY': { lat: 4.2105, lon: 101.9758, name: '马来西亚', emoji: '🇲🇾' },
  'PH': { lat: 12.8797, lon: 121.7740, name: '菲律宾', emoji: '🇵🇭' },
  'SG': { lat: 1.3521, lon: 103.8198, name: '新加坡', emoji: '🇸🇬' },
  'TR': { lat: 38.9637, lon: 35.2433, name: '土耳其', emoji: '🇹🇷' },
  'IR': { lat: 32.4279, lon: 53.6880, name: '伊朗', emoji: '🇮🇷' },
  'SA': { lat: 23.8859, lon: 45.0792, name: '沙特阿拉伯', emoji: '🇸🇦' },
  'IL': { lat: 31.0461, lon: 34.8516, name: '以色列', emoji: '🇮🇱' },
  'AE': { lat: 23.4241, lon: 53.8478, name: '阿联酋', emoji: '🇦🇪' },
  
  // 欧洲
  'RU': { lat: 61.5240, lon: 105.3188, name: '俄罗斯', emoji: '🇷🇺' },
  'GB': { lat: 55.3781, lon: -3.4360, name: '英国', emoji: '🇬🇧' },
  'DE': { lat: 51.1657, lon: 10.4515, name: '德国', emoji: '🇩🇪' },
  'FR': { lat: 46.2276, lon: 2.2137, name: '法国', emoji: '🇫🇷' },
  'IT': { lat: 41.8719, lon: 12.5674, name: '意大利', emoji: '🇮🇹' },
  'ES': { lat: 40.4637, lon: -3.7492, name: '西班牙', emoji: '🇪🇸' },
  'UA': { lat: 48.3794, lon: 31.1656, name: '乌克兰', emoji: '🇺🇦' },
  'PL': { lat: 51.9194, lon: 19.1451, name: '波兰', emoji: '🇵🇱' },
  'NL': { lat: 52.1326, lon: 5.2913, name: '荷兰', emoji: '🇳🇱' },
  'BE': { lat: 50.5039, lon: 4.4699, name: '比利时', emoji: '🇧🇪' },
  'SE': { lat: 60.1282, lon: 18.6435, name: '瑞典', emoji: '🇸🇪' },
  'NO': { lat: 60.4720, lon: 8.4689, name: '挪威', emoji: '🇳🇴' },
  'FI': { lat: 61.9241, lon: 25.7482, name: '芬兰', emoji: '🇫🇮' },
  'DK': { lat: 56.2639, lon: 9.5018, name: '丹麦', emoji: '🇩🇰' },
  'CH': { lat: 46.8182, lon: 8.2275, name: '瑞士', emoji: '🇨🇭' },
  'AT': { lat: 47.5162, lon: 14.5501, name: '奥地利', emoji: '🇦🇹' },
  'GR': { lat: 39.0742, lon: 21.8243, name: '希腊', emoji: '🇬🇷' },
  'PT': { lat: 39.3999, lon: -8.2245, name: '葡萄牙', emoji: '🇵🇹' },
  'CZ': { lat: 49.8175, lon: 15.4730, name: '捷克', emoji: '🇨🇿' },
  'HU': { lat: 47.1625, lon: 19.5033, name: '匈牙利', emoji: '🇭🇺' },
  'RO': { lat: 45.9432, lon: 24.9668, name: '罗马尼亚', emoji: '🇷🇴' },
  
  // 北美洲
  'US': { lat: 37.0902, lon: -95.7129, name: '美国', emoji: '🇺🇸' },
  'CA': { lat: 56.1304, lon: -106.3468, name: '加拿大', emoji: '🇨🇦' },
  'MX': { lat: 23.6345, lon: -102.5528, name: '墨西哥', emoji: '🇲🇽' },
  'CU': { lat: 21.5218, lon: -77.7812, name: '古巴', emoji: '🇨🇺' },
  
  // 南美洲
  'BR': { lat: -14.2350, lon: -51.9253, name: '巴西', emoji: '🇧🇷' },
  'AR': { lat: -38.4161, lon: -63.6167, name: '阿根廷', emoji: '🇦🇷' },
  'CO': { lat: 4.5709, lon: -74.2973, name: '哥伦比亚', emoji: '🇨🇴' },
  'PE': { lat: -9.1900, lon: -75.0152, name: '秘鲁', emoji: '🇵🇪' },
  'CL': { lat: -35.6751, lon: -71.5430, name: '智利', emoji: '🇨🇱' },
  'VE': { lat: 6.4238, lon: -66.5897, name: '委内瑞拉', emoji: '🇻🇪' },
  
  // 非洲
  'ZA': { lat: -30.5595, lon: 22.9375, name: '南非', emoji: '🇿🇦' },
  'EG': { lat: 26.8206, lon: 30.8025, name: '埃及', emoji: '🇪🇬' },
  'NG': { lat: 9.0820, lon: 8.6753, name: '尼日利亚', emoji: '🇳🇬' },
  'KE': { lat: -0.0236, lon: 37.9062, name: '肯尼亚', emoji: '🇰🇪' },
  'ET': { lat: 9.1450, lon: 40.4897, name: '埃塞俄比亚', emoji: '🇪🇹' },
  'MA': { lat: 31.7917, lon: -7.0926, name: '摩洛哥', emoji: '🇲🇦' },
  'DZ': { lat: 28.0339, lon: 1.6596, name: '阿尔及利亚', emoji: '🇩🇿' },
  
  // 大洋洲
  'AU': { lat: -25.2744, lon: 133.7751, name: '澳大利亚', emoji: '🇦🇺' },
  'NZ': { lat: -40.9006, lon: 174.8869, name: '新西兰', emoji: '🇳🇿' },
  'FJ': { lat: -17.7134, lon: 178.0650, name: '斐济', emoji: '🇫🇯' },
  'PG': { lat: -6.3150, lon: 143.9555, name: '巴布亚新几内亚', emoji: '🇵🇬' },
};

/**
 * 将经纬度转换为 3D 球面坐标
 * @param {number} lat - 纬度 (-90 to 90)
 * @param {number} lon - 经度 (-180 to 180)
 * @param {number} radius - 球体半径
 * @returns {Object} {x, y, z} 3D坐标
 */
export function latLonToVector3(lat, lon, radius = 5) {
  const phi = (90 - lat) * (Math.PI / 180);
  const theta = (lon + 180) * (Math.PI / 180);
  
  const x = -(radius * Math.sin(phi) * Math.cos(theta));
  const z = radius * Math.sin(phi) * Math.sin(theta);
  const y = radius * Math.cos(phi);
  
  return { x, y, z };
}

/**
 * 获取国家 3D 坐标
 * @param {string} countryCode - 国家代码
 * @param {number} radius - 球体半径
 * @returns {Object|null} {x, y, z} 3D坐标
 */
export function getCountryPosition(countryCode, radius = 5) {
  const country = countryCoords[countryCode.toUpperCase()];
  if (!country) return null;
  
  return latLonToVector3(country.lat, country.lon, radius);
}

/**
 * 获取国家信息
 * @param {string} countryCode - 国家代码
 * @returns {Object|null} 国家信息
 */
export function getCountryInfo(countryCode) {
  return countryCoords[countryCode.toUpperCase()] || null;
}

/**
 * 获取所有国家代码
 * @returns {Array} 国家代码数组
 */
export function getAllCountryCodes() {
  return Object.keys(countryCoords);
}

/**
 * 获取热门国家 (Top 20)
 * @returns {Array} 热门国家代码数组
 */
export function getTopCountries() {
  return ['CN', 'US', 'JP', 'GB', 'RU', 'IN', 'DE', 'FR', 'BR', 'CA', 
          'AU', 'KR', 'IT', 'ES', 'MX', 'ID', 'TR', 'SA', 'ZA', 'EG'];
}

/**
 * 获取热力图颜色
 * @param {number} value - 新闻数量
 * @param {number} max - 最大值 (用于归一化)
 * @returns {string} CSS颜色值
 */
export function getHeatmapColor(value, max = 50) {
  const ratio = Math.min(value / max, 1);
  
  // 从绿色到黄色到红色的渐变
  if (ratio < 0.33) {
    // 绿色到黄色
    const r = Math.round(46 + (241 - 46) * (ratio / 0.33));
    const g = Math.round(204 + (196 - 204) * (ratio / 0.33));
    const b = Math.round(113 + (15 - 113) * (ratio / 0.33));
    return `rgb(${r}, ${g}, ${b})`;
  } else if (ratio < 0.66) {
    // 黄色到橙色
    const localRatio = (ratio - 0.33) / 0.33;
    const r = Math.round(241 + (230 - 241) * localRatio);
    const g = Math.round(196 + (126 - 196) * localRatio);
    const b = Math.round(15 + (34 - 15) * localRatio);
    return `rgb(${r}, ${g}, ${b})`;
  } else {
    // 橙色到红色
    const localRatio = (ratio - 0.66) / 0.34;
    const r = Math.round(230 + (231 - 230) * localRatio);
    const g = Math.round(126 + (76 - 126) * localRatio);
    const b = Math.round(34 + (60 - 34) * localRatio);
    return `rgb(${r}, ${g}, ${b})`;
  }
}

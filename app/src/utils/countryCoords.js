/**
 * 国家坐标映射表
 * 用于 3D 地球热力图定位
 * 坐标格式: { lat: 纬度, lon: 经度, name: 中文名, emoji: 国旗emoji }
 * 
 * 数据来源: db/schema.sql 中的 countries 表定义
 * 包含所有 200+ 个国家/地区
 */

export const countryCoords = {
  // ==================== 亚洲 (49个国家/地区) ====================
  'CN': { lat: 35.8617, lon: 104.1954, name: '中国', emoji: '🇨🇳' },
  'IN': { lat: 20.5937, lon: 78.9629, name: '印度', emoji: '🇮🇳' },
  'ID': { lat: -0.7893, lon: 113.9213, name: '印度尼西亚', emoji: '🇮🇩' },
  'PK': { lat: 30.3753, lon: 69.3451, name: '巴基斯坦', emoji: '🇵🇰' },
  'BD': { lat: 23.6850, lon: 90.3563, name: '孟加拉国', emoji: '🇧🇩' },
  'JP': { lat: 36.2048, lon: 138.2529, name: '日本', emoji: '🇯🇵' },
  'PH': { lat: 12.8797, lon: 121.7740, name: '菲律宾', emoji: '🇵🇭' },
  'VN': { lat: 14.0583, lon: 108.2772, name: '越南', emoji: '🇻🇳' },
  'TR': { lat: 38.9637, lon: 35.2433, name: '土耳其', emoji: '🇹🇷' },
  'IR': { lat: 32.4279, lon: 53.6880, name: '伊朗', emoji: '🇮🇷' },
  'TH': { lat: 15.8700, lon: 100.9925, name: '泰国', emoji: '🇹🇭' },
  'MM': { lat: 21.9162, lon: 95.9560, name: '缅甸', emoji: '🇲🇲' },
  'KR': { lat: 35.9078, lon: 127.7669, name: '韩国', emoji: '🇰🇷' },
  'IQ': { lat: 33.2232, lon: 43.6793, name: '伊拉克', emoji: '🇮🇶' },
  'SA': { lat: 23.8859, lon: 45.0792, name: '沙特阿拉伯', emoji: '🇸🇦' },
  'UZ': { lat: 41.3775, lon: 64.5853, name: '乌兹别克斯坦', emoji: '🇺🇿' },
  'MY': { lat: 4.2105, lon: 101.9758, name: '马来西亚', emoji: '🇲🇾' },
  'AF': { lat: 33.9391, lon: 67.7100, name: '阿富汗', emoji: '🇦🇫' },
  'NP': { lat: 28.3949, lon: 84.1240, name: '尼泊尔', emoji: '🇳🇵' },
  'YE': { lat: 15.5527, lon: 48.5164, name: '也门', emoji: '🇾🇪' },
  'KP': { lat: 40.3399, lon: 127.5101, name: '朝鲜', emoji: '🇰🇵' },
  'LK': { lat: 7.8731, lon: 80.7718, name: '斯里兰卡', emoji: '🇱🇰' },
  'KZ': { lat: 48.0196, lon: 66.9237, name: '哈萨克斯坦', emoji: '🇰🇿' },
  'SY': { lat: 34.8021, lon: 38.9968, name: '叙利亚', emoji: '🇸🇾' },
  'KH': { lat: 12.5657, lon: 104.9910, name: '柬埔寨', emoji: '🇰🇭' },
  'JO': { lat: 30.5852, lon: 36.2384, name: '约旦', emoji: '🇯🇴' },
  'AZ': { lat: 40.1431, lon: 47.5769, name: '阿塞拜疆', emoji: '🇦🇿' },
  'AE': { lat: 23.4241, lon: 53.8478, name: '阿联酋', emoji: '🇦🇪' },
  'TJ': { lat: 38.8610, lon: 71.2761, name: '塔吉克斯坦', emoji: '🇹🇯' },
  'IL': { lat: 31.0461, lon: 34.8516, name: '以色列', emoji: '🇮🇱' },
  'LA': { lat: 19.8563, lon: 102.4955, name: '老挝', emoji: '🇱🇦' },
  'LB': { lat: 33.8547, lon: 35.8623, name: '黎巴嫩', emoji: '🇱🇧' },
  'SG': { lat: 1.3521, lon: 103.8198, name: '新加坡', emoji: '🇸🇬' },
  'OM': { lat: 21.4735, lon: 55.9754, name: '阿曼', emoji: '🇴🇲' },
  'KW': { lat: 29.3117, lon: 47.4818, name: '科威特', emoji: '🇰🇼' },
  'GE': { lat: 42.3154, lon: 43.3569, name: '格鲁吉亚', emoji: '🇬🇪' },
  'MN': { lat: 46.8625, lon: 103.8467, name: '蒙古', emoji: '🇲🇳' },
  'AM': { lat: 40.0691, lon: 45.0382, name: '亚美尼亚', emoji: '🇦🇲' },
  'QA': { lat: 25.3548, lon: 51.1839, name: '卡塔尔', emoji: '🇶🇦' },
  'BH': { lat: 26.0667, lon: 50.5577, name: '巴林', emoji: '🇧🇭' },
  'TL': { lat: -8.8742, lon: 125.7275, name: '东帝汶', emoji: '🇹🇱' },
  'CY': { lat: 35.1264, lon: 33.4299, name: '塞浦路斯', emoji: '🇨🇾' },
  'BT': { lat: 27.5142, lon: 90.4336, name: '不丹', emoji: '🇧🇹' },
  'MV': { lat: 3.2028, lon: 73.2207, name: '马尔代夫', emoji: '🇲🇻' },
  'BN': { lat: 4.5353, lon: 114.7277, name: '文莱', emoji: '🇧🇳' },
  'KG': { lat: 41.2044, lon: 74.7661, name: '吉尔吉斯斯坦', emoji: '🇰🇬' },
  'TM': { lat: 38.9697, lon: 59.5563, name: '土库曼斯坦', emoji: '🇹🇲' },
  'PS': { lat: 31.9522, lon: 35.2332, name: '巴勒斯坦', emoji: '🇵🇸' },
  'TW': { lat: 23.6978, lon: 120.9605, name: '中国台湾省', emoji: '🇨🇳' },
  'HK': { lat: 22.3193, lon: 114.1694, name: '中国香港', emoji: '🇨🇳' },
  'MO': { lat: 22.1987, lon: 113.5439, name: '中国澳门', emoji: '🇨🇳' },

  // ==================== 欧洲 (44个国家/地区) ====================
  'RU': { lat: 61.5240, lon: 105.3188, name: '俄罗斯', emoji: '🇷🇺' },
  'DE': { lat: 51.1657, lon: 10.4515, name: '德国', emoji: '🇩🇪' },
  'GB': { lat: 55.3781, lon: -3.4360, name: '英国', emoji: '🇬🇧' },
  'FR': { lat: 46.2276, lon: 2.2137, name: '法国', emoji: '🇫🇷' },
  'IT': { lat: 41.8719, lon: 12.5674, name: '意大利', emoji: '🇮🇹' },
  'ES': { lat: 40.4637, lon: -3.7492, name: '西班牙', emoji: '🇪🇸' },
  'UA': { lat: 48.3794, lon: 31.1656, name: '乌克兰', emoji: '🇺🇦' },
  'PL': { lat: 51.9194, lon: 19.1451, name: '波兰', emoji: '🇵🇱' },
  'RO': { lat: 45.9432, lon: 24.9668, name: '罗马尼亚', emoji: '🇷🇴' },
  'NL': { lat: 52.1326, lon: 5.2913, name: '荷兰', emoji: '🇳🇱' },
  'BE': { lat: 50.5039, lon: 4.4699, name: '比利时', emoji: '🇧🇪' },
  'CZ': { lat: 49.8175, lon: 15.4730, name: '捷克', emoji: '🇨🇿' },
  'GR': { lat: 39.0742, lon: 21.8243, name: '希腊', emoji: '🇬🇷' },
  'PT': { lat: 39.3999, lon: -8.2245, name: '葡萄牙', emoji: '🇵🇹' },
  'SE': { lat: 60.1282, lon: 18.6435, name: '瑞典', emoji: '🇸🇪' },
  'HU': { lat: 47.1625, lon: 19.5033, name: '匈牙利', emoji: '🇭🇺' },
  'BY': { lat: 53.7098, lon: 27.9534, name: '白俄罗斯', emoji: '🇧🇾' },
  'AT': { lat: 47.5162, lon: 14.5501, name: '奥地利', emoji: '🇦🇹' },
  'CH': { lat: 46.8182, lon: 8.2275, name: '瑞士', emoji: '🇨🇭' },
  'RS': { lat: 44.0165, lon: 21.0059, name: '塞尔维亚', emoji: '🇷🇸' },
  'BG': { lat: 42.7339, lon: 25.4858, name: '保加利亚', emoji: '🇧🇬' },
  'DK': { lat: 56.2639, lon: 9.5018, name: '丹麦', emoji: '🇩🇰' },
  'FI': { lat: 61.9241, lon: 25.7482, name: '芬兰', emoji: '🇫🇮' },
  'NO': { lat: 60.4720, lon: 8.4689, name: '挪威', emoji: '🇳🇴' },
  'SK': { lat: 48.6690, lon: 19.6990, name: '斯洛伐克', emoji: '🇸🇰' },
  'IE': { lat: 53.1424, lon: -7.6921, name: '爱尔兰', emoji: '🇮🇪' },
  'HR': { lat: 45.1000, lon: 15.2000, name: '克罗地亚', emoji: '🇭🇷' },
  'BA': { lat: 43.9159, lon: 17.6791, name: '波黑', emoji: '🇧🇦' },
  'AL': { lat: 41.1533, lon: 20.1683, name: '阿尔巴尼亚', emoji: '🇦🇱' },
  'LT': { lat: 55.1694, lon: 23.8813, name: '立陶宛', emoji: '🇱🇹' },
  'SI': { lat: 46.1512, lon: 14.9955, name: '斯洛文尼亚', emoji: '🇸🇮' },
  'LV': { lat: 56.8796, lon: 24.6032, name: '拉脱维亚', emoji: '🇱🇻' },
  'EE': { lat: 58.5953, lon: 25.0136, name: '爱沙尼亚', emoji: '🇪🇪' },
  'MD': { lat: 47.4116, lon: 28.3699, name: '摩尔多瓦', emoji: '🇲🇩' },
  'LU': { lat: 49.8153, lon: 6.1296, name: '卢森堡', emoji: '🇱🇺' },
  'MT': { lat: 35.9375, lon: 14.3754, name: '马耳他', emoji: '🇲🇹' },
  'IS': { lat: 64.9631, lon: -19.0208, name: '冰岛', emoji: '🇮🇸' },
  'MK': { lat: 41.6086, lon: 21.7453, name: '北马其顿', emoji: '🇲🇰' },
  'ME': { lat: 42.7087, lon: 19.3744, name: '黑山', emoji: '🇲🇪' },
  'AD': { lat: 42.5063, lon: 1.5218, name: '安道尔', emoji: '🇦🇩' },
  'LI': { lat: 47.1660, lon: 9.5554, name: '列支敦士登', emoji: '🇱🇮' },
  'MC': { lat: 43.7384, lon: 7.4246, name: '摩纳哥', emoji: '🇲🇨' },
  'SM': { lat: 43.9424, lon: 12.4578, name: '圣马力诺', emoji: '🇸🇲' },
  'VA': { lat: 41.9029, lon: 12.4534, name: '梵蒂冈', emoji: '🇻🇦' },
  'XK': { lat: 42.6026, lon: 20.9030, name: '科索沃', emoji: '🇽🇰' },

  // ==================== 非洲 (54个国家/地区) ====================
  'NG': { lat: 9.0820, lon: 8.6753, name: '尼日利亚', emoji: '🇳🇬' },
  'ET': { lat: 9.1450, lon: 40.4897, name: '埃塞俄比亚', emoji: '🇪🇹' },
  'EG': { lat: 26.8206, lon: 30.8025, name: '埃及', emoji: '🇪🇬' },
  'CD': { lat: -4.0383, lon: 21.7587, name: '刚果(金)', emoji: '🇨🇩' },
  'TZ': { lat: -6.3690, lon: 34.8888, name: '坦桑尼亚', emoji: '🇹🇿' },
  'ZA': { lat: -30.5595, lon: 22.9375, name: '南非', emoji: '🇿🇦' },
  'KE': { lat: -0.0236, lon: 37.9062, name: '肯尼亚', emoji: '🇰🇪' },
  'UG': { lat: 1.3733, lon: 32.2903, name: '乌干达', emoji: '🇺🇬' },
  'SD': { lat: 12.8628, lon: 30.2176, name: '苏丹', emoji: '🇸🇩' },
  'DZ': { lat: 28.0339, lon: 1.6596, name: '阿尔及利亚', emoji: '🇩🇿' },
  'MA': { lat: 31.7917, lon: -7.0926, name: '摩洛哥', emoji: '🇲🇦' },
  'AO': { lat: -11.2027, lon: 17.8739, name: '安哥拉', emoji: '🇦🇴' },
  'GH': { lat: 7.9465, lon: -1.0232, name: '加纳', emoji: '🇬🇭' },
  'MZ': { lat: -18.6657, lon: 35.5296, name: '莫桑比克', emoji: '🇲🇿' },
  'MG': { lat: -18.7669, lon: 46.8691, name: '马达加斯加', emoji: '🇲🇬' },
  'CM': { lat: 7.3697, lon: 12.3547, name: '喀麦隆', emoji: '🇨🇲' },
  'CI': { lat: 7.5400, lon: -5.5471, name: '科特迪瓦', emoji: '🇨🇮' },
  'NE': { lat: 17.6078, lon: 8.0817, name: '尼日尔', emoji: '🇳🇪' },
  'BF': { lat: 12.2383, lon: -1.5616, name: '布基纳法索', emoji: '🇧🇫' },
  'ML': { lat: 17.5707, lon: -3.9962, name: '马里', emoji: '🇲🇱' },
  'MW': { lat: -13.2543, lon: 34.3015, name: '马拉维', emoji: '🇲🇼' },
  'ZM': { lat: -13.1339, lon: 27.8493, name: '赞比亚', emoji: '🇿🇲' },
  'SO': { lat: 5.1521, lon: 46.1996, name: '索马里', emoji: '🇸🇴' },
  'SN': { lat: 14.4974, lon: -14.4524, name: '塞内加尔', emoji: '🇸🇳' },
  'TD': { lat: 15.4542, lon: 18.7322, name: '乍得', emoji: '🇹🇩' },
  'ZW': { lat: -19.0154, lon: 29.1549, name: '津巴布韦', emoji: '🇿🇼' },
  'GN': { lat: 9.9456, lon: -9.6966, name: '几内亚', emoji: '🇬🇳' },
  'RW': { lat: -1.9403, lon: 29.8739, name: '卢旺达', emoji: '🇷🇼' },
  'SS': { lat: 6.8770, lon: 31.3070, name: '南苏丹', emoji: '🇸🇸' },
  'BJ': { lat: 9.3077, lon: 2.3158, name: '贝宁', emoji: '🇧🇯' },
  'TN': { lat: 33.8869, lon: 9.5375, name: '突尼斯', emoji: '🇹🇳' },
  'BI': { lat: -3.3731, lon: 29.9189, name: '布隆迪', emoji: '🇧🇮' },
  'LS': { lat: -29.6100, lon: 28.2336, name: '莱索托', emoji: '🇱🇸' },
  'TG': { lat: 8.6195, lon: 0.8248, name: '多哥', emoji: '🇹🇬' },
  'SL': { lat: 8.4606, lon: -11.7799, name: '塞拉利昂', emoji: '🇸🇱' },
  'LY': { lat: 26.3351, lon: 17.2283, name: '利比亚', emoji: '🇱🇾' },
  'LR': { lat: 6.4281, lon: -9.4295, name: '利比里亚', emoji: '🇱🇷' },
  'MR': { lat: 21.0079, lon: -10.9408, name: '毛里塔尼亚', emoji: '🇲🇷' },
  'ER': { lat: 15.1794, lon: 39.7823, name: '厄立特里亚', emoji: '🇪🇷' },
  'GM': { lat: 13.4432, lon: -15.3101, name: '冈比亚', emoji: '🇬🇲' },
  'BW': { lat: -22.3285, lon: 24.6849, name: '博茨瓦纳', emoji: '🇧🇼' },
  'GA': { lat: -0.8037, lon: 11.6094, name: '加蓬', emoji: '🇬🇦' },
  'GW': { lat: 11.8037, lon: -15.1804, name: '几内亚比绍', emoji: '🇬🇼' },
  'GQ': { lat: 1.6508, lon: 10.2679, name: '赤道几内亚', emoji: '🇬🇶' },
  'MU': { lat: -20.3484, lon: 57.5522, name: '毛里求斯', emoji: '🇲🇺' },
  'SZ': { lat: -26.5225, lon: 31.4659, name: '斯威士兰', emoji: '🇸🇿' },
  'DJ': { lat: 11.8251, lon: 42.5903, name: '吉布提', emoji: '🇩🇯' },
  'KM': { lat: -11.6520, lon: 43.3726, name: '科摩罗', emoji: '🇰🇲' },
  'CV': { lat: 16.5388, lon: -23.0418, name: '佛得角', emoji: '🇨🇻' },
  'ST': { lat: 0.1864, lon: 6.6131, name: '圣多美和普林西比', emoji: '🇸🇹' },
  'SC': { lat: -4.6796, lon: 55.4920, name: '塞舌尔', emoji: '🇸🇨' },
  'EH': { lat: 24.2155, lon: -12.8858, name: '西撒哈拉', emoji: '🇪🇭' },
  'CG': { lat: -0.2280, lon: 15.8277, name: '刚果(布)', emoji: '🇨🇬' },
  'CF': { lat: 6.6111, lon: 20.9394, name: '中非共和国', emoji: '🇨🇫' },
  'NA': { lat: -22.9576, lon: 18.4904, name: '纳米比亚', emoji: '🇳🇦' },

  // ==================== 北美洲 (23个国家/地区) ====================
  'US': { lat: 37.0902, lon: -95.7129, name: '美国', emoji: '🇺🇸' },
  'CA': { lat: 56.1304, lon: -106.3468, name: '加拿大', emoji: '🇨🇦' },
  'MX': { lat: 23.6345, lon: -102.5528, name: '墨西哥', emoji: '🇲🇽' },
  'GT': { lat: 15.7835, lon: -90.2308, name: '危地马拉', emoji: '🇬🇹' },
  'CU': { lat: 21.5218, lon: -77.7812, name: '古巴', emoji: '🇨🇺' },
  'HT': { lat: 18.9712, lon: -72.2852, name: '海地', emoji: '🇭🇹' },
  'DO': { lat: 18.7357, lon: -70.1627, name: '多米尼加', emoji: '🇩🇴' },
  'HN': { lat: 15.2000, lon: -86.2419, name: '洪都拉斯', emoji: '🇭🇳' },
  'NI': { lat: 12.8654, lon: -85.2072, name: '尼加拉瓜', emoji: '🇳🇮' },
  'CR': { lat: 9.7489, lon: -83.7534, name: '哥斯达黎加', emoji: '🇨🇷' },
  'PA': { lat: 8.5380, lon: -80.7821, name: '巴拿马', emoji: '🇵🇦' },
  'SV': { lat: 13.7942, lon: -88.8965, name: '萨尔瓦多', emoji: '🇸🇻' },
  'BZ': { lat: 17.1899, lon: -88.4976, name: '伯利兹', emoji: '🇧🇿' },
  'JM': { lat: 18.1096, lon: -77.2975, name: '牙买加', emoji: '🇯🇲' },
  'TT': { lat: 10.6918, lon: -61.2225, name: '特立尼达和多巴哥', emoji: '🇹🇹' },
  'BS': { lat: 25.0343, lon: -77.3963, name: '巴哈马', emoji: '🇧🇸' },
  'BB': { lat: 13.1939, lon: -59.5432, name: '巴巴多斯', emoji: '🇧🇧' },
  'GD': { lat: 12.1165, lon: -61.6790, name: '格林纳达', emoji: '🇬🇩' },
  'LC': { lat: 13.9094, lon: -60.9789, name: '圣卢西亚', emoji: '🇱🇨' },
  'VC': { lat: 12.9843, lon: -61.2872, name: '圣文森特和格林纳丁斯', emoji: '🇻🇨' },
  'AG': { lat: 17.0608, lon: -61.7964, name: '安提瓜和巴布达', emoji: '🇦🇬' },
  'KN': { lat: 17.3578, lon: -62.7820, name: '圣基茨和尼维斯', emoji: '🇰🇳' },
  'DM': { lat: 15.4150, lon: -61.3710, name: '多米尼克', emoji: '🇩🇲' },

  // ==================== 南美洲 (12个国家/地区) ====================
  'BR': { lat: -14.2350, lon: -51.9253, name: '巴西', emoji: '🇧🇷' },
  'AR': { lat: -38.4161, lon: -63.6167, name: '阿根廷', emoji: '🇦🇷' },
  'CO': { lat: 4.5709, lon: -74.2973, name: '哥伦比亚', emoji: '🇨🇴' },
  'PE': { lat: -9.1900, lon: -75.0152, name: '秘鲁', emoji: '🇵🇪' },
  'VE': { lat: 6.4238, lon: -66.5897, name: '委内瑞拉', emoji: '🇻🇪' },
  'CL': { lat: -35.6751, lon: -71.5430, name: '智利', emoji: '🇨🇱' },
  'EC': { lat: -1.8312, lon: -78.1834, name: '厄瓜多尔', emoji: '🇪🇨' },
  'BO': { lat: -16.2902, lon: -63.5887, name: '玻利维亚', emoji: '🇧🇴' },
  'PY': { lat: -23.4425, lon: -58.4438, name: '巴拉圭', emoji: '🇵🇾' },
  'UY': { lat: -32.5228, lon: -55.7658, name: '乌拉圭', emoji: '🇺🇾' },
  'GY': { lat: 4.8604, lon: -58.9302, name: '圭亚那', emoji: '🇬🇾' },
  'SR': { lat: 3.9193, lon: -56.0278, name: '苏里南', emoji: '🇸🇷' },

  // ==================== 大洋洲 (14个国家/地区) ====================
  'AU': { lat: -25.2744, lon: 133.7751, name: '澳大利亚', emoji: '🇦🇺' },
  'PG': { lat: -6.3150, lon: 143.9555, name: '巴布亚新几内亚', emoji: '🇵🇬' },
  'NZ': { lat: -40.9006, lon: 174.8869, name: '新西兰', emoji: '🇳🇿' },
  'FJ': { lat: -17.7134, lon: 178.0650, name: '斐济', emoji: '🇫🇯' },
  'SB': { lat: -9.6457, lon: 160.1562, name: '所罗门群岛', emoji: '🇸🇧' },
  'VU': { lat: -15.3767, lon: 166.9592, name: '瓦努阿图', emoji: '🇻🇺' },
  'WS': { lat: -13.7590, lon: -172.1046, name: '萨摩亚', emoji: '🇼🇸' },
  'KI': { lat: -3.3704, lon: -168.7340, name: '基里巴斯', emoji: '🇰🇮' },
  'TO': { lat: -21.1790, lon: -175.1982, name: '汤加', emoji: '🇹🇴' },
  'FM': { lat: 7.4256, lon: 150.5508, name: '密克罗尼西亚联邦', emoji: '🇫🇲' },
  'PW': { lat: 7.5150, lon: 134.5825, name: '帕劳', emoji: '🇵🇼' },
  'MH': { lat: 11.8251, lon: 162.1836, name: '马绍尔群岛', emoji: '🇲🇭' },
  'NR': { lat: -0.5228, lon: 166.9315, name: '瑙鲁', emoji: '🇳🇷' },
  'TV': { lat: -7.1095, lon: 177.6493, name: '图瓦卢', emoji: '🇹🇻' },

  // ==================== 其他地区与属地 (35个) ====================
  'GL': { lat: 71.7069, lon: -42.6043, name: '格陵兰', emoji: '🇬🇱' },
  'PR': { lat: 18.2208, lon: -66.5901, name: '波多黎各', emoji: '🇵🇷' },
  'GU': { lat: 13.4443, lon: 144.7937, name: '关岛', emoji: '🇬🇺' },
  'VI': { lat: 18.3358, lon: -64.8963, name: '美属维尔京群岛', emoji: '🇻🇮' },
  'AS': { lat: -14.2710, lon: -170.1322, name: '美属萨摩亚', emoji: '🇦🇸' },
  'KY': { lat: 19.3138, lon: -81.2546, name: '开曼群岛', emoji: '🇰🇾' },
  'BM': { lat: 32.3078, lon: -64.7505, name: '百慕大', emoji: '🇧🇲' },
  'GI': { lat: 36.1408, lon: -5.3536, name: '直布罗陀', emoji: '🇬🇮' },
  'FO': { lat: 61.8926, lon: -6.9118, name: '法罗群岛', emoji: '🇫🇴' },
  'AX': { lat: 60.1785, lon: 19.9156, name: '奥兰群岛', emoji: '🇦🇽' },
  'SJ': { lat: 77.5536, lon: 23.6703, name: '斯瓦尔巴和扬马延', emoji: '🇸🇯' },
  'RE': { lat: -21.1151, lon: 55.5364, name: '留尼汪', emoji: '🇷🇪' },
  'YT': { lat: -12.8275, lon: 45.1662, name: '马约特', emoji: '🇾🇹' },
  'GP': { lat: 16.2650, lon: -61.5510, name: '瓜德罗普', emoji: '🇬🇵' },
  'MQ': { lat: 14.6415, lon: -61.0242, name: '马提尼克', emoji: '🇲🇶' },
  'GF': { lat: 3.9339, lon: -53.1258, name: '法属圭亚那', emoji: '🇬🇫' },
  'PF': { lat: -17.6797, lon: -149.4068, name: '法属波利尼西亚', emoji: '🇵🇫' },
  'NC': { lat: -20.9043, lon: 165.6180, name: '新喀里多尼亚', emoji: '🇳🇨' },
  'WF': { lat: -13.7688, lon: -177.1561, name: '瓦利斯和富图纳', emoji: '🇼🇫' },
  'PM': { lat: 46.9419, lon: -56.2711, name: '圣皮埃尔和密克隆', emoji: '🇵🇲' },
  'BL': { lat: 17.9000, lon: -62.8333, name: '圣巴泰勒米', emoji: '🇧🇱' },
  'MF': { lat: 18.0826, lon: -63.0523, name: '法属圣马丁', emoji: '🇲🇫' },
  'SX': { lat: 18.0425, lon: -63.0548, name: '荷属圣马丁', emoji: '🇸🇽' },
  'AW': { lat: 12.5211, lon: -69.9683, name: '阿鲁巴', emoji: '🇦🇼' },
  'CW': { lat: 12.1696, lon: -68.9900, name: '库拉索', emoji: '🇨🇼' },
  'BQ': { lat: 12.1784, lon: -68.2385, name: '荷属加勒比区', emoji: '🇧🇶' },
  'AI': { lat: 18.2206, lon: -63.0686, name: '安圭拉', emoji: '🇦🇮' },
  'MS': { lat: 16.7425, lon: -62.1874, name: '蒙特塞拉特', emoji: '🇲🇸' },
  'VG': { lat: 18.4207, lon: -64.6400, name: '英属维尔京群岛', emoji: '🇻🇬' },
  'TC': { lat: 21.6940, lon: -71.7979, name: '特克斯和凯科斯群岛', emoji: '🇹🇨' },
  'FK': { lat: -51.7963, lon: -59.5236, name: '福克兰群岛', emoji: '🇫🇰' },
  'GG': { lat: 49.4657, lon: -2.5853, name: '根西岛', emoji: '🇬🇬' },
  'JE': { lat: 49.2144, lon: -2.1313, name: '泽西岛', emoji: '🇯🇪' },
  'IM': { lat: 54.2361, lon: -4.5481, name: '马恩岛', emoji: '🇮🇲' },
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
  if (!countryCode) return null;
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
  if (!countryCode) return null;
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

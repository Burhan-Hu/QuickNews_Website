/**
 * 新闻可视化页面
 * 左侧 3D 地球热力图，右侧信息面板
 */

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, TrendingUp, Globe, Tag } from 'lucide-react';
import Earth3D from '../components/Earth3D';
import NewsCard from '../components/NewsCard';
import { searchNews, getCountryStatsFromAPI, getHotTopics } from '../utils/api';
import { countryCoords, getHeatmapColor } from '../utils/countryCoords';

export default function Visual() {
  const navigate = useNavigate();
  const [selectedCountry, setSelectedCountry] = useState(null);
  const [heatmapData, setHeatmapData] = useState({});
  const [newsList, setNewsList] = useState([]);
  const [loading, setLoading] = useState(false);
  const [hotTopics, setHotTopics] = useState([]);
  const [dataLoading, setDataLoading] = useState(true);
  
  // 加载热力图数据和热门话题
  useEffect(() => {
    loadData();
  }, []);
  
  // 加载数据
  const loadData = async () => {
    setDataLoading(true);
    try {
      // 并行获取热力图数据和热门话题
      const [stats, topics] = await Promise.all([
        getCountryStatsFromAPI(),
        getHotTopics()
      ]);
      
      setHeatmapData(stats);
      setHotTopics(topics);
      
      console.log('[Visual] 热力图数据:', stats);
      console.log('[Visual] 热门话题:', topics);
    } catch (error) {
      console.error('Load data error:', error);
    } finally {
      setDataLoading(false);
    }
  };
  
  // 处理国家点击
  const handleCountryClick = async (countryCode) => {
    setSelectedCountry(countryCode);
    setLoading(true);
    
    try {
      const news = await searchNews(`country:${countryCode}`, 20);
      setNewsList(news);
    } catch (error) {
      console.error('Search error:', error);
    } finally {
      setLoading(false);
    }
  };
  
  // 处理话题点击
  const handleTopicClick = async (topic) => {
    setLoading(true);
    try {
      const news = await searchNews(`title:${topic}`, 20);
      setNewsList(news);
    } catch (error) {
      console.error('Search error:', error);
    } finally {
      setLoading(false);
    }
  };
  
  // 返回主页
  const handleBack = () => {
    navigate('/');
  };

  // 点击新闻跳转到详情页
  const handleNewsClick = (newsId) => {
    navigate(`/news/${newsId}`);
  };
  
  // 获取地区热度排行
  const getRegionRanking = () => {
    return Object.entries(heatmapData)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10)
      .map(([code, count]) => ({
        code,
        count,
        info: countryCoords[code],
      }))
      .filter(item => item.info);
  };
  
  return (
    <div className="relative w-full h-screen overflow-hidden bg-[#0a0a0f]">
      {/* 左侧地球区域 */}
      <motion.div 
        className="absolute left-0 top-0 w-[60%] h-full z-[1]"
        initial={{ x: '-5%', opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        transition={{ duration: 0.6, ease: 'easeOut' }}
      >
        <Earth3D
          mode="heatmap"
          heatmapData={heatmapData}
          selectedCountry={selectedCountry}
          onCountryClick={handleCountryClick}
          rotationSpeed={0.0003}
          enableControls={true}
          cameraPosition={[2, 0, 14]}
        />
      </motion.div>
      
      {/* 返回按钮 */}
      <motion.button
        className="absolute top-6 left-6 z-20 glass p-3 rounded-full text-white/80 hover:text-white hover:bg-white/10 transition-all"
        onClick={handleBack}
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: 0.5, duration: 0.4 }}
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
      >
        <ArrowLeft size={24} />
      </motion.button>
      
      {/* 右侧信息面板 */}
      <motion.div
        className="absolute right-0 top-0 w-[40%] h-full glass z-10 overflow-hidden"
        initial={{ x: '100%' }}
        animate={{ x: 0 }}
        transition={{ delay: 0.2, duration: 0.6, ease: [0.4, 0, 0.2, 1] }}
      >
        <div className="h-full flex flex-col p-6">
          {/* 面板标题 */}
          <motion.div 
            className="mb-6"
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4, duration: 0.4 }}
          >
            <h2 className="font-['Orbitron'] text-2xl text-white flex items-center gap-2">
              <Globe className="text-[#00d4ff]" size={28} />
              全球新闻热力图
            </h2>
            <p className="text-white/50 text-sm mt-1">
              点击地球上的标记查看各国新闻
            </p>
          </motion.div>
          
          {/* 数据加载指示器 */}
          {dataLoading && (
            <motion.div 
              className="flex items-center justify-center py-4 mb-4"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
            >
              <div className="w-6 h-6 border-2 border-[#00d4ff] border-t-transparent rounded-full animate-spin mr-2" />
              <span className="text-white/60 text-sm">加载数据中...</span>
            </motion.div>
          )}
          
          {/* 内容区域 */}
          <div className="flex-1 overflow-y-auto custom-scrollbar space-y-6">
            {/* 话题热度排行 */}
            <motion.section
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5, duration: 0.4 }}
            >
              <h3 className="text-white/80 font-medium mb-3 flex items-center gap-2">
                <Tag size={18} className="text-[#00d4ff]" />
                热门话题
              </h3>
              <div className="flex flex-wrap gap-2">
                {hotTopics.length > 0 ? (
                  hotTopics.map((topic, index) => (
                    <motion.button
                      key={topic.name}
                      className="px-3 py-1.5 rounded-full glass text-sm text-white/70 hover:text-white hover:border-[#00d4ff]/50 transition-all"
                      onClick={() => handleTopicClick(topic.name)}
                      initial={{ opacity: 0, scale: 0.8 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: 0.6 + index * 0.05, duration: 0.3 }}
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                    >
                      {topic.name}
                      <span className="ml-2 text-[#00d4ff]">{topic.count}</span>
                    </motion.button>
                  ))
                ) : (
                  <span className="text-white/40 text-sm">暂无热门话题数据</span>
                )}
              </div>
            </motion.section>
            
            {/* 地区热度排行 */}
            <motion.section
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.6, duration: 0.4 }}
            >
              <h3 className="text-white/80 font-medium mb-3 flex items-center gap-2">
                <TrendingUp size={18} className="text-[#00d4ff]" />
                地区热度
              </h3>
              <div className="space-y-2">
                {getRegionRanking().length > 0 ? (
                  getRegionRanking().map((item, index) => (
                    <motion.div
                      key={item.code}
                      className={`flex items-center justify-between p-3 rounded-lg glass cursor-pointer transition-all ${
                        selectedCountry === item.code 
                          ? 'border-[#00d4ff]/50 bg-[#00d4ff]/10' 
                          : 'hover:bg-white/5'
                      }`}
                      onClick={() => handleCountryClick(item.code)}
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.7 + index * 0.05, duration: 0.3 }}
                      whileHover={{ scale: 1.02 }}
                    >
                      <div className="flex items-center gap-3">
                        <span className="text-2xl">{item.info.emoji}</span>
                        <span className="text-white/80">{item.info.name}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div 
                          className="w-3 h-3 rounded-full"
                          style={{ backgroundColor: getHeatmapColor(item.count, 50) }}
                        />
                        <span className="text-[#00d4ff] font-medium">{item.count}</span>
                      </div>
                    </motion.div>
                  ))
                ) : (
                  <div className="text-white/40 text-sm py-4 text-center">
                    暂无地区热度数据
                  </div>
                )}
              </div>
            </motion.section>
            
            {/* 新闻列表 */}
            <motion.section
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.7, duration: 0.4 }}
            >
              <h3 className="text-white/80 font-medium mb-3">
                {selectedCountry 
                  ? `${countryCoords[selectedCountry]?.name || selectedCountry} 相关新闻`
                  : '最新新闻'
                }
              </h3>
              
              {loading ? (
                <div className="flex items-center justify-center py-8">
                  <div className="w-8 h-8 border-2 border-[#00d4ff] border-t-transparent rounded-full animate-spin" />
                </div>
              ) : newsList.length > 0 ? (
                <div className="space-y-3">
                  {newsList.map((news, index) => (
                    <NewsCard
                      key={news.id}
                      title={news.title}
                      summary={news.summary}
                      country={news.country}
                      time={news.time}
                      index={index}
                      onClick={() => handleNewsClick(news.id)}
                    />
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-white/40">
                  {selectedCountry 
                    ? '暂无相关新闻，请选择其他国家'
                    : '点击国家或话题查看新闻'
                  }
                </div>
              )}
            </motion.section>
          </div>
        </div>
      </motion.div>
    </div>
  );
}

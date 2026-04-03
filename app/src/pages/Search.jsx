/**
 * 搜索页面
 * 左侧搜索功能面板，右侧地球背景
 */

import React, { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, Search as SearchIcon, Clock, X, Tag } from 'lucide-react';
import Earth3D from '../components/Earth3D';
import NewsCard from '../components/NewsCard';
import { searchNews, getLatestNews, getCategories, getNewsByCategory } from '../utils/api';

export default function Search() {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [newsList, setNewsList] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchHistory, setSearchHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  
  // 分类相关状态
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [categoriesLoading, setCategoriesLoading] = useState(false);
  
  // 加载最新新闻和分类
  useEffect(() => {
    loadLatestNews();
    loadCategories();
    
    // 从本地存储加载搜索历史
    const saved = localStorage.getItem('searchHistory');
    if (saved) {
      try {
        setSearchHistory(JSON.parse(saved));
      } catch (e) {
        console.error('Failed to parse search history:', e);
      }
    }
  }, []);
  
  // 加载分类数据
  const loadCategories = async () => {
    setCategoriesLoading(true);
    try {
      const cats = await getCategories();
      setCategories(cats);
    } catch (error) {
      console.error('Load categories error:', error);
    } finally {
      setCategoriesLoading(false);
    }
  };
  
  // 加载最新新闻
  const loadLatestNews = async () => {
    setLoading(true);
    try {
      const news = await getLatestNews(20);
      setNewsList(news);
    } catch (error) {
      console.error('Load latest news error:', error);
    } finally {
      setLoading(false);
    }
  };
  
  // 执行搜索
  const performSearch = useCallback(async (searchQuery) => {
    if (!searchQuery.trim()) {
      loadLatestNews();
      return;
    }
    
    setLoading(true);
    setShowHistory(false);
    setSelectedCategory(null); // 清除分类选择
    
    try {
      const news = await searchNews(searchQuery, 20);
      setNewsList(news);
      
      // 保存搜索历史
      if (!searchHistory.includes(searchQuery)) {
        const newHistory = [searchQuery, ...searchHistory.slice(0, 9)];
        setSearchHistory(newHistory);
        localStorage.setItem('searchHistory', JSON.stringify(newHistory));
      }
    } catch (error) {
      console.error('Search error:', error);
    } finally {
      setLoading(false);
    }
  }, [searchHistory]);
  
  // 处理搜索提交
  const handleSubmit = (e) => {
    e.preventDefault();
    performSearch(query);
  };
  
  // 处理输入变化 (防抖搜索)
  useEffect(() => {
    const timer = setTimeout(() => {
      if (query.trim()) {
        performSearch(query);
      }
    }, 500);
    
    return () => clearTimeout(timer);
  }, [query, performSearch]);
  
  // 清除搜索
  const handleClear = () => {
    setQuery('');
    setSelectedCategory(null);
    loadLatestNews();
  };
  
  // 从历史记录搜索
  const handleHistoryClick = (term) => {
    setQuery(term);
    setSelectedCategory(null);
    performSearch(term);
  };
  
  // 删除历史记录
  const removeHistoryItem = (term, e) => {
    e.stopPropagation();
    const newHistory = searchHistory.filter(item => item !== term);
    setSearchHistory(newHistory);
    localStorage.setItem('searchHistory', JSON.stringify(newHistory));
  };
  
  // 返回主页
  const handleBack = () => {
    navigate('/', { state: { fromInternal: true } });
  };

  // 点击新闻跳转到详情页
  const handleNewsClick = (newsId) => {
    navigate(`/news/${newsId}`, { state: { fromInternal: true } });
  };
  
  // 处理分类按钮点击
  const handleCategoryClick = async (category) => {
    setLoading(true);
    setSelectedCategory(category);
    setQuery(''); // 清除搜索框内容
    setShowHistory(false);
    
    try {
      const news = await getNewsByCategory(category.category_code, 20);
      setNewsList(news);
    } catch (error) {
      console.error('Load news by category error:', error);
    } finally {
      setLoading(false);
    }
  };
  
  // 获取页面标题
  const getPageTitle = () => {
    if (query) {
      return `"${query}" 的搜索结果`;
    }
    if (selectedCategory) {
      return `${selectedCategory.category_name} 相关新闻`;
    }
    return '最新新闻';
  };
  
  return (
    <div className="relative w-full h-screen overflow-hidden bg-[#0a0a0f]">
      {/* 左侧搜索面板 */}
      <motion.div
        className="absolute left-0 top-0 w-[40%] h-full glass z-10 overflow-hidden"
        initial={{ x: '-100%' }}
        animate={{ x: 0 }}
        transition={{ delay: 0.2, duration: 0.6, ease: [0.4, 0, 0.2, 1] }}
      >
        <div className="h-full flex flex-col p-6">
          {/* 搜索标题 */}
          <motion.div 
            className="mb-6"
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4, duration: 0.4 }}
          >
            <h2 className="font-['Orbitron'] text-2xl text-white flex items-center gap-2">
              <SearchIcon className="text-[#00d4ff]" size={28} />
              新闻搜索
            </h2>
          </motion.div>
          
          {/* 搜索栏 */}
          <motion.form 
            onSubmit={handleSubmit}
            className="relative mb-6"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5, duration: 0.4 }}
          >
            <div className="relative">
              <SearchIcon 
                className="absolute left-4 top-1/2 -translate-y-1/2 text-white/40" 
                size={20} 
              />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onFocus={() => setShowHistory(true)}
                placeholder="输入关键词，支持 title:中国, country:US..."
                className="w-full pl-12 pr-12 py-4 glass rounded-xl text-white placeholder-white/40 focus:outline-none focus:border-[#00d4ff]/50 transition-all"
              />
              {query && (
                <button
                  type="button"
                  onClick={handleClear}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-white/40 hover:text-white transition-colors"
                >
                  <X size={18} />
                </button>
              )}
            </div>
            
            {/* 搜索历史下拉 */}
            {showHistory && searchHistory.length > 0 && (
              <motion.div
                className="absolute top-full left-0 right-0 mt-2 glass rounded-xl overflow-hidden z-30"
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
              >
                <div className="p-2">
                  <div className="text-white/40 text-xs px-3 py-2">搜索历史</div>
                  {searchHistory.map((term, index) => (
                    <motion.div
                      key={term}
                      className="flex items-center justify-between px-3 py-2 rounded-lg hover:bg-white/5 cursor-pointer group"
                      onClick={() => handleHistoryClick(term)}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.03 }}
                    >
                      <div className="flex items-center gap-2 text-white/70 group-hover:text-white">
                        <Clock size={14} />
                        <span>{term}</span>
                      </div>
                      <button
                        onClick={(e) => removeHistoryItem(term, e)}
                        className="opacity-0 group-hover:opacity-100 text-white/40 hover:text-white transition-all"
                      >
                        <X size={14} />
                      </button>
                    </motion.div>
                  ))}
                </div>
              </motion.div>
            )}
          </motion.form>
          
          {/* 分类按钮区域 */}
          {!query && (
            <motion.div
              className="mb-6"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.6, duration: 0.4 }}
            >
              <div className="text-white/40 text-xs mb-2 flex items-center gap-1">
                <Tag size={12} />
                分类浏览
              </div>
              <div className="flex flex-wrap gap-2">
                {categoriesLoading ? (
                  <div className="flex items-center gap-2 text-white/40 text-sm">
                    <div className="w-4 h-4 border-2 border-[#00d4ff] border-t-transparent rounded-full animate-spin" />
                    加载分类...
                  </div>
                ) : (
                  categories.map((category, index) => (
                    <motion.button
                      key={category.category_code}
                      onClick={() => handleCategoryClick(category)}
                      className={`px-3 py-1.5 rounded-lg glass text-sm transition-all ${
                        selectedCategory?.category_code === category.category_code
                          ? 'text-white border-[#00d4ff]/50 bg-[#00d4ff]/10'
                          : 'text-white/60 hover:text-white hover:border-[#00d4ff]/30'
                      }`}
                      style={{
                        borderColor: selectedCategory?.category_code === category.category_code 
                          ? category.color_code 
                          : undefined
                      }}
                      initial={{ opacity: 0, scale: 0.8 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: 0.6 + index * 0.05, duration: 0.3 }}
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                    >
                      <span 
                        className="inline-block w-2 h-2 rounded-full mr-1.5"
                        style={{ backgroundColor: category.color_code }}
                      />
                      {category.category_name}
                    </motion.button>
                  ))
                )}
              </div>
            </motion.div>
          )}
          
          {/* 搜索结果 */}
          <motion.div 
            className="flex-1 overflow-hidden flex flex-col"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.6, duration: 0.4 }}
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-white/80 font-medium">
                {getPageTitle()}
              </h3>
              {newsList.length > 0 && (
                <span className="text-white/40 text-sm">
                  共 {newsList.length} 条
                </span>
              )}
            </div>
            
            <div className="flex-1 overflow-y-auto custom-scrollbar">
              {loading ? (
                <div className="flex items-center justify-center py-12">
                  <div className="w-8 h-8 border-2 border-[#00d4ff] border-t-transparent rounded-full animate-spin" />
                </div>
              ) : newsList.length > 0 ? (
                <div className="space-y-3 pr-2">
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
                <div className="text-center py-12 text-white/40">
                  <SearchIcon size={48} className="mx-auto mb-4 opacity-30" />
                  <p>未找到相关新闻</p>
                  <p className="text-sm mt-1">尝试其他关键词或分类</p>
                </div>
              )}
            </div>
          </motion.div>
        </div>
      </motion.div>
      
      {/* 右侧地球背景 */}
      <motion.div 
        className="absolute right-0 top-0 w-[60%] h-full z-[1]"
        initial={{ x: '5%', opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        transition={{ duration: 0.6, ease: 'easeOut' }}
      >
        <Earth3D
          mode="background"
          rotationSpeed={0.0002}
          enableControls={false}
          cameraPosition={[-3, 0, 16]}
        />
      </motion.div>
      
      {/* 返回按钮 */}
      <motion.button
        className="absolute top-6 right-6 z-20 glass p-3 rounded-full text-white/80 hover:text-white hover:bg-white/10 transition-all"
        onClick={handleBack}
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: 0.5, duration: 0.4 }}
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
      >
        <ArrowRight size={24} />
      </motion.button>
      
      {/* 点击外部关闭历史记录 */}
      {showHistory && (
        <div 
          className="fixed inset-0 z-20"
          onClick={() => setShowHistory(false)}
        />
      )}
    </div>
  );
}
